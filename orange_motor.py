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

def ramp_throttle(start, end, duration=1.0, steps=50):
    """
    Smoothly ramp throttle from start to end value.
    
    Args:
        start: Starting throttle value (0.05 - 0.10)
        end: Ending throttle value (0.05 - 0.10)
        duration: Total time for the ramp in seconds
        steps: Number of intermediate steps
    """
    step_delay = duration / steps
    step_size = (end - start) / steps
    
    current = start
    for _ in range(steps):
        current += step_size
        motor.value = current
        sleep(step_delay)
