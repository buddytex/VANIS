# distance_alarm.py
# Pi 5 + HC-SR04 + Active buzzer
# TRIG=GPIO20, ECHO=GPIO24 (via divider), BUZZER=GPIO21

from gpiozero import DistanceSensor, LED
from time import sleep, time

TRIG_PIN = 20
ECHO_PIN = 24
BUZZER_PIN = 21

# max_distance in meters (HC-SR04 ~4m ideal; keep 2.0 for stability)
sensor = DistanceSensor(echo=ECHO_PIN, trigger=TRIG_PIN, max_distance=2.0)
buzzer = LED(BUZZER_PIN)  # on/off for active buzzer

def interval_from_distance_m(d_m):
    """
    Map distance to beep interval (seconds).
    Silent ≥ 0.8 m.
    At 80 cm -> ~0.6 s, at 5 cm -> ~0.05 s.
    """
    if d_m is None or d_m >= 0.8:
        return None
    d_cm = max(5.0, d_m * 100.0)
    return 0.05 + (0.6 - 0.05) * ((d_cm - 5.0) / (80.0 - 5.0))

try:
    next_beep = 0.0
    while True:
        # gpiozero returns 0.0..1.0 of max_distance
        d_m = sensor.distance * sensor.max_distance
        print(f"Distance: {d_m*100:6.1f} cm", end="\r")

        interval = interval_from_distance_m(d_m)
        if interval is None:
            buzzer.off()
            sleep(0.05)
            continue

        now = time()
        if now >= next_beep:
            buzzer.on()
            sleep(0.03)  # short chirp
            buzzer.off()
            next_beep = now + interval
        else:
            sleep(0.01)

except KeyboardInterrupt:
    pass
finally:
    buzzer.off()
    print("\nExiting cleanly.")
