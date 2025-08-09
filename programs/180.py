# sweep_hide_fixed5_tank.py
import RPi.GPIO as GPIO
import time

# ---- PINS (BCM) ----
SERVO = 17
TRIG  = 20
ECHO  = 24          # level-shift to 3.3V
LEFT_IN1, LEFT_IN2  = 5, 6
RIGHT_IN3, RIGHT_IN4 = 13, 19

# ---- SWEEP ----
SWEEP_MIN = 40
SWEEP_MAX = 80
STEP_DEG  = 2
STEP_DELAY = 0.03
SETTLE_S   = 0.10

# ---- ULTRASONIC / LOGIC ----
NEAR_CM      = 35
NEAR_HITS    = 2
TIMEOUT_S    = 0.025
HIDE_BACK_S  = 0.0   # not used now, but kept if you want a little reverse
FIXED_HIDE_S = 5.0   # stay in HIDING exactly 5s

# ---- TANK TURN (approx 180°) ----
TURN_180_S = 1.0     # <-- tune this for your robot (try 0.8–1.5s)

def angle_to_duty(deg: float) -> float:
    return 2.5 + (deg/180.0)*10.0

def motors_stop():
    GPIO.output(LEFT_IN1, 0); GPIO.output(LEFT_IN2, 0)
    GPIO.output(RIGHT_IN3,0); GPIO.output(RIGHT_IN4,0)

def left_forward(on=True):
    GPIO.output(LEFT_IN1, 1 if on else 0)
    GPIO.output(LEFT_IN2, 0 if on else 0)

def left_backward(on=True):
    GPIO.output(LEFT_IN1, 0 if on else 0)
    GPIO.output(LEFT_IN2, 1 if on else 0)

def right_forward(on=True):
    GPIO.output(RIGHT_IN3, 1 if on else 0)
    GPIO.output(RIGHT_IN4, 0 if on else 0)

def right_backward(on=True):
    GPIO.output(RIGHT_IN3, 0 if on else 0)
    GPIO.output(RIGHT_IN4, 1 if on else 0)

def motors_backward(t=0):
    left_backward(True); right_backward(True)
    if t>0:
        time.sleep(t); motors_stop()

def tank_turn_180_ccw():
    # Left forward, Right backward -> spin in place (CCW viewed from above)
    left_forward(True); right_backward(True)
    time.sleep(TURN_180_S)
    motors_stop()

def distance_cm():
    GPIO.output(TRIG, GPIO.LOW); time.sleep(0.00001)
    GPIO.output(TRIG, GPIO.HIGH); time.sleep(0.00001)
    GPIO.output(TRIG, GPIO.LOW)

    t0 = time.time()
    while GPIO.input(ECHO) == 0:
        if time.time() - t0 > TIMEOUT_S: return None
    start = time.time()
    while GPIO.input(ECHO) == 1:
        if time.time() - start > TIMEOUT_S: return None
    end = time.time()

    dur = end - start
    return (dur * 34300.0) / 2.0

def main():
    GPIO.setmode(GPIO.BCM)

    for p in (LEFT_IN1, LEFT_IN2, RIGHT_IN3, RIGHT_IN4):
        GPIO.setup(p, GPIO.OUT); GPIO.output(p, 0)

    GPIO.setup(TRIG, GPIO.OUT); GPIO.output(TRIG, GPIO.LOW)
    GPIO.setup(ECHO, GPIO.IN)

    GPIO.setup(SERVO, GPIO.OUT)
    servo = GPIO.PWM(SERVO, 50)
    servo.start(angle_to_duty(60))
    time.sleep(0.3)

    direction = +1
    angle = SWEEP_MIN
    state = "SWEEP"
    near_ct = 0
    hide_start = None

    print("Sweep 40↔80 on GPIO17; on detect: tank-turn 180°, hide 5s. Ctrl+C to quit.")
    try:
        while True:
            d = distance_cm()

            if state == "SWEEP":
                if d is not None and d <= NEAR_CM:
                    near_ct += 1
                else:
                    near_ct = 0

                if near_ct >= NEAR_HITS:
                    print(f"[DETECTED] {d:.1f} cm -> TANK TURN + HIDE ({FIXED_HIDE_S}s)")
                    # Face away and tank turn
                    servo.ChangeDutyCycle(angle_to_duty(180))
                    time.sleep(SETTLE_S)

                    # Optional tiny reverse before spin:
                    if HIDE_BACK_S > 0: motors_backward(HIDE_BACK_S)

                    tank_turn_180_ccw()   # spin in place
                    motors_stop()

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
                    print("[DONE HIDING] Returning to sweep")
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

