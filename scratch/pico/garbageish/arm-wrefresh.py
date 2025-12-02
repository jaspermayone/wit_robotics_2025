# from machine import Pin, PWM
# import time

# # Configuration
# SIG_PIN = 2  # Signal pin to ESC: GP2

# # Setup PWM on the ESC pin
# pwm = PWM(Pin(SIG_PIN))
# pwm.freq(50)  # 50 Hz servo signal

# # Use duty_ns for precise timing
# # 1000us = 1,000,000 nanoseconds for arming
# ARM_PULSE_NS = 1_000_000

# print(f"Setting pulse width to {ARM_PULSE_NS}ns (1000us)")
# pwm.duty_ns(ARM_PULSE_NS)
# print("ESC armed. Signal should be stable now.")
# print("Press Ctrl+C to stop")

# # Keep program running
# try:
#     while True:
#         time.sleep(1)
# except KeyboardInterrupt:
#     print("\nStopping...")
#     pwm.duty_ns(0)
#     pwm.deinit()
#     print("PWM disabled")


from machine import Pin, PWM
import time

# Signal pin to ESC: GP2
pwm = PWM(Pin(2))
pwm.freq(50)
pwm.duty_ns(1_000_000)  # 1000us = 1ms pulse

print("ESC armed - signal active")
print("Press Ctrl+C to stop")

while True:
    time.sleep(1)
