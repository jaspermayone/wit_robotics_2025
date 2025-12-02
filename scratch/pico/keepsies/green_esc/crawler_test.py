from machine import Pin, PWM
import time
import gc

gc.disable()

pwm = PWM(Pin(2))
pwm.freq(50)

# Inverted values for crawler ESC
NEUTRAL = 18_500_000   # 1500us
FORWARD_SLOW = 18_200_000   # 1800us (30% forward)
REVERSE_SLOW = 18_800_000   # 1200us (30% reverse)

def set_pulse(pulse_us):
    """Set ESC pulse (1000-2000us)"""
    duty = (20_000 - pulse_us) * 1000
    pwm.duty_ns(duty)

print("Crawler ESC Test")
print("Power on ESC now")
print()

# Start at neutral
set_pulse(1500)
time.sleep(3)

print("Forward slow (3 sec)...")
set_pulse(1800)
time.sleep(3)

print("Neutral (2 sec)...")
set_pulse(1500)
time.sleep(2)

print("Reverse slow (3 sec)...")
set_pulse(1200)
time.sleep(3)

print("Neutral - Done!")
set_pulse(1500)