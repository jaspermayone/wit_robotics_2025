from machine import Pin, PWM
import time

# Signal pin to ESC: GP2
pwm = PWM(Pin(2))

# Try setting frequency very explicitly
requested_freq = 50
pwm.freq(requested_freq)

# Read back what frequency was actually set
actual_freq = pwm.freq()

print(f"Requested frequency: {requested_freq} Hz")
print(f"Actual frequency: {actual_freq} Hz")

# Set pulse width
pwm.duty_ns(1_000_000)  # 1000us

print(f"Pulse width set to: 1000us")
print(f"Period should be: {1000000/actual_freq}us ({1/actual_freq}s)")
print("\nSignal active. Check scope for:")
print("  - Frequency should be ~50Hz (20ms period)")
print("  - Pulse width should be ~1ms")
print("\nPress Ctrl+C to stop")

while True:
    time.sleep(1)
