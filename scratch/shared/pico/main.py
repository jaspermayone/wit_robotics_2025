from utime import sleep
from machine import Pin, PWM
import time

# Pins (change to match your wiring)
# Pin mapping (change to match your wiring)
IN1_PIN = 10   # Motor driver IN1 (direction)
IN2_PIN = 11   # Motor driver IN2 (direction)
EN_PIN  = 2    # PWM A1 on Pico = GP2 (enable/speed)
LED = Pin("LED", Pin.OUT)  # On-board LED

LED.on()

# Set up direction pins
IN1 = Pin(IN1_PIN, Pin.OUT, value=0)
IN2 = Pin(IN2_PIN, Pin.OUT, value=0)

# Set up PWM on GP2
EN = PWM(Pin(EN_PIN))
EN.freq(50)        # 5 kHz: above audible range, smooth for DC motors
EN.duty_u16(0)        # duty range 0..65535

def set_speed(duty):
    """
    Set motor speed as 0..65535 (uint16).
    Clamp to valid range to avoid ValueError.
    """
    if duty < 0:
        duty = 0
    elif duty > 65535:
        duty = 65535
    EN.duty_u16(duty)

def forward(duty):
    IN1.high()
    IN2.low()
    set_speed(duty)

def backward(duty):
    IN1.low()
    IN2.high()
    set_speed(duty)

def brake():
    # Active brake (short the motor via driver, if supported)
    IN1.high()
    IN2.high()
    set_speed(0)

def coast():
    # No drive: motor freewheels
    IN1.low()
    IN2.low()
    set_speed(0)

# Demo: ramp up/down forward, then reverse
def demo():
    coast()
    time.sleep(0.5)

    # Ramp forward
    for duty in range(0, 50000, 2500):
        forward(duty)
        time.sleep(0.05)

    time.sleep(0.5)
    # Ramp down
    for duty in range(50000, -1, -2500):
        forward(duty)
        time.sleep(0.03)

    coast()
    time.sleep(0.5)

    # Reverse
    for duty in range(0, 40000, 4000):
        backward(duty)
        time.sleep(0.05)

    brake()
    time.sleep(0.5)
    coast()

if __name__ == "__main__":
    demo()