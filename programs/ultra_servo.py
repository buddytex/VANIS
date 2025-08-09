# radar_watch_18_20_24.py
# Sweep servo + ultrasonic. If an object is near at some angle,
# hold that angle until it's clear, then resume sweeping.

import pigpio, time

# --- PIN MAP (BCM) ---
SERVO = 18       # GPIO 18 (phys 12) - PWM capable
TRIG  = 20       # GPIO 20 (phys 38)
ECHO  = 24       # GPIO 24 (phys 18)  -> LEVEL-SHIFT to 3.3V!

# --- RADAR / SCAN SETTINGS ---
MIN_ANGLE   = 20      # deg
MAX_ANGLE   = 160     # deg
STEP_DEG    = 5       # deg per step
SETTLE_S    = 0.10    # wait after moving servo before measuring

# --- DISTANCE / NEAR LOGIC ---
TIMEOUT_S   = 0.025   # ~4m timeout
NEAR_CM     = 35      # threshold to start tracking
CLEAR_CM    = 45      # threshold to stop tracking (hysteresis)
NEAR_COUNT  = 2       # consecutive near hits to lock
CLEAR_COUNT = 4       # consecutive clear hits to release

def angle_to_us(deg: float) -> int:
    # map 0..180 deg -> 500..2500 µs
    return int(500 + (deg/180.0)*2000)

class Radar:
    def __init__(self):
        self.pi = pigpio.pi()
        if not self.pi.connected:
            raise RuntimeError("pigpio daemon not running (sudo systemctl start pigpiod)")

        self.pi.set_mode(SERVO, pigpio.OUTPUT)
        self.pi.set_servo_pulsewidth(SERVO, 0)

        self.pi.set_mode(TRIG, pigpio.OUTPUT)
        self.pi.set_mode(ECHO, pigpio.INPUT)
        self.pi.write(TRIG, 0)
        time.sleep(0.05)

    def set_servo_deg(self, deg: int):
        if   deg < 0:   deg = 0
        elif deg > 180: deg = 180
        self.pi.set_servo_pulsewidth(SERVO, angle_to_us(deg))
        time.sleep(SETTLE_S)

    def distance_cm(self):
        # trigger 10us pulse
        self.pi.gpio_trigger(TRIG, 10, 1)

        t0 = time.time()
        # wait rise
        while self.pi.read(ECHO) == 0:
            if time.time() - t0 > TIMEOUT_S:
                return None

        start = time.time()
        # wait fall
        while self.pi.read(ECHO) == 1:
            if time.time() - start > TIMEOUT_S:
                return None
        end = time.time()

        dur = end - start
        return (dur * 34300.0) / 2.0  # cm

    def cleanup(self):
        self.pi.set_servo_pulsewidth(SERVO, 0)
        self.pi.stop()

def bar(cm, max_cm=150):
    if cm is None: return ""
    n = int(max(0, min(40, 40 * (1 - cm/max_cm))))
    return "█" * n

def main():
    r = Radar()
    try:
        angle = MIN_ANGLE
        direction = +1
        tracking = False
        track_angle = None
        near_hits = 0
        clear_hits = 0

        print("Radar running. Ctrl+C to stop.")
        while True:
            if not tracking:
                # sweeping
                r.set_servo_deg(angle)
                dist = r.distance_cm()
                print(f"[SWEEP] angle={angle:3d}°  dist={dist if dist else -1:6.1f} cm  {bar(dist)}")

                near_hits = near_hits + 1 if (dist is not None and dist <= NEAR_CM) else 0
                if near_hits >= NEAR_COUNT:
                    tracking = True
                    track_angle = angle
                    clear_hits = 0
                    print(f"--> Near object @ ~{track_angle}°. Holding...")

                angle += direction * STEP_DEG
                if angle >= MAX_ANGLE:
                    angle, direction = MAX_ANGLE, -1
                elif angle <= MIN_ANGLE:
                    angle, direction = MIN_ANGLE, +1

            else:
                # tracking (stay pointed)
                r.set_servo_deg(track_angle)
                dist = r.distance_cm()
                print(f"[TRACK] angle={track_angle:3d}°  dist={dist if dist else -1:6.1f} cm  {bar(dist)}")

                clear_hits = clear_hits + 1 if (dist is not None and dist >= CLEAR_CM) else 0
                if clear_hits >= CLEAR_COUNT:
                    print(f"<-- Cleared @ {track_angle}°. Resuming sweep.")
                    tracking = False
                    near_hits = 0
                    # resume outward from where we left
                    midpoint = (MIN_ANGLE + MAX_ANGLE)//2
                    if track_angle <= midpoint:
                        angle, direction = track_angle + STEP_DEG, +1
                    else:
                        angle, direction = track_angle - STEP_DEG, -1
                    track_angle = None

            time.sleep(0.02)
    except KeyboardInterrupt:
        print("\nStopping radar.")
    finally:
        r.cleanup()

if __name__ == "__main__":
    main()

