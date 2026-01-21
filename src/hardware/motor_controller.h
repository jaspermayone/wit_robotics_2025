// =============================================================================
// Motor Controller for BattleBot
// High-level control: tank/arcade drive, weapon, failsafe, arming
// =============================================================================

#ifndef MOTOR_CONTROLLER_H
#define MOTOR_CONTROLLER_H

#include <stdint.h>
#include <stdbool.h>
#include "config.h"  // All settings centralized
#include "motor.h"

// =============================================================================
// MOTOR CONTROLLER API
// =============================================================================

// Motor controller state
typedef struct {
    motor_t motor_left;
    motor_t motor_right;
    motor_t weapon;

    // Current speeds (-100 to 100 for drive, 0 to 100 for weapon)
    int left_speed;
    int right_speed;
    int weapon_speed;

    // Weapon arming state (weapon won't spin unless armed)
    bool weapon_armed;

    // Failsafe tracking
    uint32_t last_command_time_ms;
    bool failsafe_triggered;
} motor_controller_t;

/**
 * Initialize the motor controller.
 * Sets up PWM for all motors and starts in stopped/disarmed state.
 */
void motor_controller_init(motor_controller_t* mc);

/**
 * Set left motor speed.
 * @param speed -100 to 100 (negative = reverse if bidirectional)
 */
void motor_controller_set_left(motor_controller_t* mc, int speed);

/**
 * Set right motor speed.
 * @param speed -100 to 100 (negative = reverse if bidirectional)
 */
void motor_controller_set_right(motor_controller_t* mc, int speed);

/**
 * Tank drive control (direct left/right motor control).
 */
void motor_controller_tank_drive(motor_controller_t* mc, int left, int right);

/**
 * Arcade drive control (throttle + turn mixing).
 * @param throttle -100 to 100 (forward/back)
 * @param turn     -100 to 100 (positive = turn right)
 */
void motor_controller_arcade_drive(motor_controller_t* mc, int throttle, int turn);

/**
 * Set weapon speed.
 * Only works if weapon is armed!
 * @param speed 0 to 100
 */
void motor_controller_set_weapon(motor_controller_t* mc, int speed);

/**
 * Arm the weapon (allows it to spin).
 */
void motor_controller_arm_weapon(motor_controller_t* mc);

/**
 * Disarm the weapon (stops it and prevents spinning).
 */
void motor_controller_disarm_weapon(motor_controller_t* mc);

/**
 * Check if weapon is armed.
 */
bool motor_controller_is_weapon_armed(motor_controller_t* mc);

/**
 * Emergency stop - all motors to zero, weapon disarmed.
 */
void motor_controller_stop_all(motor_controller_t* mc);

/**
 * Check and apply failsafe if no commands received recently.
 * Call this periodically (e.g., every main loop iteration).
 * @return true if failsafe was triggered
 */
bool motor_controller_check_failsafe(motor_controller_t* mc);

/**
 * Get current motor status for logging/telemetry.
 */
void motor_controller_get_status(motor_controller_t* mc, int* left, int* right, int* weapon, bool* armed);

#endif // MOTOR_CONTROLLER_H
