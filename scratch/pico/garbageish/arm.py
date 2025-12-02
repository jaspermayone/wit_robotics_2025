from machine import Pin, PWM
import time

# Configuration
SIG_PIN = 2  # Signal pin to ESC: GP2
ARM_PULSE = 1000  # Microseconds (low throttle to arm)

# Setup PWM on the ESC pin
pwm = PWM(Pin(SIG_PIN))
pwm.freq(50)  # 50 Hz servo signal

# Convert microseconds to duty cycle (0-65535 range)
# For 50Hz: period = 20ms = 20000us
# duty = (pulse_width_us / 20000) * 65535
duty = int((ARM_PULSE / 20000) * 65535)

print("Arming ESC...")
pwm.duty_u16(duty)

# Wait for ESC to arm (typically takes 2-5 seconds)
time.sleep(20)

print("ESC armed!")
print("Motor ready for throttle commands")