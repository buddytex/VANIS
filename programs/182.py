# sweep_hide_back_full.py
import RPi.GPIO as GPIO
import time

# ---- PINS (BCM) ----
SERVO = 17
TRIG  = 20
ECHO  = 24          # MUST be level-shifted to 3.3V
LEFT_IN1, LEFT_IN2  = 5, 6
RIGHT_IN3, RIGHT_IN4 = 13, 19

# ---- SWEEP ----
SWEEP_MIN = 40          # degrees
SWEEP_MAX = 80
STEP_DEG  = 2
STEP_DELAY = 0.03       # medium speed
SETTLE_S   = 0.10       # servo settle after big move

# ---- LOGIC / ULTRASONIC ----
NEAR_CM       = 35      # trigger distance
NEAR_HITS     = 2       # consecutive near reads to trigger
TIMEOUT_S     = 0.025   # ~4 m
FIXED_HIDE_S  = 5.0     # stay in HIDING exactly 5s
BACK_UP_S     = 1.0     # reverse duration at the moment of hide

# ===== Helpers =====
def angle_to_duty(deg: float) -> float:
    # 50 Hz PWM: 0.5–2.5 ms -> 2.5–12.5% duty
    return 2.5 + (deg/180.0)*10.0

def motors_stop():
    GPIO.output(LEFT_IN1, 0); GPIO.output(LEFT_IN2, 0)
    GPIO.output(RIGHT_IN3,0); GPIO.output(RIGHT_IN4,0)

def both_backward(t=1.0):
    GPIO.output(LEFT_IN1, 0); GPIO.output(LEFT_IN2, 1)
    GPIO.output(RIGHT_IN3,0); GPIO.output(RIGHT_IN4,1)
    time.sleep(t)
    motors_stop()

def distance_cm():
    # 10 µs trigger
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
    servo.start(angle_to_duty(60))  # start mid-ish
    time.sleep(0.3)

    direction = +1
    angle = SWEEP_MIN
    state = "SWEEP"
    near_ct = 0
    hide_start = None

    print("Sweep 40↔80 on GPIO17; on detect: BACKWARD + hide 5s. Ctrl+C to quit.")
    try:
        while True:
            d = distance_cm()

            if state == "SWEEP":
                if d is not None and d <= NEAR_CM:
                    near_ct += 1
                else:
                    near_ct = 0

                if near_ct >= NEAR_HITS:
                    print(f"[DETECTED] {d:.1f} cm -> BACKWARD {BACK_UP_S}s + HIDE {FIXED_HIDE_S}s")
                    # Face “away” and back up, then enter HIDING for fixed time
                    servo.ChangeDutyCycle(angle_to_duty(180))
                    time.sleep(SETTLE_S)
                    both_backward(BACK_UP_S)
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
                    print("[DONE HIDING] Return to sweep")
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

