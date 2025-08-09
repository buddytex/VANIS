# sweep_hide_tank_full.py
import RPi.GPIO as GPIO
import time

# ---- PINS (BCM) ----
SERVO = 17
TRIG  = 20
ECHO  = 24          # level-shift to 3.3V
LEFT_IN1, LEFT_IN2  = 5, 6
RIGHT_IN3, RIGHT_IN4 = 13, 19

# ---- SWEEP ----
SWEEP_MIN = 40
SWEEP_MAX = 80
STEP_DEG  = 2
STEP_DELAY = 0.03
SETTLE_S   = 0.10

# ---- LOGIC / ULTRASONIC ----
NEAR_CM      = 35
NEAR_HITS    = 2
TIMEOUT_S    = 0.025
FIXED_HIDE_S = 5.0     # stay hiding exactly 5s

# ---- TANK TURN ----
TURN_180_S = 1.0       # tune: ~0.8–1.5s for ~180° spin

# ===== Helpers =====
def angle_to_duty(deg: float) -> float:
    return 2.5 + (deg/180.0)*10.0   # 50Hz PWM, 0.5–2.5ms

def motors_stop():
    GPIO.output(LEFT_IN1, 0); GPIO.output(LEFT_IN2, 0)
    GPIO.output(RIGHT_IN3,0); GPIO.output(RIGHT_IN4,0)

def left_forward(on=True):
    GPIO.output(LEFT_IN1, 1 if on else 0)
    GPIO.output(LEFT_IN2, 0)

def right_backward(on=True):
    GPIO.output(RIGHT_IN3, 0)
    GPIO.output(RIGHT_IN4, 1 if on else 0)

def tank_turn_ccw(duration_s: float):
    # LEFT forward + RIGHT backward -> spin in place (CCW)
    left

