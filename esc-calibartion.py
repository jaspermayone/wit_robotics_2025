from gpiozero import PWMLED
from time import sleep

pin = int(input("Enter GPIO pin for motor to calibrate: "))
motor = PWMLED(pin, frequency=50)

print("ESC Calibration Procedure")
print("1. Disconnect motor power")
print("2. Press Enter when ready")
input()

print("Sending maximum throttle...")
motor.value = 0.10  # Maximum
print("3. Connect motor power NOW")
print("4. Wait for beeps, then press Enter")
input()

print("Sending minimum throttle...")
motor.value = 0.05  # Minimum
print("ESC should beep to confirm calibration")
sleep(3)

print("Calibration complete! Testing...")
motor.value = 0.06  # Slight throttle
sleep(1)
motor.value = 0.05
motor.close()
