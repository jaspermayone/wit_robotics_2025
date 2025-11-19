from gpiozero import PWMLED
from time import sleep

# Motor connected to GPIO 14
motor = PWMLED(14, frequency=50)

# ESC control values (for 50Hz):
# 0.05 (5%) = 1ms pulse = minimum throttle/stop
# 0.075 (7.5%) = 1.5ms pulse = neutral
# 0.10 (10%) = 2ms pulse = maximum throttle

MIN_THROTTLE = 0.05
MAX_THROTTLE = 0.10

try:
    # Arming sequence - send minimum throttle for 2 seconds
    print("Arming ESC...")
    motor.value = MIN_THROTTLE
    sleep(2)

    print("Running motor test...")
    while True:
        # Slowly increase throttle
        print("Increasing speed...")
        for throttle in range(50, 75, 5):  # From 5% to 7.5% in steps
            motor.value = throttle / 1000
            sleep(0.5)

        # Hold at medium speed
        sleep(2)

        # Return to minimum
        print("Decreasing speed...")
        motor.value = MIN_THROTTLE
        sleep(2)

except KeyboardInterrupt:
    print("Stopping motor...")
    motor.value = MIN_THROTTLE
    sleep(1)
    motor.close()
