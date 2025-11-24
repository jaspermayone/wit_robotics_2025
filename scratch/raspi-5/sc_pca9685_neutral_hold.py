# esc_pca9685_neutral_hold.py
# pip install adafruit-circuitpython-pca9685
from time import sleep
from adafruit_pca9685 import PCA9685
import board, busio

i2c = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c)
pca.frequency = 50

CHANNEL = 0  # ESC signal channel

def set_pulse_us(us):
    # 50 Hz -> 20,000 µs period; 12-bit resolution (0..4095)
    duty = int((us / 20000.0) * 4095)
    pca.channels[CHANNEL].duty_cycle = max(0, min(4095, duty))

# Tune neutral slightly high to reduce idle current on your ESC
NEUTRAL_US = 1510   # try 1510–1520 if 1500 disconnects
FORWARD_US = NEUTRAL_US + 120  # modest bump

try:
    # Arming: hold neutral
    set_pulse_us(NEUTRAL_US)
    sleep(1.0)

    while True:
        # Quick bump forward then back to neutral and hold
        set_pulse_us(FORWARD_US); sleep(0.6)
        set_pulse_us(NEUTRAL_US); sleep(1.2)

except KeyboardInterrupt:
    set_pulse_us(NEUTRAL_US)
    sleep(0.5)
    pca.deinit()
