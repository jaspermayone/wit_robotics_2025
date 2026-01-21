// =============================================================================
// ESC Motor Driver for Pico 2 W
// Controls brushless ESCs using 50Hz PWM (servo-style pulse widths)
// =============================================================================

#ifndef MOTOR_H
#define MOTOR_H

#include <stdint.h>
#include <stdbool.h>
#include "pico/stdlib.h"  // For uint and Pico types

// Default ESC timing (microseconds)
#define ESC_DEFAULT_MIN_US   1000  // Full reverse / idle
#define ESC_DEFAULT_MID_US   1500  // Stopped (for bidirectional ESCs)
#define ESC_DEFAULT_MAX_US   2000  // Full forward
#define ESC_DEFAULT_FREQ_HZ  50    // Standard servo/ESC frequency

// Safety limits (absolute min/max to prevent ESC damage)
#define ESC_ABS_MIN_US  900
#define ESC_ABS_MAX_US  2100

// Motor instance structure
typedef struct {
    uint gpio_pin;           // GPIO pin number
    uint slice_num;          // PWM slice number (derived from pin)
    uint channel;            // PWM channel (A or B)
    uint16_t min_us;         // Minimum pulse width (microseconds)
    uint16_t mid_us;         // Middle pulse width (stopped)
    uint16_t max_us;         // Maximum pulse width (microseconds)
    float last_throttle;     // Last set throttle value (0.0 - 1.0)
    bool armed;              // Whether motor is armed
} motor_t;

/**
 * Initialize a motor on the specified GPIO pin.
 * Sets up PWM at 50Hz and starts with motor stopped.
 *
 * @param motor     Pointer to motor structure to initialize
 * @param gpio_pin  GPIO pin connected to ESC signal wire
 * @param min_us    Minimum pulse width in microseconds (default: 1000)
 * @param mid_us    Middle pulse width in microseconds (default: 1500)
 * @param max_us    Maximum pulse width in microseconds (default: 2000)
 */
void motor_init(motor_t* motor, uint gpio_pin, uint16_t min_us, uint16_t mid_us, uint16_t max_us);

/**
 * Initialize motor with default timing (1000/1500/2000 microseconds).
 */
void motor_init_default(motor_t* motor, uint gpio_pin);

/**
 * Set raw pulse width in microseconds.
 * Clamped to safety limits (ESC_ABS_MIN_US to ESC_ABS_MAX_US).
 *
 * @param motor  Motor to control
 * @param us     Pulse width in microseconds
 */
void motor_set_pulse_us(motor_t* motor, uint16_t us);

/**
 * Set throttle as a value from 0.0 to 1.0.
 * Maps linearly from min_us to max_us.
 *
 * @param motor    Motor to control
 * @param throttle Throttle value (0.0 = min_us, 1.0 = max_us)
 */
void motor_set_throttle(motor_t* motor, float throttle);

/**
 * Set speed as a value from -100 to 100.
 * For bidirectional ESCs: -100 = full reverse, 0 = stop, 100 = full forward
 * For unidirectional ESCs: Uses absolute value (0-100 range)
 *
 * @param motor         Motor to control
 * @param speed         Speed value (-100 to 100)
 * @param bidirectional True if ESC supports reverse
 */
void motor_set_speed(motor_t* motor, int speed, bool bidirectional);

/**
 * Stop motor immediately (sets to min_us for unidirectional, mid_us for bidirectional).
 */
void motor_stop(motor_t* motor, bool bidirectional);

/**
 * Arm the motor (allows throttle commands to take effect).
 */
void motor_arm(motor_t* motor);

/**
 * Disarm the motor and stop it.
 */
void motor_disarm(motor_t* motor);

/**
 * Check if motor is armed.
 */
bool motor_is_armed(motor_t* motor);

#endif // MOTOR_H
