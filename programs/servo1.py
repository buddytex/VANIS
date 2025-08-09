from gpiozero import AngularServo
from time import sleep

PIN = 17  # BCM 17 (physical pin 11)

# Calibrate pulse widths for your servo (tweak if motion is off)
MIN_PW = 0.0005  # 0.5 ms
MAX_PW = 0.0025  # 2.5 ms

servo = AngularServo(
    PIN,
    min_angle=0, max_angle=180,
    min_pulse_width=MIN_PW,
    max_pulse_width=MAX_PW
)

LOW, HIGH = 40, 80
STEP = 1
DELAY = 0.02

def go(angle):
    # Clamp and move
    angle = max(0, min(180, angle))
    servo.angle = angle

try:
    # move to start
    go(LOW); sleep(0.3)

    current = LOW
    going_up = True

    while True:
        if going_up:
            current += STEP
            if current >= HIGH:
                current = HIGH
                going_up = False
        else:
            current -= STEP
            if current <= LOW:
                current = LOW
                going_up = True

        go(current)
        sleep(DELAY)

except KeyboardInterrupt:
    pass
