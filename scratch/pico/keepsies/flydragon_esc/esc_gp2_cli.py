# esc_gp2_cli.py
# CLI tool to control brushless motor ESC using Raspberry Pi Pico (MicroPython) on GP2.

from machine import Pin, PWM
import time

LED = Pin("LED", Pin.OUT)
LED.on()

# Signal pin to ESC: GP2
SIG_PIN = 2
pwm = PWM(Pin(SIG_PIN))
pwm.freq(50)  # 50 Hz servo signal

# Pulse width configuration
MIN_US = 1000
MID_US = 1500
MAX_US = 2000

# Hard safety clamps
ABS_MIN_US = 900
ABS_MAX_US = 2100

# Track last throttle
_last_throttle = 0.0

def set_pulse_us(us: int) -> None:
    """Set PWM pulse width in microseconds, clamped to safety limits."""
    if us < ABS_MIN_US:
        us = ABS_MIN_US
    elif us > ABS_MAX_US:
        us = ABS_MAX_US
    pwm.duty_ns(us * 1000)

def set_throttle(t: float) -> None:
    """Set throttle 0.0..1.0 → MIN_US..MAX_US (linear)."""
    global _last_throttle
    if t < 0.0:
        t = 0.0
    elif t > 1.0:
        t = 1.0
    us = int(MIN_US + t * (MAX_US - MIN_US))
    set_pulse_us(us)
    _last_throttle = t

def stop() -> None:
    """Immediately command min throttle."""
    set_pulse_us(MIN_US)
    global _last_throttle
    _last_throttle = 0.0

def arm(hold_seconds: float = 3.0) -> None:
    """Send MIN_US for a few seconds to arm ESC."""
    stop()
    time.sleep(hold_seconds)

def ramp_to(target: float, duration_s: float = 2.0, steps: int = 50) -> None:
    """Smoothly ramp from current throttle to target over duration."""
    global _last_throttle
    if target < 0.0:
        target = 0.0
    elif target > 1.0:
        target = 1.0
    start = _last_throttle
    dt = duration_s / steps if steps > 0 else duration_s
    for i in range(steps + 1):
        t = start + (target - start) * (i / steps)
        set_throttle(t)
        time.sleep(dt)

def run_throttle_test(percent: float, hold_seconds: float) -> None:
    """
    Complete test sequence:
    - Arm ESC
    - Ramp to specified throttle percentage
    - Hold for specified duration
    - Ramp back down
    - Stop
    """
    throttle = percent / 100.0

    print(f"\n=== ESC Throttle Test ===")
    print(f"Target: {percent}% ({throttle:.2f})")
    print(f"Hold duration: {hold_seconds}s\n")

    print("Arming ESC...")
    arm(hold_seconds=3.0)

    print(f"Ramping to {percent}%...")
    ramp_to(throttle, duration_s=3.0, steps=30)

    print(f"Holding at {percent}% for {hold_seconds}s...")
    time.sleep(hold_seconds)

    print("Ramping down...")
    ramp_to(0.0, duration_s=2.0, steps=40)

    print("Stopped.")
    stop()
    print("=== Test complete ===\n")

def cli() -> None:
    """Interactive CLI for running throttle tests."""
    print("\n" + "="*40)
    print("ESC Throttle Control CLI")
    print("="*40)

    while True:
        try:
            print("\nEnter 'q' to quit")

            # Get throttle percentage
            percent_input = input("Throttle percentage (0-100): ").strip()
            if percent_input.lower() == 'q':
                print("Stopping motor and exiting...")
                stop()
                break

            percent = float(percent_input)
            if percent < 0 or percent > 100:
                print("Error: Percentage must be between 0 and 100")
                continue

            # Get hold duration
            duration_input = input("Hold duration (seconds): ").strip()
            if duration_input.lower() == 'q':
                print("Stopping motor and exiting...")
                stop()
                break

            duration = float(duration_input)
            if duration < 0:
                print("Error: Duration must be positive")
                continue

            # Run the test
            run_throttle_test(percent, duration)

        except ValueError:
            print("Error: Please enter valid numbers")
        except KeyboardInterrupt:
            print("\n\nInterrupted! Stopping motor...")
            stop()
            break
        except Exception as e:
            print(f"Error: {e}")
            stop()

if __name__ == "__main__":
    try:
        cli()
    except KeyboardInterrupt:
        print("\nShutting down...")
        stop()