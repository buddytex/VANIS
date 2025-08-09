# sweep_hide_tank_full.py
# Pi 5 friendly (uses python3-rpi-lgpio as RPi.GPIO)
# Behavior:
# - Sweep servo (GPIO17) 40↔80 degrees.
# - If ultrasonic detects object (<= NEAR_CM for NEAR_HITS reads):
#     * Turn CCW in place (left fwd + right back) for TURN_180_S.
#     * Stay "hiding" for FIXED_HIDE_S.
#     * Turn CW in place (left back + right fwd) for TURN_180_S to face original direction.
# - Resume sweep.

import RPi.GPIO as GPIO
import time

# ---- PINS (BCM) ----
SERVO = 17
TRIG  = 20
ECHO  = 24          # Echo MUST be level-shifted to 3.3V
LEFT_IN1, LEFT_IN2  = 5, 6
RIGHT_IN3, RIGHT_IN4 = 13, 19

# ---- SWEEP ----
SWEEP_MIN = 40
SWEEP_MAX = 80
STEP_DEG  = 2
STEP_DELAY = 0.03
SETTLE_S   = 0.10

# ---- LOGIC / ULTRASONIC ----
NEAR_CM      = 35
NEAR_HITS    = 2
TIMEOUT_S    = 0.025
FIXED_HIDE_S = 5.0     # stay hiding exactly 5s

# ---- TANK TURN ----
TURN_180_S = 0.7   # ~180° spin time (tune 0.6–1.0 as needed)

# ===== Helpers =====
def angle_to_duty(deg: float) -> float:
    # 50Hz PWM, 0.5–2.5ms pulse => ~2.5–12.5% duty
    return 2.5 + (deg/180.0)*10.0

def motors_stop():
    GPIO.output(LEFT_IN1, 0); GPIO.output(LEFT_IN2, 0)
    GPIO.output(RIGHT_IN3,0); GPIO.output(RIGHT_IN4,0)

def left_forward(on=True):
    GPIO.output(LEFT_IN1, 1 if on else 0)
    GPIO.output(LEFT_IN2, 0)

def right_backward(on=True):
    GPIO.output(RIGHT_IN3, 0)
    GPIO.output(RIGHT_IN4, 1 if on else 0)

def left_backward(on=True):
    GPIO.output(LEFT_IN1, 0)
    GPIO.output(LEFT_IN2, 1 if on else 0)

def right_forward(on=True):
    GPIO.output(RIGHT_IN3, 1 if on else 0)
    GPIO.output(RIGHT_IN4, 0)

def tank_turn_ccw(duration_s: float):
    # LEFT forward + RIGHT backward -> spin CCW
    left_forward(True)
    right_backward(True)
    time.sleep(duration_s)
    motors_stop()

def tank_turn_cw(duration_s: float):
    # LEFT backward + RIGHT forward -> spin CW
    left_backward(True)
    right_forward(True)
    time.sleep(duration_s)
    motors_stop()

def distance_cm():
    # 10us trigger
    GPIO.output(TRIG, GPIO.LOW); time.sleep(0.00001)
    GPIO.output(TRIG, GPIO.HIGH); time.sleep(0.00001)
    GPIO.output(TRIG, GPIO.LOW)

    t0 = time.time()
    while GPIO.input(ECHO) == 0:
        if time.time() - t0 > TIMEOUT_S:
            return None
    start = time.time()

    while GPIO.input(ECHO) == 1:
        if time.time() - start > TIMEOUT_S:
            return None
    end = time.time()

    dur = end - start
    return (dur * 34300.0) / 2.0

# ===== Main =====
def main():
    GPIO.setmode(GPIO.BCM)

    # Motors
    for p in (LEFT_IN1, LEFT_IN2, RIGHT_IN3, RIGHT_IN4):
        GPIO.setup(p, GPIO.OUT); GPIO.output(p, 0)

    # Ultrasonic
    GPIO.setup(TRIG, GPIO.OUT); GPIO.output(TRIG, GPIO.LOW)
    GPIO.setup(ECHO, GPIO.IN)

    # Servo
    GPIO.setup(SERVO, GPIO.OUT)
    servo = GPIO.PWM(SERVO, 50)
    servo.start(angle_to_duty(60))  # mid-ish
    time.sleep(0.3)

    direction = +1
    angle = SWEEP_MIN
    state = "SWEEP"
    near_ct = 0
    hide_start = None

    print("Sweep 40↔80 on GPIO17; detect -> CCW turn, hide 5s, CW turn back, resume sweep.")
    try:
        while True:
            d = distance_cm()

            if state == "SWEEP":
                if d is not None and d <= NEAR_CM:
                    near_ct += 1
                else:
                    near_ct = 0

                if near_ct >= NEAR_HITS:
                    print(f"[DETECTED] {d:.1f} cm -> CCW turn + HIDE ({FIXED_HIDE_S}s)")
                    # Face "away" with servo (optional visual), then tank turn CCW
                    servo.ChangeDutyCycle(angle_to_duty(180))
                    time.sleep(SETTLE_S)
                    tank_turn_ccw(TURN_180_S)
                    state = "HIDING"
                    hide_start = time.time()
                    continue

                # normal sweep
                servo.ChangeDutyCycle(angle_to_duty(angle))
                time.sleep(STEP_DELAY)
                angle += direction * STEP_DEG
                if angle >= SWEEP_MAX:
                    angle = SWEEP_MAX; direction = -1
                elif angle <= SWEEP_MIN:
                    angle = SWEEP_MIN; direction = +1

            else:  # HIDING
                if time.time() - hide_start >= FIXED_HIDE_S:
                    print("[DONE HIDING] Turning back CW, then resume sweep")
                    tank_turn_cw(TURN_180_S)              # reverse the first spin
                    servo.ChangeDutyCycle(angle_to_duty(60))
                    time.sleep(SETTLE_S)
                    state = "SWEEP"
                    near_ct = 0
                    angle = SWEEP_MIN
                    direction = +1
                else:
                    time.sleep(0.05)

    except KeyboardInterrupt:
        pass
    finally:
        motors_stop()
        servo.stop()
        GPIO.cleanup()

if __name__ == "__main__":
    main()

