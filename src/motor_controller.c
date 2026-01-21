// =============================================================================
// Motor Controller Implementation
// Tank/arcade drive mixing, weapon control, and failsafe
// =============================================================================

#include "motor_controller.h"
#include <stdio.h>
#include <stdlib.h>
#include "pico/time.h"

// Helper: Apply deadband to eliminate stick drift
static int apply_deadband(int value) {
    if (abs(value) < MOTOR_DEADBAND) {
        return 0;
    }
    return value;
}

// Helper: Clamp value to range
static int clamp(int value, int min, int max) {
    if (value < min) return min;
    if (value > max) return max;
    return value;
}

// Helper: Update command timestamp for failsafe
static void update_command_time(motor_controller_t* mc) {
    mc->last_command_time_ms = to_ms_since_boot(get_absolute_time());
    mc->failsafe_triggered = false;
}

void motor_controller_init(motor_controller_t* mc) {
    printf("Initializing motor controller...\n");

    // Initialize drive motors
    motor_init(&mc->motor_left, PIN_MOTOR_LEFT, DRIVE_MIN_US, DRIVE_MID_US, DRIVE_MAX_US);
    motor_init(&mc->motor_right, PIN_MOTOR_RIGHT, DRIVE_MIN_US, DRIVE_MID_US, DRIVE_MAX_US);

    // Initialize weapon motor
    motor_init(&mc->weapon, PIN_WEAPON, WEAPON_MIN_US, WEAPON_MID_US, WEAPON_MAX_US);

    // Initialize state
    mc->left_speed = 0;
    mc->right_speed = 0;
    mc->weapon_speed = 0;
    mc->weapon_armed = false;
    mc->last_command_time_ms = to_ms_since_boot(get_absolute_time());
    mc->failsafe_triggered = false;

    // Start with everything stopped
    motor_controller_stop_all(mc);

    printf("Motor controller ready (weapon DISARMED)\n");
}

void motor_controller_set_left(motor_controller_t* mc, int speed) {
    speed = apply_deadband(speed);
    speed = clamp(speed, -MOTOR_MAX_SPEED, MOTOR_MAX_SPEED);

    motor_set_speed(&mc->motor_left, speed, MOTOR_BIDIRECTIONAL);
    mc->left_speed = speed;
    update_command_time(mc);
}

void motor_controller_set_right(motor_controller_t* mc, int speed) {
    speed = apply_deadband(speed);
    speed = clamp(speed, -MOTOR_MAX_SPEED, MOTOR_MAX_SPEED);

    motor_set_speed(&mc->motor_right, speed, MOTOR_BIDIRECTIONAL);
    mc->right_speed = speed;
    update_command_time(mc);
}

void motor_controller_tank_drive(motor_controller_t* mc, int left, int right) {
    motor_controller_set_left(mc, left);
    motor_controller_set_right(mc, right);
}

void motor_controller_arcade_drive(motor_controller_t* mc, int throttle, int turn) {
    // Apply deadband to inputs
    throttle = apply_deadband(throttle);
    turn = apply_deadband(turn);

    // Arcade mixing: throttle controls forward/back, turn controls rotation
    int left = throttle + turn;
    int right = throttle - turn;

    // Normalize if over max speed (preserve ratio)
    int max_val = abs(left);
    if (abs(right) > max_val) {
        max_val = abs(right);
    }

    if (max_val > MOTOR_MAX_SPEED) {
        left = (left * MOTOR_MAX_SPEED) / max_val;
        right = (right * MOTOR_MAX_SPEED) / max_val;
    }

    motor_controller_set_left(mc, left);
    motor_controller_set_right(mc, right);
}

void motor_controller_set_weapon(motor_controller_t* mc, int speed) {
    // Weapon only works if armed
    if (!mc->weapon_armed) {
        speed = 0;
    }

    speed = clamp(speed, 0, MOTOR_MAX_SPEED);

    // Weapon is typically unidirectional (forward only)
    motor_set_speed(&mc->weapon, speed, false);
    mc->weapon_speed = speed;
    update_command_time(mc);
}

void motor_controller_arm_weapon(motor_controller_t* mc) {
    mc->weapon_armed = true;
    motor_arm(&mc->weapon);
    printf("*** WEAPON ARMED ***\n");
}

void motor_controller_disarm_weapon(motor_controller_t* mc) {
    bool was_armed = mc->weapon_armed;
    mc->weapon_armed = false;
    motor_disarm(&mc->weapon);

    // Stop weapon immediately
    motor_set_speed(&mc->weapon, 0, false);
    mc->weapon_speed = 0;

    if (was_armed) {
        printf("*** WEAPON DISARMED ***\n");
    }
}

bool motor_controller_is_weapon_armed(motor_controller_t* mc) {
    return mc->weapon_armed;
}

void motor_controller_stop_all(motor_controller_t* mc) {
    // Stop drive motors
    motor_stop(&mc->motor_left, MOTOR_BIDIRECTIONAL);
    motor_stop(&mc->motor_right, MOTOR_BIDIRECTIONAL);
    mc->left_speed = 0;
    mc->right_speed = 0;

    // Disarm and stop weapon
    motor_controller_disarm_weapon(mc);
}

bool motor_controller_check_failsafe(motor_controller_t* mc) {
    if (!FAILSAFE_ENABLED) {
        return false;
    }

    uint32_t now = to_ms_since_boot(get_absolute_time());
    uint32_t elapsed = now - mc->last_command_time_ms;

    if (elapsed > FAILSAFE_TIMEOUT_MS) {
        if (!mc->failsafe_triggered) {
            // Only print if motors were actually running
            if (mc->left_speed != 0 || mc->right_speed != 0 || mc->weapon_speed != 0) {
                printf("Failsafe: motors stopped\n");
            }
            motor_controller_stop_all(mc);
            mc->failsafe_triggered = true;
        }
        return true;
    }

    return false;
}

void motor_controller_get_status(motor_controller_t* mc, int* left, int* right, int* weapon, bool* armed) {
    if (left) *left = mc->left_speed;
    if (right) *right = mc->right_speed;
    if (weapon) *weapon = mc->weapon_speed;
    if (armed) *armed = mc->weapon_armed;
}
