# ultra_simple_hide.py
import RPi.GPIO as GPIO
import time

# --- PIN MAP (BCM) ---
SERVO = 18
TRIG  = 20
ECHO  = 24  # must be level-shifted to 3.3V

LEFT_IN1, LEFT_IN2  = 5, 6
RIGHT_IN3, RIGHT_IN4 = 13, 19

# --- SETTINGS ---
NEAR_CM     = 35
HIDE_BACK_S = 0.5
TIMEOUT_S   = 0.025
SETTLE_S    = 0.10

# --- Helpers ---
def angle_to_duty(deg: float) -> float:
    return 2.5 + (deg / 180.0) * 10.0

def motors_stop():
    GPIO.output(LEFT_IN1, 0)
    GPIO.output(LEFT_IN2, 0)
    GPIO.output(RIGHT_IN3, 0)
    GPIO.output(RIGHT_IN4, 0)

def motors_backward(t=0):
    GPIO.output(LEFT_IN1, 0)
    GPIO.output(LEFT_IN2, 1)
    GPIO.output(RIGHT_IN3, 0)
    GPIO.output(RIGHT_IN4, 1)
    if t > 0:
        time.sleep(t)
        motors_stop()

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

# --- Main ---
def main():
    GPIO.setmode(GPIO.BCM)

    for p in (LEFT_IN1, LEFT_IN2, RIGHT_IN3, RIGHT_IN4):
        GPIO.setup(p, GPIO.OUT)
        GPIO.output(p, 0)

    GPIO.setup(TRIG, GPIO.OUT)
    GPIO.output(TRIG, GPIO.LOW)
    GPIO.setup(ECHO, GPIO.IN)

    GPIO.setup(SERVO, GPIO.OUT)
    servo = GPIO.PWM(SERVO, 50)
    servo.start(angle_to_duty(90))
    time.sleep(0.3)

    try:
        while True:
            d = distance_cm()
            if d is not None and d <= NEAR_CM:
                print(f"Object detected at {d:.1f} cm — HIDE")
                servo.ChangeDutyCycle(angle_to_duty(180))
                time.sleep(SETTLE_S)
                motors_backward(HIDE_BACK_S)
            else:
                print("No object")
                servo.ChangeDutyCycle(angle_to_duty(90))
                motors_stop()

            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        motors_stop()
        servo.stop()
        GPIO.cleanup()

if __name__ == "__main__":
    main()

