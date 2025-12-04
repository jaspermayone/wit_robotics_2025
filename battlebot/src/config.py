# config.py - Central configuration for battlebot

# WiFi Access Point Settings
AP_SSID = 'Monster Book of Monsters'
AP_PASSWORD = 'battlebot123'  # Min 8 characters
AP_CHANNEL = 11  # Less crowded channel

ALLOWED_MACS = [
  '70:8c:f2:b1:a6:66',  # Jasper's laptop
]

# Authentication
ADMIN_PASSWORD = 'admin123'  # Change this!
SESSION_TIMEOUT = 3600  # 1 hour in seconds

# Hardware Pin Assignments
PIN_SD_CS = 17    # SD card chip select
PIN_SD_SCK = 18   # SD card SPI clock
PIN_SD_MOSI = 19  # SD card SPI MOSI
PIN_SD_MISO = 16  # SD card SPI MISO

# ESC Motor Pins (PWM signal only - no direction pins needed)
PIN_MOTOR_LEFT_PWM = 0
PIN_MOTOR_RIGHT_PWM = 1
PIN_WEAPON_PWM = 2

PIN_BATTERY_ADC = 26  # ADC0
PIN_STATUS_LED = 25   # Onboard LED

# Logging Settings
LOG_DIR = '/sd/logs'
LOG_FILE_PREFIX = 'match'
LOG_MAX_SIZE_MB = 10  # Max size per log file
LOG_ROTATION_COUNT = 5  # Keep last 5 logs

# Logging rates (Hz)
LOG_RATE_MOTORS = 100      # Motor commands
LOG_RATE_TELEMETRY = 50    # Sensor data
LOG_RATE_DIAGNOSTICS = 10  # System health

# Telemetry Settings
TELEMETRY_ENABLE_UDP = False  # Disabled - telemetry only via web interface
TELEMETRY_UDP_PORT = 5005
TELEMETRY_UDP_IP = '192.168.4.2'  # Your laptop IP (if UDP enabled)

# Motor Settings
MOTOR_PWM_FREQ = 50        # 50Hz for ESC (servo-style PWM)
MOTOR_MAX_SPEED = 100      # Percentage
MOTOR_DEADBAND = 5         # Ignore inputs below this %

# ESC PWM Pulse Width Settings (microseconds)
MOTOR_MIN_US = 1000        # Minimum pulse width (idle/reverse)
MOTOR_MID_US = 1500        # Mid pulse width (stopped for bidirectional)
MOTOR_MAX_US = 2000        # Maximum pulse width (full forward)
WEAPON_MIN_US = 1000       # Weapon ESC minimum
WEAPON_MID_US = 1500       # Weapon ESC mid
WEAPON_MAX_US = 2000       # Weapon ESC maximum

# Motor Behavior
MOTOR_BIDIRECTIONAL = False  # True if ESCs support reverse (most don't)
MOTOR_ARM_TIME = 3.0         # Seconds to wait during ESC arming sequence

# Battery Monitoring
BATTERY_MIN_VOLTAGE = 10.0  # Emergency stop below this
BATTERY_MAX_VOLTAGE = 12.6  # Fully charged
BATTERY_CELLS = 3           # 3S LiPo
BATTERY_ADC_RATIO = 5.7     # Voltage divider ratio

# Safety Settings
ENABLE_FAILSAFE = True
FAILSAFE_TIMEOUT_MS = 500  # Stop if no command for 500ms
ENABLE_LOW_BATTERY_CUTOFF = True

# Debug Settings
DEBUG_MODE = True
VERBOSE_LOGGING = False