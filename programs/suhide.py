# sweep_hide.py
import RPi.GPIO as GPIO
import time

# ---- PINS (BCM) ----
SERVO = 17          # <-- sweep servo here
TRIG  = 20
ECHO  = 24          # MUST be level-shifted to 3.3V
LEFT_IN1, LEFT_IN2  = 5, 6
RIGHT_IN3, RIGHT_IN4 = 13, 19

# ---- SWEEP ----
SWEEP_MIN = 40      # degrees
SWEEP_MAX = 80
STEP_DEG  = 2
STEP_DELAY = 0.03   # "medium" speed
SETTLE_S   = 0.10   # settle after big moves (like hide/free)

# ---- ULTRASONIC / LOGIC ----
NEAR_CM     = 35
CLEAR_CM    = 45
NEAR_HITS   = 2     # consecutive near readings to trigger hide
CLEAR_HITS  = 3     # consecutive clear readings to resume
TIMEOUT_S   = 0.025
HIDE_BACK_S = 0.5   # reverse time during hide

def angle_to_duty(deg: float) -> float:
    # 50 Hz -> 20 ms period; 0.5–2.5 ms pulse => 2.5–12.5% duty
    return 2.5 + (deg/180.0)*10.0

def motors_stop():
    GPIO.output(LEFT_IN1, 0); GPIO.output(LEFT_IN2, 0)
    GPIO.output(RIGHT_IN3,0); GPIO.output(RIGHT_IN4,0)

def motors_backward(t=0):
    GPIO.output(LEFT_IN1, 0); GPIO.output(LEFT_IN2, 1)
    GPIO.output(RIGHT_IN3,0); GPIO.output(RIGHT_IN4,1)
    if t>0:
        time.sleep(t); motors_stop()

def distance_cm():
    GPIO.output(TRIG, GPIO.LOW)
    time.sleep(0.00001)
    GPIO.output(TRIG, GPIO.HIGH)
    time.sleep(0.00001)
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

def main():
    GPIO.setmode(GPIO.BCM)

    # motors
    for p in (LEFT_IN1, LEFT_IN2, RIGHT_IN3, RIGHT_IN4):
        GPIO.setup(p, GPIO.OUT); GPIO.output(p, 0)

    # ultrasonic
    GPIO.setup(TRIG, GPIO.OUT); GPIO.output(TRIG, GPIO.LOW)
    GPIO.setup(ECHO, GPIO.IN)

    # servo
    GPIO.setup(SERVO, GPIO.OUT)
    servo = GPIO.PWM(SERVO, 50)
    servo.start(angle_to_duty(60))   # start mid-sweep
    time.sleep(0.3)

    direction = +1
    angle = SWEEP_MIN
    state = "SWEEP"  # or "HIDING"
    near_ct = 0
    clear_ct = 0

    print("Sweep 40↔80 on GPIO17; hide on detection. Ctrl+C to quit.")
    try:
        while True:
            d = distance_cm()

            if state == "SWEEP":
                # check object
                if d is not None and d <= NEAR_CM:
                    near_ct += 1
                else:
                    near_ct = 0

                if near_ct >= NEAR_HITS:
                    print(f"[DETECTED] {d:.1f} cm -> HIDE")
                    # stop sweep & hide
                    servo.ChangeDutyCycle(angle_to_duty(180))
                    time.sleep(SETTLE_S)
                    motors_backward(HIDE_BACK_S)
                    motors_stop()
                    state = "HIDING"
                    clear_ct = 0
                    continue  # skip stepping this loop

                # sweep step
                servo.ChangeDutyCycle(angle_to_duty(angle))
                time.sleep(STEP_DELAY)
                angle += direction * STEP_DEG
                if angle >= SWEEP_MAX:
                    angle = SWEEP_MAX; direction = -1
                elif angle <= SWEEP_MIN:
                    angle = SWEEP_MIN; direction = +1

            else:  # HIDING
                # Hold at 180°, wait till clear to resume
                if d is not None and d >= CLEAR_CM:
                    clear_ct += 1
                else:
                    clear_ct = 0

                if clear_ct >= CLEAR_HITS:
                    print(f"[CLEAR] {d:.1f} cm -> FREE (resume sweep)")
                    servo.ChangeDutyCycle(angle_to_duty(60))  # face forward-ish
                    time.sleep(SETTLE_S)
                    state = "SWEEP"
                    near_ct = 0
                    # restart sweep heading outward
                    angle = SWEEP_MIN; direction = +1

                time.sleep(0.05)

    except KeyboardInterrupt:
        pass
    finally:
        motors_stop()
        servo.stop()
        GPIO.cleanup()

if __name__ == "__main__":
    main()

