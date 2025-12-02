from machine import Pin, PWM
import time
import gc

gc.disable()

pwm = PWM(Pin(2))
pwm.freq(50)

def set_throttle(percent):
    """Set crawler throttle: -100 (reverse) to +100 (forward)"""
    percent = max(-100, min(100, percent))
    # Map -100 to 100 → 1000us to 2000us (center at 1500us)
    pulse_us = 1500 + (percent * 5)  # ±500us range
    duty = (20_000 - pulse_us) * 1000  # Invert for transistor
    pwm.duty_ns(duty)
    return pulse_us

print("Crawler Control Ready!")
print("Power on ESC now")
print()

# Start at neutral
set_throttle(0)
time.sleep(3)

print("Commands:")
print("  -100 to 100: Set speed (negative = reverse)")
print("  's': Stop (neutral)")
print("  'q': Quit")
print()

try:
    while True:
        cmd = input("Speed (-100 to 100): ").strip().lower()

        if cmd == 'q':
            break
        elif cmd == 's':
            pulse = set_throttle(0)
            print(f"Neutral ({pulse}us)")
        else:
            try:
                speed = int(cmd)
                pulse = set_throttle(speed)
                direction = "FORWARD" if speed > 0 else "REVERSE" if speed < 0 else "NEUTRAL"
                print(f"{direction} {abs(speed)}% ({pulse}us)")
            except:
                print("Invalid. Enter -100 to 100, 's' for stop, 'q' to quit")

except KeyboardInterrupt:
    pass

print("\nStopping...")
set_throttle(0)
time.sleep(1)
print("Done!")