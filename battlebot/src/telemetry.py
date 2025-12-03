# telemetry.py - Sensor data collection and telemetry

import machine
import time
from config import *

class TelemetryCollector:
    """
    Collects sensor data from various sources and provides
    real-time telemetry over UDP.
    """

    def __init__(self):
        # Battery monitoring via ADC
        self.battery_adc = machine.ADC(machine.Pin(PIN_BATTERY_ADC))

        # IMU placeholder (add your IMU library here)
        self.imu = None
        self.imu_available = False

        # Telemetry data cache
        self.last_telemetry = {
            'battery_voltage': 0.0,
            'battery_percent': 0,
            'current_draw': 0.0,
            'uptime_ms': 0,
            'loop_time_us': 0,
            'cpu_temp': 0.0,
            'imu_accel': (0, 0, 0),
            'imu_gyro': (0, 0, 0),
            'wifi_rssi': 0,
        }

    def read_battery_voltage(self):
        """Read battery voltage from ADC"""
        # Read ADC (0-65535 for 0-3.3V)
        adc_value = self.battery_adc.read_u16()

        # Convert to voltage (accounting for voltage divider)
        voltage = (adc_value / 65535.0) * 3.3 * BATTERY_ADC_RATIO

        self.last_telemetry['battery_voltage'] = voltage

        # Calculate percentage
        percent = ((voltage - BATTERY_MIN_VOLTAGE) /
                  (BATTERY_MAX_VOLTAGE - BATTERY_MIN_VOLTAGE)) * 100
        self.last_telemetry['battery_percent'] = max(0, min(100, int(percent)))

        return voltage

    def read_imu(self):
        """Read IMU data (accelerometer and gyroscope)"""
        if not self.imu_available:
            return (0, 0, 0), (0, 0, 0)

        # TODO: Implement your IMU reading here
        # Example for MPU6050 or similar:
        # accel = self.imu.read_accel()
        # gyro = self.imu.read_gyro()

        accel = (0, 0, 0)
        gyro = (0, 0, 0)

        self.last_telemetry['imu_accel'] = accel
        self.last_telemetry['imu_gyro'] = gyro

        return accel, gyro

    def read_cpu_temp(self):
        """Read Pico W CPU temperature"""
        try:
            sensor_temp = machine.ADC(4)
            voltage = sensor_temp.read_u16() * (3.3 / 65535)
            temperature = 27 - (voltage - 0.706) / 0.001721
            self.last_telemetry['cpu_temp'] = temperature
            return temperature
        except:
            return 0.0

    def update_all(self, loop_time_us=0):
        """Update all telemetry readings"""
        self.last_telemetry['uptime_ms'] = time.ticks_ms()
        self.last_telemetry['loop_time_us'] = loop_time_us

        # Read sensors
        self.read_battery_voltage()
        self.read_imu()
        self.read_cpu_temp()

        return self.last_telemetry

    def is_battery_critical(self):
        """Check if battery is below critical threshold"""
        return self.last_telemetry['battery_voltage'] < BATTERY_MIN_VOLTAGE

    def get_status_flags(self, motor_status):
        """
        Generate status flags byte for logging.

        Returns:
            uint8 with bit flags set
        """
        flags = 0

        if motor_status.get('armed', False):
            flags |= 0x01  # ARMED

        if not motor_status.get('failsafe_ok', True):
            flags |= 0x02  # FAILSAFE

        if self.is_battery_critical():
            flags |= 0x04  # LOW_BATTERY

        if self.last_telemetry['cpu_temp'] > 70:
            flags |= 0x08  # OVERTEMP

        if self.imu_available:
            flags |= 0x10  # IMU_VALID

        # Check WiFi (if we have network module imported)
        try:
            import network
            sta = network.WLAN(network.STA_IF)
            if sta.isconnected():
                flags |= 0x20  # WIFI_CONNECTED
        except:
            pass

        return flags

    def get_summary(self):
        """Get human-readable summary of telemetry"""
        return {
            'Battery': f"{self.last_telemetry['battery_voltage']:.2f}V ({self.last_telemetry['battery_percent']}%)",
            'CPU Temp': f"{self.last_telemetry['cpu_temp']:.1f}°C",
            'Uptime': f"{self.last_telemetry['uptime_ms'] / 1000:.1f}s",
            'Loop Time': f"{self.last_telemetry['loop_time_us']}µs",
        }