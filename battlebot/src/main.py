# main.py - BattleBot main control loop

import time
import machine
from config import *
# from logger import BinaryLogger  # Disabled - no SD card
from motor_controller import MotorController
from telemetry import TelemetryCollector
from wifi_ap import WiFiAccessPoint
from web_server import WebServer

class BattleBot:
    """
    Main battlebot controller class.
    Coordinates logging, telemetry, motor control, and web interface.
    """

    def __init__(self):
        print("\n" + "="*50)
        print("🤖 BattleBot Controller Starting...")
        print("="*50 + "\n")

        # Initialize status LED
        self.status_led = machine.Pin(PIN_STATUS_LED, machine.Pin.OUT)
        self.blink_status(3)

        # Initialize subsystems
        # Logger disabled - no SD card
        self.logger = None

        print("Initializing motor controller...")
        self.motors = MotorController()

        print("Initializing telemetry...")
        self.telemetry = TelemetryCollector()

        print("Initializing WiFi Access Point...")
        self.wifi_ap = WiFiAccessPoint()


        print("Initializing web server...")
        self.web_server = WebServer(self.wifi_ap, self.motors, self.telemetry)
        self.web_server.start_server()

        # Timing tracking
        self.last_log_time = time.ticks_ms()
        self.last_telemetry_time = time.ticks_ms()
        self.last_diagnostic_time = time.ticks_ms()

        # Calculate intervals
        self.log_interval_ms = int(1000 / LOG_RATE_MOTORS)
        self.telemetry_interval_ms = int(1000 / LOG_RATE_TELEMETRY)
        self.diagnostic_interval_ms = int(1000 / LOG_RATE_DIAGNOSTICS)

        # Performance tracking
        self.loop_count = 0
        self.loop_start_time = time.ticks_ms()

        print("\n✓ All systems initialized")
        print(f"✓ Ready for battle!\n")
        self.blink_status(2)

    def run(self):
        """
        Main control loop.
        Runs at maximum speed, with different subsystems updating at their own rates.
        """
        print("Entering main control loop...")

        try:
            while True:
                loop_start = time.ticks_us()

                # Handle web requests (non-blocking)
                self.web_server.handle_requests()

                # Check motor failsafe (disabled for testing)
                # if self.motors.check_failsafe():
                #     print("⚠ FAILSAFE TRIGGERED")
                #     self.status_led.value(1)  # LED on to indicate failsafe
                if False:
                    pass
                else:
                    # Blink LED to show alive
                    if self.loop_count % 500 == 0:
                        self.status_led.value(not self.status_led.value())

                # Update telemetry at configured rate
                current_time = time.ticks_ms()
                if time.ticks_diff(current_time, self.last_telemetry_time) >= self.telemetry_interval_ms:
                    loop_time = time.ticks_diff(time.ticks_us(), loop_start)
                    self.telemetry.update_all(loop_time)
                    self.last_telemetry_time = current_time

                # Log data at configured rate (disabled - no SD card)
                # if time.ticks_diff(current_time, self.last_log_time) >= self.log_interval_ms:
                #     self._log_current_state()
                #     self.last_log_time = current_time

                # Print diagnostics
                # if DEBUG_MODE and time.ticks_diff(current_time, self.last_diagnostic_time) >= self.diagnostic_interval_ms:
                #     self._print_diagnostics()
                #     self.last_diagnostic_time = current_time

                # # Check for critical battery (disabled for testing)
                # # if ENABLE_LOW_BATTERY_CUTOFF and self.telemetry.is_battery_critical():
                # #     print("⚠ CRITICAL BATTERY - EMERGENCY STOP")
                # #     self.motors.stop_all()
                # #     self.blink_status(10)

                # self.loop_count += 1

                # # Small delay to prevent tight loop (adjust as needed)
                # time.sleep_ms(1)

        except KeyboardInterrupt:
            print("\n\nShutdown requested...")
            self.shutdown()
        except Exception as e:
            print(f"\n⚠ CRITICAL ERROR: {e}")
            self.motors.stop_all()
            self.shutdown()
            raise

    def _log_current_state(self):
        """Log current state to binary log file"""
        motor_status = self.motors.get_status()
        telemetry = self.telemetry.last_telemetry

        # Get status flags
        status_flags = self.telemetry.get_status_flags(motor_status)

        # Log entry
        self.logger.log_entry(
            motor_left=motor_status['left'],
            motor_right=motor_status['right'],
            weapon_speed=motor_status['weapon'],
            battery_voltage=telemetry['battery_voltage'],
            current_draw=telemetry['current_draw'],
            imu_accel=telemetry['imu_accel'],
            status_flags=status_flags,
            error_code=0
        )

    def _print_diagnostics(self):
        """Print diagnostic information to console"""
        motor_status = self.motors.get_status()
        telemetry = self.telemetry.get_summary()

        # Calculate loop rate
        elapsed = time.ticks_diff(time.ticks_ms(), self.loop_start_time)
        loop_rate = (self.loop_count * 1000) / elapsed if elapsed > 0 else 0

        print(f"\n--- Diagnostics (Loop: {loop_rate:.1f} Hz) ---")
        print(f"Motors: L={motor_status['left']:+4d}% R={motor_status['right']:+4d}% W={motor_status['weapon']:3d}%")
        print(f"Battery: {telemetry['Battery']}")
        print(f"CPU: {telemetry['CPU Temp']}")
        print(f"Armed: {motor_status['armed']} | Failsafe: {motor_status['failsafe_ok']}")

    def blink_status(self, count):
        """Blink status LED"""
        for _ in range(count):
            self.status_led.value(1)
            time.sleep_ms(100)
            self.status_led.value(0)
            time.sleep_ms(100)

    def shutdown(self):
        """Clean shutdown"""
        print("Stopping motors...")
        self.motors.stop_all()

        if self.logger:
            print("Closing log file...")
            self.logger.close()

        print("Shutdown complete.")
        self.blink_status(3)


# Entry point
if __name__ == '__main__':
    try:
        bot = BattleBot()
        bot.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        # Emergency stop
        try:
            motors = MotorController()
            motors.stop_all()
        except:
            pass