# logger.py - Binary logging system for battlebot telemetry

import struct
import machine
import sdcard
import os
import time
from config import *

class BinaryLogger:
    """
    Efficient binary logger for high-frequency battlebot data.

    Log Entry Format (24 bytes):
    - timestamp: uint32 (4 bytes) - milliseconds since boot
    - motor_left: int16 (2 bytes) - PWM value -100 to 100
    - motor_right: int16 (2 bytes) - PWM value -100 to 100
    - weapon_speed: int16 (2 bytes) - PWM value 0 to 100
    - battery_voltage: uint16 (2 bytes) - voltage * 100 (e.g., 1240 = 12.40V)
    - current_draw: uint16 (2 bytes) - current in mA
    - imu_accel_x: int16 (2 bytes) - acceleration * 100
    - imu_accel_y: int16 (2 bytes) - acceleration * 100
    - imu_accel_z: int16 (2 bytes) - acceleration * 100
    - status_flags: uint8 (1 byte) - bit flags for various states
    - error_code: uint8 (1 byte) - error code if any
    - checksum: uint16 (2 bytes) - simple checksum for validation
    """

    ENTRY_SIZE = 24
    ENTRY_FORMAT = '<IhhhHHhhhBBH'  # Little-endian format string

    # Status flag bits
    FLAG_ARMED = 0x01
    FLAG_FAILSAFE = 0x02
    FLAG_LOW_BATTERY = 0x04
    FLAG_OVERTEMP = 0x08
    FLAG_IMU_VALID = 0x10
    FLAG_WIFI_CONNECTED = 0x20

    def __init__(self):
        self.file = None
        self.current_match = 0
        self.entries_written = 0
        self.start_time_ms = time.ticks_ms()

        # Initialize SD card
        self._init_sd_card()

        # Create new log file
        self._create_new_log()

    def _init_sd_card(self):
        """Initialize SD card over SPI"""
        try:
            spi = machine.SPI(0,
                            baudrate=1000000,
                            polarity=0,
                            phase=0,
                            bits=8,
                            firstbit=machine.SPI.MSB,
                            sck=machine.Pin(PIN_SD_SCK),
                            mosi=machine.Pin(PIN_SD_MOSI),
                            miso=machine.Pin(PIN_SD_MISO))

            cs = machine.Pin(PIN_SD_CS, machine.Pin.OUT)
            self.sd = sdcard.SDCard(spi, cs)

            # Mount SD card
            os.mount(self.sd, '/sd')
            print("SD card initialized successfully")

            # Create logs directory if it doesn't exist
            try:
                os.mkdir(LOG_DIR)
            except OSError:
                pass  # Directory already exists

        except Exception as e:
            print(f"SD card initialization failed: {e}")
            raise

    def _create_new_log(self):
        """Create a new log file with incremented match number"""
        # Find next available match number
        existing_logs = [f for f in os.listdir(LOG_DIR) if f.startswith(LOG_FILE_PREFIX)]

        if existing_logs:
            numbers = [int(f.split('_')[1].split('.')[0]) for f in existing_logs if '_' in f]
            self.current_match = max(numbers) + 1 if numbers else 1
        else:
            self.current_match = 1

        # Create new log file
        filename = f"{LOG_DIR}/{LOG_FILE_PREFIX}_{self.current_match:03d}.bin"
        self.file = open(filename, 'wb')

        # Write header
        self._write_header()

        print(f"Created new log: {filename}")

        # Clean up old logs
        self._rotate_logs()

    def _write_header(self):
        """Write log file header with metadata"""
        header = struct.pack('<4sHHI',
                           b'BTBL',  # Magic number: BaTtle Bot Log
                           1,        # Version
                           self.ENTRY_SIZE,
                           self.start_time_ms)
        self.file.write(header)
        self.file.flush()

    def log_entry(self, motor_left, motor_right, weapon_speed,
                  battery_voltage, current_draw=0,
                  imu_accel=(0, 0, 0), status_flags=0, error_code=0):
        """
        Log a single entry to the binary log file.

        Args:
            motor_left: Left motor PWM (-100 to 100)
            motor_right: Right motor PWM (-100 to 100)
            weapon_speed: Weapon PWM (0 to 100)
            battery_voltage: Battery voltage in volts
            current_draw: Current draw in amps
            imu_accel: Tuple of (x, y, z) acceleration in g's
            status_flags: Status flag bits
            error_code: Error code (0 = no error)
        """
        if not self.file:
            return

        # Convert values to appropriate formats
        timestamp = time.ticks_diff(time.ticks_ms(), self.start_time_ms)
        battery_mv = int(battery_voltage * 100)
        current_ma = int(current_draw * 1000)
        accel_x = int(imu_accel[0] * 100)
        accel_y = int(imu_accel[1] * 100)
        accel_z = int(imu_accel[2] * 100)

        # Calculate simple checksum
        checksum = (timestamp + motor_left + motor_right + weapon_speed +
                   battery_mv + current_ma + accel_x + accel_y + accel_z +
                   status_flags + error_code) & 0xFFFF

        # Pack data
        data = struct.pack(self.ENTRY_FORMAT,
                          timestamp,
                          motor_left,
                          motor_right,
                          weapon_speed,
                          battery_mv,
                          current_ma,
                          accel_x,
                          accel_y,
                          accel_z,
                          status_flags,
                          error_code,
                          checksum)

        # Write to file
        self.file.write(data)
        self.entries_written += 1

        # Flush every 100 entries for safety
        if self.entries_written % 100 == 0:
            self.file.flush()

        # Check if log file is too large
        if self.entries_written * self.ENTRY_SIZE > LOG_MAX_SIZE_MB * 1024 * 1024:
            self._create_new_log()

    def _rotate_logs(self):
        """Keep only the most recent LOG_ROTATION_COUNT log files"""
        logs = sorted([f for f in os.listdir(LOG_DIR) if f.startswith(LOG_FILE_PREFIX)])

        while len(logs) > LOG_ROTATION_COUNT:
            old_log = logs.pop(0)
            try:
                os.remove(f"{LOG_DIR}/{old_log}")
                print(f"Deleted old log: {old_log}")
            except:
                pass

    def close(self):
        """Close the current log file"""
        if self.file:
            self.file.flush()
            self.file.close()
            self.file = None
            print(f"Closed log with {self.entries_written} entries")

    def get_stats(self):
        """Get logging statistics"""
        return {
            'match': self.current_match,
            'entries': self.entries_written,
            'uptime_ms': time.ticks_diff(time.ticks_ms(), self.start_time_ms),
            'size_kb': (self.entries_written * self.ENTRY_SIZE) / 1024
        }