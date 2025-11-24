# esc_boot_arming.py
from gpiozero import PWMLED
from time import sleep

# 50Hz PWM for typical RC ESCs
motor = PWMLED(14, frequency=50)

# Map PWM duty-cycle at 50Hz to microseconds:
# 1.0ms ≈ 0.05, 1.5ms ≈ 0.075, 2.0ms ≈ 0.10
STOP = 0.05       # use 0.075 if your ESC is bidirectional and expects neutral to arm
MID  = 0.075
MAX  = 0.10

def set(val):
    motor.value = max(0.0, min(1.0, val))

def ramp(start, end, duration=1.0, steps=50):
    step_delay = duration / steps
    delta = (end - start) / steps
    v = start
    for _ in range(steps):
        v += delta
        set(v)
        sleep(step_delay)
    set(end)

try:
    # Assert stop immediately so the ESC sees a valid pulse during its boot window
    print("Boot: asserting STOP...")
    set(STOP)
    sleep(2.5)  # hold long enough for ESC to arm (listen for arming beeps)

    while True:
        print("Ramp up...")
        ramp(STOP, MID, duration=2.0)
        print("Hold mid...")
        sleep(3)

        print("Ramp down to STOP...")
        ramp(MID, STOP, duration=2.0)
        print("Hold STOP...")
        sleep(6)

except KeyboardInterrupt:
    print("Safe stop...")
    # Always return to STOP and hold briefly before closing
    set(STOP)
    sleep(1)
    motor.close()
