# motor_controller.py - Motor control for battlebot using ESC Motor class

import machine
import time
from config import *
from classes.esc_motor import Motor

class MotorController:
    """
    Controls drive motors and weapon using ESC Motor class.
    Includes safety features like failsafe and deadband.
    """

    def __init__(self):
        # Initialize ESC motors
        self.motor_left = Motor(
            signal_pin=PIN_MOTOR_LEFT_PWM,
            freq_hz=MOTOR_PWM_FREQ,
            min_us=MOTOR_MIN_US,
            mid_us=MOTOR_MID_US,
            max_us=MOTOR_MAX_US
        )

        self.motor_right = Motor(
            signal_pin=PIN_MOTOR_RIGHT_PWM,
            freq_hz=MOTOR_PWM_FREQ,
            min_us=MOTOR_MIN_US,
            mid_us=MOTOR_MID_US,
            max_us=MOTOR_MAX_US
        )

        self.weapon = Motor(
            signal_pin=PIN_WEAPON_PWM,
            freq_hz=MOTOR_PWM_FREQ,
            min_us=WEAPON_MIN_US,
            mid_us=WEAPON_MID_US,
            max_us=WEAPON_MAX_US
        )

        # Current motor states (stored as -100 to 100 for logging compatibility)
        self.left_speed = 0
        self.right_speed = 0
        self.weapon_speed = 0

        # Failsafe tracking
        self.last_command_time = time.ticks_ms()
        self.armed = False

        # Initialize stopped
        print("Arming ESCs...")
        self.motor_left.arm(hold_seconds=MOTOR_ARM_TIME)
        self.motor_right.arm(hold_seconds=0.1)  # Already waited for left
        self.weapon.arm(hold_seconds=0.1)
        print("ESCs armed and ready")

        self.stop_all()

    def set_left_motor(self, speed):
        """
        Set left motor speed.

        Args:
            speed: -100 to 100 (negative = reverse)
        """
        speed = self._apply_deadband(speed)
        speed = max(-MOTOR_MAX_SPEED, min(MOTOR_MAX_SPEED, speed))

        # Convert -100 to 100 range to 0.0 to 1.0 throttle
        # Negative values are reverse (if ESC supports bidirectional)
        # For forward-only ESCs, use absolute value
        if MOTOR_BIDIRECTIONAL:
            # Map -100..100 to 0.0..1.0 (0.5 = stopped, <0.5 = reverse, >0.5 = forward)
            throttle = (speed + 100) / 200.0
        else:
            # Forward only - use absolute value
            throttle = abs(speed) / 100.0

        self.motor_left.set_throttle(throttle)
        self.left_speed = speed
        self._update_command_time()

    def set_right_motor(self, speed):
        """
        Set right motor speed.

        Args:
            speed: -100 to 100 (negative = reverse)
        """
        speed = self._apply_deadband(speed)
        speed = max(-MOTOR_MAX_SPEED, min(MOTOR_MAX_SPEED, speed))

        if MOTOR_BIDIRECTIONAL:
            throttle = (speed + 100) / 200.0
        else:
            throttle = abs(speed) / 100.0

        self.motor_right.set_throttle(throttle)
        self.right_speed = speed
        self._update_command_time()

    def set_weapon(self, speed):
        """
        Set weapon motor speed.

        Args:
            speed: 0 to 100 (weapon typically one direction)
        """
        if not self.armed:
            speed = 0

        speed = max(0, min(MOTOR_MAX_SPEED, speed))

        # Weapon is typically forward only
        throttle = speed / 100.0
        self.weapon.set_throttle(throttle)
        self.weapon_speed = speed
        self._update_command_time()

    def set_tank_drive(self, left, right):
        """Convenience method for tank drive control"""
        self.set_left_motor(left)
        self.set_right_motor(right)

    def set_arcade_drive(self, throttle, turn):
        """
        Arcade drive mixing.

        Args:
            throttle: -100 to 100 (forward/back)
            turn: -100 to 100 (left/right)
        """
        left = throttle + turn
        right = throttle - turn

        # Normalize if over 100
        max_val = max(abs(left), abs(right))
        if max_val > 100:
            left = (left / max_val) * 100
            right = (right / max_val) * 100

        self.set_tank_drive(int(left), int(right))

    def arm(self):
        """Arm the weapon - must be called before weapon will spin"""
        self.armed = True
        print("Weapon ARMED")

    def disarm(self):
        """Disarm the weapon - weapon will not spin"""
        self.armed = False
        self.set_weapon(0)
        print("Weapon DISARMED")

    def stop_all(self):
        """Emergency stop - all motors to zero"""
        self.set_left_motor(0)
        self.set_right_motor(0)
        self.set_weapon(0)
        self.disarm()

    def check_failsafe(self):
        """
        Check if failsafe should trigger (no commands received).
        Returns True if failsafe activated.
        """
        if not ENABLE_FAILSAFE:
            return False

        if time.ticks_diff(time.ticks_ms(), self.last_command_time) > FAILSAFE_TIMEOUT_MS:
            self.stop_all()
            return True

        return False

    def _apply_deadband(self, speed):
        """Apply deadband to eliminate stick drift"""
        if abs(speed) < MOTOR_DEADBAND:
            return 0
        return speed

    def _update_command_time(self):
        """Update last command timestamp for failsafe"""
        self.last_command_time = time.ticks_ms()

    def get_status(self):
        """Get current motor status"""
        return {
            'left': self.left_speed,
            'right': self.right_speed,
            'weapon': self.weapon_speed,
            'armed': self.armed,
            'failsafe_ok': not self.check_failsafe()
        }