from machine import Pin, PWM
import time
import gc

gc.disable()

pwm = PWM(Pin(2))
pwm.freq(50)

# Inverted values
ARM = 19_000_000      # 1000us at ESC (0%)

def set_throttle(percent):
    pulse_us = 1000 + (percent * 10)
    duty = (20_000 - pulse_us) * 1000
    pwm.duty_ns(duty)

print("Arming ESC...")
pwm.duty_ns(ARM)
print("Power on ESC now")
time.sleep(5)

print("\nSpinning motor at 20% for 3 seconds...")
set_throttle(20)
time.sleep(3)

print("Stopping motor...")
set_throttle(0)
time.sleep(1)

print("Done!")