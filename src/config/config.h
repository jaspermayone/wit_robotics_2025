// =============================================================================
// Monster Book of Monsters - Central Configuration
// All hardware pins, settings, and tunables in one place
// =============================================================================

#ifndef CONFIG_H
#define CONFIG_H

#include "secrets.h"  // Contains SECRET_WIFI_PASSWORD (gitignored)

// =============================================================================
// ROBOT IDENTITY
// =============================================================================

#define ROBOT_NAME  "Monster Book of Monsters"

// =============================================================================
// HARDWARE PIN ASSIGNMENTS
// =============================================================================

// ESC Motor Pins (PWM signal to ESC)
#define PIN_MOTOR_LEFT_FRONT   0   // GP0 - Left front drive motor
#define PIN_MOTOR_RIGHT_FRONT  1   // GP1 - Right front drive motor
#define PIN_MOTOR_LEFT_BACK    2   // GP2 - Left back drive motor
#define PIN_MOTOR_RIGHT_BACK   3   // GP3 - Right back drive motor
#define PIN_WEAPON             4   // GP4 - Weapon motor

// Analog Inputs
#define PIN_BATTERY_ADC  26  // ADC0 - Battery voltage divider

// Status LED is handled by CYW43 (CYW43_WL_GPIO_LED_PIN)

// =============================================================================
// MOTOR SETTINGS
// =============================================================================

// ESC PWM Configuration (50Hz servo-style)
#define MOTOR_PWM_FREQ      50      // Hz

// ESC Pulse Width Timing (microseconds)
#define DRIVE_MIN_US        1000    // Full reverse / idle
#define DRIVE_MID_US        1500    // Stopped (for bidirectional)
#define DRIVE_MAX_US        2000    // Full forward
#define WEAPON_MIN_US       1000
#define WEAPON_MID_US       1500
#define WEAPON_MAX_US       2000

#define ARM_SEQUENCE_ONE    1480
#define ARM_SEQUENCE_ONE_DELAY  4000

// Motor Behavior
#define MOTOR_BIDIRECTIONAL true   // Try unidirectional arming
#define MOTOR_INVERT_SIGNAL false   // No inverting transistor on GPIO 0
#define MOTOR_MAX_SPEED     100     // Maximum speed percentage
#define MOTOR_DEADBAND      10      // Ignore inputs below this %

// =============================================================================
// SAFETY SETTINGS
// =============================================================================

// Failsafe - stops motors if no controller input
#define FAILSAFE_ENABLED     true
#define FAILSAFE_TIMEOUT_MS  500    // Stop if no command for this long

// Low battery cutoff (disable if no battery sensor connected)
#define ENABLE_LOW_BATTERY_CUTOFF  false

// =============================================================================
// BATTERY SETTINGS (3S LiPo)
// =============================================================================

#define BATTERY_CELLS           3
#define BATTERY_MIN_VOLTAGE     10.0f   // Emergency stop (3.33V/cell)
#define BATTERY_LOW_VOLTAGE     10.8f   // Warning (3.6V/cell)
#define BATTERY_CRITICAL_VOLTAGE 10.2f  // Critical (3.4V/cell)
#define BATTERY_MAX_VOLTAGE     12.6f   // Fully charged (4.2V/cell)
#define BATTERY_ADC_RATIO       5.7f    // Voltage divider ratio

// =============================================================================
// WIFI SETTINGS
// =============================================================================

#define WIFI_AP_SSID      "Monster Book of Monsters"
#define WIFI_AP_PASSWORD  SECRET_WIFI_PASSWORD  // From secrets.h
#define WIFI_AP_CHANNEL   11

// AP IP Configuration
#define WIFI_AP_IP        "192.168.4.1"
#define WIFI_AP_NETMASK   "255.255.255.0"
#define WIFI_AP_GATEWAY   "192.168.4.1"

// =============================================================================
// WEB SERVER SETTINGS
// =============================================================================

#define WEB_SERVER_PORT   80

// =============================================================================
// CONTROLLER MAPPING
// =============================================================================

// Xbox controller stick ranges
#define STICK_MIN    -512
#define STICK_MAX     511
#define TRIGGER_MAX   1023

// Invert controls if needed (-1 to invert, 1 for normal)
#define THROTTLE_INVERT  -1  // Push forward = forward (Y axis inverted)
#define TURN_INVERT       1  // Push right = turn right

// =============================================================================
// DEBUG SETTINGS
// =============================================================================

#define DEBUG_MODE           false  // Set true to enable telemetry printing
#define VERBOSE_LOGGING      false
#define TELEMETRY_PRINT_INTERVAL_MS  10000  // Print telemetry every 10 seconds (if DEBUG_MODE)

#endif // CONFIG_H
