from machine import Pin, PWM
import gc

gc.disable()

pwm = PWM(Pin(2))
pwm.freq(50)

# For inverted signal through transistor:
# Normal: 1000us high, 19000us low
# Inverted: 19000us high, 1000us low
# Period = 20000us, so inverted duty = 20000 - 1000 = 19000us

pwm.duty_ns(19_000_000)  # 19ms high = 1ms low after transistor

print("Inverted PWM active for transistor circuit")
print("Should output 1000us LOW pulse (ESC arming)")

while 1:
    pass
