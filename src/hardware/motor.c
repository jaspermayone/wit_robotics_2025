// =============================================================================
// ESC Motor Driver Implementation
// Uses Pico SDK hardware PWM for precise 50Hz ESC control
// =============================================================================

#include "motor.h"
#include "config.h"
#include <stdio.h>
#include "hardware/pwm.h"
#include "hardware/clocks.h"
#include "hardware/gpio.h"

// PWM configuration for 50Hz operation
// Pico runs at 125MHz by default
// For 50Hz with good resolution: 125MHz / (wrap * divider) = 50Hz
// Using wrap=20000 and divider=125 gives exactly 50Hz with 1us resolution
#define PWM_WRAP     20000  // 20ms period = 50Hz
#define PWM_DIVIDER  125.0f // Clock divider

void motor_init(motor_t* motor, uint gpio_pin, uint16_t min_us, uint16_t mid_us, uint16_t max_us) {
    motor->gpio_pin = gpio_pin;
    motor->min_us = min_us;
    motor->mid_us = mid_us;
    motor->max_us = max_us;
    motor->last_throttle = 0.0f;
    motor->armed = false;

    // Configure GPIO for PWM
    gpio_set_function(gpio_pin, GPIO_FUNC_PWM);

    // Get PWM slice and channel for this pin
    motor->slice_num = pwm_gpio_to_slice_num(gpio_pin);
    motor->channel = pwm_gpio_to_channel(gpio_pin);

    // Configure PWM for 50Hz with 1us resolution
    pwm_set_wrap(motor->slice_num, PWM_WRAP - 1);
    pwm_set_clkdiv(motor->slice_num, PWM_DIVIDER);

    // Enable PWM first
    pwm_set_enabled(motor->slice_num, true);

    // Start with minimum throttle for ESC arming
    // Some bidirectional ESCs still need min_us at startup to arm
    motor_set_pulse_us(motor, min_us);

    printf("Motor initialized on GPIO %d (slice %d, channel %d)\n",
           gpio_pin, motor->slice_num, motor->channel);
}

void motor_init_default(motor_t* motor, uint gpio_pin) {
    motor_init(motor, gpio_pin, ESC_DEFAULT_MIN_US, ESC_DEFAULT_MID_US, ESC_DEFAULT_MAX_US);
}

void motor_set_pulse_us(motor_t* motor, uint16_t us) {
    // Clamp to safety limits
    if (us < ESC_ABS_MIN_US) {
        us = ESC_ABS_MIN_US;
    } else if (us > ESC_ABS_MAX_US) {
        us = ESC_ABS_MAX_US;
    }

    uint16_t level = us;
#if MOTOR_INVERT_SIGNAL
    // Invert signal if using inverting transistor
    level = PWM_WRAP - us;
#endif

    // Debug: print pulse width changes
    static uint16_t last_level[8] = {0};
    if (level != last_level[motor->gpio_pin] && motor->gpio_pin < 8) {
        printf("GPIO%d: %dus\n", motor->gpio_pin, us);
        last_level[motor->gpio_pin] = level;
    }

    // Set PWM level (with our config, level = microseconds directly)
    pwm_set_chan_level(motor->slice_num, motor->channel, level);
}

void motor_set_throttle(motor_t* motor, float throttle) {
    // Clamp throttle to 0.0 - 1.0
    if (throttle < 0.0f) {
        throttle = 0.0f;
    } else if (throttle > 1.0f) {
        throttle = 1.0f;
    }

    // Map throttle to pulse width
    uint16_t us = motor->min_us + (uint16_t)(throttle * (motor->max_us - motor->min_us));

    motor_set_pulse_us(motor, us);
    motor->last_throttle = throttle;
}

void motor_set_speed(motor_t* motor, int speed, bool bidirectional) {
    // Clamp speed to -100 to 100
    if (speed < -100) speed = -100;
    if (speed > 100) speed = 100;

    float throttle;
    if (bidirectional) {
        // Map -100..100 to 0.0..1.0 (0.5 = stopped)
        throttle = (speed + 100) / 200.0f;
    } else {
        // Forward only - use absolute value
        throttle = (float)((speed < 0) ? -speed : speed) / 100.0f;
    }

    motor_set_throttle(motor, throttle);
}

void motor_stop(motor_t* motor, bool bidirectional) {
    if (bidirectional) {
        // For bidirectional ESCs, mid_us is stopped
        motor_set_pulse_us(motor, motor->mid_us);
    } else {
        // For unidirectional ESCs, min_us is stopped/idle
        motor_set_pulse_us(motor, motor->min_us);
    }
    motor->last_throttle = bidirectional ? 0.5f : 0.0f;
}

void motor_arm(motor_t* motor) {
    motor->armed = true;
}

void motor_disarm(motor_t* motor) {
    motor->armed = false;
}

bool motor_is_armed(motor_t* motor) {
    return motor->armed;
}
