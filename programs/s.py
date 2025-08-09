import pigpio, time

PIN = 17          # BCM pin for servo signal (physical pin 11)
LOW, HIGH = 40, 80  # sweep limits in degrees
STEP = 1
DELAY = 0.02      # seconds between steps

# Pulse width calibration (tweak if needed)
MIN_PW = 500      # µs at 0°
MAX_PW = 2500     # µs at 180°

def angle_to_us(angle):
    angle = max(0, min(180, angle))
    return int(MIN_PW + (angle / 180.0) * (MAX_PW - MIN_PW))

pi = pigpio.pi()
if not pi.connected:
    raise SystemExit("pigpio daemon not running. Start it with: sudo pigpiod")

try:
    # go to start
    pi.set_servo_pulsewidth(PIN, angle_to_us(LOW))
    time.sleep(0.3)

    current = LOW
    up = True
    while True:
        current += STEP if up else -STEP
        if current >= HIGH:
            current = HIGH
            up = False
        elif current <= LOW:
            current = LOW
            up = True

        pi.set_servo_pulsewidth(PIN, angle_to_us(current))
        time.sleep(DELAY)

except KeyboardInterrupt:
    pass
finally:
    pi.set_servo_pulsewidth(PIN, 0)  # turn off pulses
    pi.stop()
