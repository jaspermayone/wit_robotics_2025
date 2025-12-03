# esc_motor.py
# MicroPython class to control a brushless ESC on Raspberry Pi Pico using PWM.
# Matches your previous behavior but as a reusable class.

from machine import Pin, PWM
import time


class Motor:
    """
    High-level ESC motor controller for MicroPython.

    - 50 Hz PWM (servo-style) with microsecond pulse widths
    - Throttle 0.0..1.0 mapped linearly to MIN_US..MAX_US
    - Safety clamps (ABS_MIN_US..ABS_MAX_US)
    - Arming, stop, ramping, and optional calibration helpers
    """

    def __init__(
        self,
        signal_pin: int,
        freq_hz: int = 50,
        min_us: int = 1000,
        mid_us: int = 1500,
        max_us: int = 2000,
        abs_min_us: int = 900,
        abs_max_us: int = 2100,
        led_pin_name: str = "LED",
    ):
        # Configure LED (optional visual cue)
        try:
            self.led = Pin(led_pin_name, Pin.OUT)
            self.led.on()
        except Exception:
            self.led = None  # Some boards may not have "LED"

        # PWM setup
        self.pwm = PWM(Pin(signal_pin))
        self.pwm.freq(freq_hz)

        # Pulse configuration
        self.MIN_US = int(min_us)
        self.MID_US = int(mid_us)
        self.MAX_US = int(max_us)
        self.ABS_MIN_US = int(abs_min_us)
        self.ABS_MAX_US = int(abs_max_us)

        # State
        self._last_throttle = 0.0
        self._armed = False

        # Cache period in nanoseconds (not strictly needed for duty_ns)
        self._period_ns = int(1_000_000_000 // freq_hz)

    def set_pulse_us(self, us: int) -> None:
        """
        Set PWM pulse width in microseconds, clamped to safety limits.
        Uses duty_ns for precise control independent of 16-bit duty resolution.
        """
        if us < self.ABS_MIN_US:
            us = self.ABS_MIN_US
        elif us > self.ABS_MAX_US:
            us = self.ABS_MAX_US
        self.pwm.duty_ns(us * 1000)  # convert microseconds to nanoseconds

    def set_throttle(self, t: float) -> None:
        """
        Set throttle in [0.0..1.0]. Maps linearly to MIN_US..MAX_US.
        Reverse is not supported here; clamp negatives to 0.0.
        """
        if t < 0.0:
            t = 0.0
        elif t > 1.0:
            t = 1.0
        us = int(self.MIN_US + t * (self.MAX_US - self.MIN_US))
        self.set_pulse_us(us)
        self._last_throttle = t

    def stop(self) -> None:
        """
        Immediately command MIN_US (idle). Keeps last throttle in sync.
        """
        self.set_pulse_us(self.MIN_US)
        self._last_throttle = 0.0

    def arm(self, hold_seconds: float = 3.0) -> None:
        """
        Send MIN_US for a few seconds to allow ESC arming beeps/sequence.
        """
        self.stop()
        time.sleep(hold_seconds)
        self._armed = True

    def disarm(self) -> None:
        """
        Disarm by sending minimum and clearing armed flag.
        """
        self.stop()
        self._armed = False

    def ramp_to(self, target: float, duration_s: float = 2.0, steps: int = 50) -> None:
        """
        Smoothly ramp from current throttle to target over the specified duration.
        """
        if target < 0.0:
            target = 0.0
        elif target > 1.0:
            target = 1.0

        start = self._last_throttle
        # Avoid divide-by-zero while still performing a single set step
        steps = max(1, int(steps))
        dt = duration_s / steps if duration_s > 0 else 0.0

        for i in range(steps + 1):
            # Linear interpolation
            t = start + (target - start) * (i / steps)
            self.set_throttle(t)
            if dt > 0:
                time.sleep(dt)

    def shutdown(self) -> None:
        """
        Safe shutdown: set to minimum and deinit PWM.
        """
        try:
            self.stop()
        finally:
            try:
                self.pwm.deinit()
            except AttributeError:
                # Some MicroPython ports don't have deinit
                pass
            self._armed = False


def demo() -> None:
    """
    Example sequence: arm → ramp up → hold → ramp down → stop.
    Mirrors your previous demo, with slightly clearer printouts.
    """
    esc = Motor(signal_pin=2)
    print("Arming...")
    esc.arm(hold_seconds=3.0)

    print("Ramp to 30%")
    esc.ramp_to(0.30, duration_s=3.0, steps=30)
    time.sleep(10.0)

    print("Ramp down")
    esc.ramp_to(0.0, duration_s=2.0, steps=40)

    print("Stop")
    esc.stop()

    print("Shutdown")
    esc.shutdown()


if __name__ == "__main__":
    demo()