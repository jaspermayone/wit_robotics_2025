from machine import Pin, PWM

pwm = PWM(Pin(2))
pwm.freq(50)
pwm.duty_ns(1_000_000)

print("PWM active on GP2")
print("50Hz, 1000us pulse")

while True:
    pass
