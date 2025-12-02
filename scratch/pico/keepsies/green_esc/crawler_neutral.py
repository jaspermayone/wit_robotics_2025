from machine import Pin, PWM
import time
import gc

gc.disable()

pwm = PWM(Pin(2))
pwm.freq(50)

# Crawler ESC needs 1500us for neutral
# Inverted: 20000 - 1500 = 18500us
NEUTRAL = 18_500_000

print("Setting ESC to NEUTRAL (1500us)")
print("Power on ESC now")
pwm.duty_ns(NEUTRAL)

print("\nESC should stay connected in neutral")
print("Press Ctrl+C to stop")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nStopped")
