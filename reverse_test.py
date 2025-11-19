# reverse_test.py

from gpiozero import PWMLED
from time import sleep

# Motor/ESC signal on GPIO 14, 50 Hz
motor = PWMLED(14, frequency=50)

# Pulse widths in fraction of period at 50 Hz (20 ms period):
# 1.0 ms -> 0.05, 1.5 ms -> 0.075, 2.0 ms -> 0.10
PULSE_1MS   = 0.05
PULSE_1_5MS = 0.075
PULSE_2MS   = 0.10

# Safety margins: many ESCs require some deadband around neutral
NEUTRAL     = PULSE_1_5MS         # 1.5 ms
FWD_MIN     = 0.080               # ~1.6 ms (small forward)
REV_MIN     = 0.070               # ~1.4 ms (small reverse)
FWD_MAX     = PULSE_2MS           # 2.0 ms
REV_MAX     = PULSE_1MS           # 1.0 ms

def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))

try:
    print("Arming ESC with neutral...")
    motor.value = NEUTRAL
    sleep(2.0)

    print("Entering reverse test...")
    # Many reversible ESCs require going to neutral before reverse
    motor.value = NEUTRAL
    sleep(1.0)

    # Ramp into reverse gently
    for v in [0.074, 0.073, 0.072, 0.071, 0.070]:  # approach ~1.4 ms
        motor.value = clamp(v, REV_MAX, NEUTRAL)
        print(f"Reverse throttle value={motor.value:.3f}")
        sleep(0.6)

    # Hold reverse
    sleep(2.0)

    # Back to neutral before going forward again
    print("Back to neutral...")
    motor.value = NEUTRAL
    sleep(1.5)

    print("Forward test...")
    for v in [0.080, 0.082, 0.085]:  # small forward ramp
        motor.value = clamp(v, NEUTRAL, FWD_MAX)
        print(f"Forward throttle value={motor.value:.3f}")
        sleep(0.6)

    print("Returning to neutral and stop.")
    motor.value = NEUTRAL
    sleep(2.0)

except KeyboardInterrupt:
    print("Emergency stop to neutral...")
    motor.value = NEUTRAL
    sleep(1.0)
finally:
    motor.close()
