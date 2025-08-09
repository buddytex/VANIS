#!/usr/bin/env python3
import sys, time
import lgpio  # sudo apt install python3-lgpio

# ===== PIN MAP (BCM) — change if needed =====
IN1, IN2, ENA = 17, 27, 18   # Left
IN3, IN4, ENB = 22, 23, 19   # Right

PWM_FREQ = 1000  # 1 kHz is smooth for L298

def clamp_pct(p): 
    try: p = int(p)
    except: p = 0
    return max(0, min(100, p))

def main():
    # Open first gpiochip (usually 0 on Pi)
    h = lgpio.gpiochip_open(0)

    # Claim outputs
    for pin in (IN1, IN2, ENA, IN3, IN4, ENB):
        lgpio.gpio_claim_output(h, pin)

    def side_stop(side):
        if side == "l":
            lgpio.gpio_write(h, IN1, 0); lgpio.gpio_write(h, IN2, 0)
            lgpio.tx_pwm(h, ENA, 0, 0)
        else:
            lgpio.gpio_write(h, IN3, 0); lgpio.gpio_write(h, IN4, 0)
            lgpio.tx_pwm(h, ENB, 0, 0)

    def side_drive(side, direction, speed_pct):
        speed = clamp_pct(speed_pct)
        if side == "l":
            if direction == "f":
                lgpio.gpio_write(h, IN1, 1); lgpio.gpio_write(h, IN2, 0)
            elif direction == "b":
                lgpio.gpio_write(h, IN1, 0); lgpio.gpio_write(h, IN2, 1)
            else:
                lgpio.gpio_write(h, IN1, 0); lgpio.gpio_write(h, IN2, 0)
            lgpio.tx_pwm(h, ENA, PWM_FREQ, speed)
        else:
            if direction == "f":
                lgpio.gpio_write(h, IN3, 1); lgpio.gpio_write(h, IN4, 0)
            elif direction == "b":
                lgpio.gpio_write(h, IN3, 0); lgpio.gpio_write(h, IN4, 1)
            else:
                lgpio.gpio_write(h, IN3, 0); lgpio.gpio_write(h, IN4, 0)
            lgpio.tx_pwm(h, ENB, PWM_FREQ, speed)

    def both_stop():
        side_stop("l"); side_stop("r")

    def both_drive(direction, speed_pct):
        side_drive("l", direction, speed_pct)
        side_drive("r", direction, speed_pct)

    HELP = """
Commands:
  l f <spd>     LEFT  forward  at <spd>% (0-100)
  l b <spd>     LEFT  backward at <spd>%
  l s           LEFT  stop

  r f <spd>     RIGHT forward  at <spd>%
  r b <spd>     RIGHT backward at <spd>%
  r s           RIGHT stop

  both f <spd>  both forward  at <spd>%
  both b <spd>  both backward at <spd>%
  both s        stop both

  turn l <spd>  spin-in-place LEFT  (L back, R fwd) at <spd>%
  turn r <spd>  spin-in-place RIGHT (L fwd, R back) at <spd>%

  stop          stop both
  help          show this help
  quit/exit     exit
"""
    print("L298 CLI (lgpio) ready. Type 'help' for commands.")
    print("Examples:  l f 60  |  r b 40  |  both f 75  |  turn r 50")

    try:
        while True:
            try:
                line = input("> ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not line: 
                continue
            p = line.split()

            try:
                if p[0] in ("quit","exit"): break
                elif p[0] == "help": print(HELP)

                elif p[0] == "l":
                    if len(p) >= 3 and p[1] in ("f","b"):
                        side_drive("l", p[1], p[2])
                    elif len(p) >= 2 and p[1] == "s":
                        side_stop("l")
                    else:
                        print("Usage: l f|b <speed>  OR  l s")

                elif p[0] == "r":
                    if len(p) >= 3 and p[1] in ("f","b"):
                        side_drive("r", p[1], p[2])
                    elif len(p) >= 2 and p[1] == "s":
                        side_stop("r")
                    else:
                        print("Usage: r f|b <speed>  OR  r s")

                elif p[0] == "both":
                    if len(p) >= 3 and p[1] in ("f","b"):
                        both_drive(p[1], p[2])
                    elif len(p) >= 2 and p[1] == "s":
                        both_stop()
                    else:
                        print("Usage: both f|b <speed>  OR  both s")

                elif p[0] == "turn":
                    if len(p) >= 3 and p[1] == "l":
                        side_drive("l","b", p[2]); side_drive("r","f", p[2])
                    elif len(p) >= 3 and p[1] == "r":
                        side_drive("l","f", p[2]); side_drive("r","b", p[2])
                    else:
                        print("Usage: turn l|r <speed>")

                elif p[0] == "stop":
                    both_stop()

                else:
                    print("Unknown command. Type 'help'.")
            except Exception as e:
                print("Error:", e)

    finally:
        both_stop()
        lgpio.gpiochip_close(h)

if __name__ == "__main__":
    main()
