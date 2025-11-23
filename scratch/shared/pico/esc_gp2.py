# esc_gp2.py
# Control a brushless motor ESC using Raspberry Pi Pico (MicroPython) on GP2 (PWM A1).
# Most hobby ESCs expect 50 Hz with ~1000–2000 microsecond pulses.

from machine import Pin, PWM
import time

LED = Pin("LED", Pin.OUT)  # On-board LED
LED.on()

# Signal pin to ESC: GP2
SIG_PIN = 2
pwm = PWM(Pin(SIG_PIN))
pwm.freq(50)  # 50 Hz servo signal

# Pulse width configuration (adjust if your ESC specifies different limits)
MIN_US = 1000   # min throttle / disarm
MID_US = 1500   # mid throttle
MAX_US = 2000   # max throttle

# Hard safety clamps to avoid out-of-range pulses
ABS_MIN_US = 900
ABS_MAX_US = 2100

# Track last throttle for smooth ramps
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
    # Keep _last_throttle consistent
    global _last_throttle
    _last_throttle = 0.0

def arm(hold_seconds: float = 3.0) -> None:
    """
    Common arming: send MIN_US for a few seconds after ESC power-up until ready tones.
    Some ESCs need longer; watch for beeps.
    """
    stop()
    time.sleep(hold_seconds)

def calibrate_throttle(max_hold_s: float = 3.0, min_hold_s: float = 3.0) -> None:
    """
    Optional ESC throttle range calibration:
    1) Power ESC while sending MAX_US; wait for beeps.
    2) Switch to MIN_US; wait for confirm beeps.
    Consult your ESC manual. Only run when prompted.
    """
    print("Calibration: sending MAX")
    set_pulse_us(MAX_US)
    time.sleep(max_hold_s)
    print("Calibration: sending MIN")
    set_pulse_us(MIN_US)
    time.sleep(min_hold_s)
    print("Calibration done")

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

def demo() -> None:
    """Example sequence: arm → ramp up → hold → ramp down → stop."""
    print("Arming...")
    arm(hold_seconds=3.0)

    print("Ramp to 20%")
    ramp_to(0.30, duration_s=3.0, steps=30)
    time.sleep(10.0)

    print("Ramp down")
    ramp_to(0.0, duration_s=2.0, steps=40)

    print("Stop")
    stop()

if __name__ == "__main__":
    demo()
