# esc_hold_neutral.py
from gpiozero import PWMLED
from time import sleep

motor = PWMLED(14, frequency=50)

# 50Hz mapping: 1000us=0.05, 1500us=0.075, 2000us=0.10
NEUTRAL = 0.076  # slight bias above 0.075; try 0.076–0.078
FORWARD_SMALL = NEUTRAL + 0.010  # small test throttle
RAMP_STEPS = 60

def set(val):
    val = max(0.0, min(1.0, val))
    if abs(motor.value - val) > 1e-4:
        motor.value = val

def ramp(start, end, duration=2.0, steps=RAMP_STEPS):
    step_delay = duration / steps
    delta = (end - start) / steps
    v = start
    for _ in range(steps):
        v += delta
        set(v)
        sleep(step_delay)
    set(end)

try:
    print("Arming at neutral...")
    set(NEUTRAL)
    sleep(3.0)

    while True:
        print("Small forward...")
        ramp(NEUTRAL, FORWARD_SMALL, duration=2.0)
        sleep(2.0)

        print("Return and hold neutral (zero)...")
        ramp(FORWARD_SMALL, NEUTRAL, duration=2.0)
        set(NEUTRAL)
        sleep(8.0)

except KeyboardInterrupt:
    print("Safe neutral stop...")
    set(NEUTRAL)
    sleep(1.0)
    motor.close()
