import RPi.GPIO as GPIO
import time

# GPIO Pin Setup (BCM)
IN1, IN2 = 17, 27  # Left motor
IN3, IN4 = 22, 23  # Right motor
ENA, ENB = 18, 19  # PWM pins

GPIO.setmode(GPIO.BCM)
for pin in [IN1, IN2, IN3, IN4, ENA, ENB]:
    GPIO.setup(pin, GPIO.OUT)

# Setup PWM
pwm_a = GPIO.PWM(ENA, 100)  # 100 Hz
pwm_b = GPIO.PWM(ENB, 100)
pwm_a.start(0)
pwm_b.start(0)

def set_speed(speed):
    pwm_a.ChangeDutyCycle(speed)
    pwm_b.ChangeDutyCycle(speed)

def forward(speed=80):
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.HIGH)
    GPIO.output(IN4, GPIO.LOW)
    set_speed(speed)

def backward(speed=80):
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.HIGH)
    set_speed(speed)

def left(speed=80):
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)
    GPIO.output(IN3, GPIO.HIGH)
    GPIO.output(IN4, GPIO.LOW)
    set_speed(speed)

def right(speed=80):
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.HIGH)
    set_speed(speed)

def stop():
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.LOW)
    set_speed(0)

try:
    while True:
        forward()
        time.sleep(2)
        backward()
        time.sleep(2)
        left()
        time.sleep(2)
        right()
        time.sleep(2)
        stop()
        time.sleep(2)
except KeyboardInterrupt:
    pass
finally:
    pwm_a.stop()
    pwm_b.stop()
    GPIO.cleanup()
