# hide_free.py  (Option 1: ENA/ENB tied to 5V)
import RPi.GPIO as GPIO
import time

# ==== PIN SETUP (BCM numbers) ====
SERVO = 18   # radar servo
LEFT_IN1  = 5
LEFT_IN2  = 6
RIGHT_IN3 = 13
RIGHT_IN4 = 19

# ==== SERVO HELPERS ====
def angle_to_duty(deg: float) -> float:
    """Map 0-180° to 2.5-12.5% duty cycle for SG90-type servo"""
    return 2.5 + (deg / 180.0) * 10.0

# ==== MOTOR HELPERS ====
def forward(t=0):
    GPIO.output(LEFT_IN1, 1)
    GPIO.output(LEFT_IN2, 0)
    GPIO.output(RIGHT_IN3, 1)
    GPIO.output(RIGHT_IN4, 0)
    if t > 0:
        time.sleep(t)
        stop()

def backward(t=0):
    GPIO.output(LEFT_IN1, 0)
    GPIO.output(LEFT_IN2, 1)
    GPIO.output(RIGHT_IN3, 0)
    GPIO.output(RIGHT_IN4, 1)
    if t > 0:
        time.sleep(t)
        stop()

def stop():
    GPIO.output(LEFT_IN1, 0)
    GPIO.output(LEFT_IN2, 0)
    GPIO.output(RIGHT_IN3, 0)
    GPIO.output(RIGHT_IN4, 0)

# ==== SETUP ====
GPIO.setmode(GPIO.BCM)

for pin in (LEFT_IN1, LEFT_IN2, RIGHT_IN3, RIGHT_IN4):
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, 0)

GPIO.setup(SERVO, GPIO.OUT)
servo_pwm = GPIO.PWM(SERVO, 50)  # 50 Hz servo control
servo_pwm.start(angle_to_duty(90))  # center forward
time.sleep(0.5)

# ==== MAIN LOOP ====
try:
    print("Type 'hide' or 'free' and press Enter. Ctrl+C to quit.")
    while True:
        cmd = input("> ").strip().lower()
        if cmd == "hide":
            print("Hiding...")
            servo_pwm.ChangeDutyCycle(angle_to_duty(180))  # turn to 180°
            time.sleep(0.5)
            backward(0.5)  # move away
            stop()
        elif cmd == "free":
            print("Returning...")
            servo_pwm.ChangeDutyCycle(angle_to_duty(90))   # back to center
            time.sleep(0.5)
            stop()
        else:
            print("Unknown command. Use 'hide' or 'free'.")
except KeyboardInterrupt:
    pass
finally:
    stop()
    servo_pwm.stop()
    GPIO.cleanup()

