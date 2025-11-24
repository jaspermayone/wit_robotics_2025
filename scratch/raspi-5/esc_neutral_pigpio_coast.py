# esc_neutral_pigpio_coast.py
# Requires: sudo apt install pigpio; sudo pigpiod
import pigpio
from time import sleep

PIN = 14
pi = pigpio.pi()
if not pi.connected:
    raise RuntimeError("pigpio daemon not running")

# Tune around lowest-current neutral
NEUTRAL_US   = 1510    # try 1490–1520; pick lowest-current value
DEADBAND_US  = (NEUTRAL_US - 5, NEUTRAL_US + 5)

def set_us(pw):
    pi.set_servo_pulsewidth(PIN, int(pw))

try:
    print("Arming at neutral...")
    set_us(NEUTRAL_US)
    sleep(2.0)

    while True:
        print("Forward small...")
        set_us(NEUTRAL_US + 120)
        sleep(0.5)

        print("Idle: neutral deadband (minimal current)...")
        set_us(sum(DEADBAND_US)//2)
        sleep(3.0)

        # Optional: coast by releasing signal if ESC allows
        # print("Idle: release signal to coast")
        # pi.set_servo_pulsewidth(PIN, 0)
        # sleep(2.0)
        # set_us(NEUTRAL_US)
        # sleep(0.8)

except KeyboardInterrupt:
    print("Neutral stop...")
    set_us(NEUTRAL_US)
    sleep(0.5)
    pi.set_servo_pulsewidth(PIN, 0)
    pi.stop()
