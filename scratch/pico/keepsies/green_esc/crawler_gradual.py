from machine import Pin, PWM
import time
import gc

gc.disable()

pwm = PWM(Pin(2))
pwm.freq(50)

def set_pulse(pulse_us):
    """Set ESC pulse (1000-2000us)"""
    duty = (20_000 - pulse_us) * 1000
    pwm.duty_ns(duty)
    print(f"  {pulse_us}us", end="\r")

print("Crawler ESC Gradual Ramp Test")
print("Power on ESC now")
print()

# Start at neutral
print("Starting at neutral (1500us)...")
set_pulse(1500)
time.sleep(2)

# Gradual ramp forward
print("\nRamping forward (1500 → 1800us)...")
for pulse in range(1500, 1801, 10):  # 10us steps
    set_pulse(pulse)
    time.sleep(0.1)

print("\nHolding forward...")
time.sleep(2)

# Ramp back to neutral
print("\nRamping back to neutral (1800 → 1500us)...")
for pulse in range(1800, 1499, -10):
    set_pulse(pulse)
    time.sleep(0.1)

print("\nAt neutral...")
time.sleep(2)

# Gradual ramp reverse
print("\nRamping reverse (1500 → 1200us)...")
for pulse in range(1500, 1199, -10):
    set_pulse(pulse)
    time.sleep(0.1)

print("\nHolding reverse...")
time.sleep(2)

# Ramp back to neutral
print("\nRamping back to neutral (1200 → 1500us)...")
for pulse in range(1200, 1501, 10):
    set_pulse(pulse)
    time.sleep(0.1)

print("\nNeutral - Done!")
set_pulse(1500)