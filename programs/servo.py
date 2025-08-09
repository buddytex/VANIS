import RPi.GPIO as GPIO
import time

# --- CONFIG ---
SERVO_PIN = 17      # BCM numbering
FREQ_HZ   = 50      # standard servo freq
MIN_DUTY  = 2.5     # ~0°  (tweak to 3.0–3.5 if needed)
MAX_DUTY  = 12.5    # ~180° (tweak to 11.0–12.0 if needed)
LOW_ANG   = 40
HIGH_ANG  = 80
STEP      = 2       # angle step per update
DELAY_S   = 0.02    # time between steps

GPIO.setmode(GPIO.BCM)
GPIO.setup(SERVO_PIN, GPIO.OUT)
pwm = GPIO.PWM(SERVO_PIN, FREQ_HZ)
pwm.start(0)

def angle_to_duty(angle):
    # Clamp angle and map linearly to duty cycle
    angle = max(0, min(180, angle))
    return MIN_DUTY + (angle / 180.0) * (MAX_DUTY - MIN_DUTY)

def go_to(angle):
    duty = angle_to_duty(angle)
    pwm.ChangeDutyCycle(duty)

try:
    # Move to start
    go_to(LOW_ANG)
    time.sleep(0.3)

    going_up = True
    current = LOW_ANG

    while True:
        # Sweep between 40 and 80
        if going_up:
            current += STEP
            if current >= HIGH_ANG:
                current = HIGH_ANG
                going_up = False
        else:
            current -= STEP
            if current <= LOW_ANG:
                current = LOW_ANG
                going_up = True

        go_to(current)
        time.sleep(DELAY_S)

except KeyboardInterrupt:
    pass
finally:
    pwm.stop()
    GPIO.cleanup()


