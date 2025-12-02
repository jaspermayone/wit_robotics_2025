from machine import Pin, PWM
import time
import gc

gc.disable()

pwm = PWM(Pin(2))
pwm.freq(50)

# Inverted values for transistor
# ESC sees: 1000us = min, 2000us = max
# Pico outputs: 19000us = min, 18000us = max
MIN = 19_000_000   # 1000us
MAX = 18_000_000   # 2000us

print("=" * 40)
print("ESC CALIBRATION for GPM080")
print("=" * 40)
print("\nStep 1: Setting FULL THROTTLE")
print("DO NOT connect battery yet!")
pwm.duty_ns(MAX)

input("Press Enter when ready to connect battery...")

print("\nConnect battery NOW!")
print("ESC should beep and recognize full throttle")
time.sleep(3)

print("\nStep 2: Setting ZERO THROTTLE")
pwm.duty_ns(MIN)
print("ESC should beep confirming calibration")
time.sleep(3)

print("\n" + "=" * 40)
print("CALIBRATION COMPLETE!")
print("=" * 40)
print("\nESC is now calibrated and armed")
print("Ready for motor test")