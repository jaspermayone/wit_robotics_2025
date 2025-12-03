import board
import busioimport adafruiut_lsm9ds0

class TempSensor:
    def __init__(self, pin):
        self.pin = pin
        i2c = busio.I2C(board.SCL, board.SDA)
        self.sensor = adafruit_lsm9ds0.LSM9DS0_I2C(self.i2c)

    def getTemp(self):
        return self.sensor.temperature
