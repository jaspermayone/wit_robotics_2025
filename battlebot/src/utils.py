# utils.py - Utility functions for battlebot

import time
import machine

def constrain(value, min_val, max_val):
    """Constrain value between min and max"""
    return max(min_val, min(max_val, value))

def map_range(value, in_min, in_max, out_min, out_max):
    """
    Map value from one range to another.
    Similar to Arduino's map() function.
    """
    return (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

def apply_deadband(value, deadband):
    """Apply deadband to eliminate small values (like joystick drift)"""
    if abs(value) < deadband:
        return 0
    return value

def exponential_curve(value, expo=0.5):
    """
    Apply exponential curve to input value.
    expo: 0 = linear, higher = more expo (more precise around center)
    """
    sign = 1 if value >= 0 else -1
    abs_val = abs(value)
    return sign * (expo * abs_val * abs_val + (1 - expo) * abs_val)

def low_pass_filter(new_value, old_value, alpha=0.8):
    """
    Simple low-pass filter for smoothing sensor readings.
    alpha: 0 = all new, 1 = all old (higher = more smoothing)
    """
    return alpha * old_value + (1 - alpha) * new_value

class RateLimiter:
    """
    Limit rate of change for smooth motor acceleration.
    """
    def __init__(self, max_rate=50):
        """
        Args:
            max_rate: Maximum change per call (units per second assumed 100Hz)
        """
        self.max_rate = max_rate
        self.last_value = 0

    def update(self, target_value):
        """
        Update towards target value with rate limiting.

        Args:
            target_value: Desired value

        Returns:
            Rate-limited value
        """
        diff = target_value - self.last_value

        # Limit the change
        if abs(diff) > self.max_rate:
            diff = self.max_rate if diff > 0 else -self.max_rate

        self.last_value += diff
        return self.last_value

    def reset(self, value=0):
        """Reset to specific value"""
        self.last_value = value

class Timer:
    """
    Simple timer for periodic tasks.
    """
    def __init__(self, interval_ms):
        self.interval_ms = interval_ms
        self.last_time = time.ticks_ms()

    def expired(self):
        """Check if timer has expired"""
        current = time.ticks_ms()
        if time.ticks_diff(current, self.last_time) >= self.interval_ms:
            self.last_time = current
            return True
        return False

    def reset(self):
        """Reset timer"""
        self.last_time = time.ticks_ms()

    def time_remaining(self):
        """Get time remaining in milliseconds"""
        current = time.ticks_ms()
        elapsed = time.ticks_diff(current, self.last_time)
        remaining = self.interval_ms - elapsed
        return max(0, remaining)

class Watchdog:
    """
    Software watchdog timer for detecting freezes.
    """
    def __init__(self, timeout_ms=1000, callback=None):
        self.timeout_ms = timeout_ms
        self.callback = callback
        self.last_feed = time.ticks_ms()
        self.triggered = False

    def feed(self):
        """Feed the watchdog to prevent timeout"""
        self.last_feed = time.ticks_ms()
        self.triggered = False

    def check(self):
        """
        Check if watchdog has timed out.

        Returns:
            True if timed out
        """
        if self.triggered:
            return True

        current = time.ticks_ms()
        if time.ticks_diff(current, self.last_feed) >= self.timeout_ms:
            self.triggered = True
            if self.callback:
                self.callback()
            return True

        return False

class MovingAverage:
    """
    Calculate moving average for smoothing sensor data.
    """
    def __init__(self, window_size=10):
        self.window_size = window_size
        self.values = []

    def update(self, value):
        """Add new value and return moving average"""
        self.values.append(value)

        if len(self.values) > self.window_size:
            self.values.pop(0)

        return sum(self.values) / len(self.values)

    def reset(self):
        """Clear all values"""
        self.values = []

    def get_average(self):
        """Get current average without adding new value"""
        if not self.values:
            return 0
        return sum(self.values) / len(self.values)

def format_uptime(ms):
    """
    Format uptime milliseconds into human-readable string.

    Args:
        ms: Milliseconds since boot

    Returns:
        String like "1h 23m 45s"
    """
    seconds = ms // 1000
    minutes = seconds // 60
    hours = minutes // 60

    seconds = seconds % 60
    minutes = minutes % 60

    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

def format_bytes(bytes):
    """
    Format bytes into human-readable string.

    Args:
        bytes: Number of bytes

    Returns:
        String like "1.5 MB"
    """
    if bytes < 1024:
        return f"{bytes} B"
    elif bytes < 1024 * 1024:
        return f"{bytes / 1024:.1f} KB"
    else:
        return f"{bytes / (1024 * 1024):.1f} MB"

def clamp_int16(value):
    """Clamp value to int16 range (-32768 to 32767)"""
    return max(-32768, min(32767, int(value)))

def clamp_uint16(value):
    """Clamp value to uint16 range (0 to 65535)"""
    return max(0, min(65535, int(value)))

def debug_print(message, enabled=True):
    """Conditional debug printing"""
    if enabled:
        timestamp = time.ticks_ms()
        print(f"[{timestamp:8d}] {message}")