// =============================================================================
// BattleBot Controller for Pico 2 W
// Xbox controller via Bluetooth → Motor control via PWM
// =============================================================================

#include <stddef.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>

#include <pico/stdlib.h>      // For to_ms_since_boot
#include <pico/cyw43_arch.h>  // For controlling the onboard LED
#include <pico/time.h>        // For repeating timer
#include <uni.h>              // Bluepad32 main header

#include "config.h"           // Central configuration
#include "sdkconfig.h"        // Bluepad32 configuration
#include "motor_controller.h" // Motor control
#include "telemetry.h"        // Battery, CPU temp
#include "wifi_ap.h"          // WiFi access point
#include "web_server.h"       // HTTP dashboard

// Sanity check - Pico W requires custom platform mode
#ifndef CONFIG_BLUEPAD32_PLATFORM_CUSTOM
#error "Pico W must use BLUEPAD32_PLATFORM_CUSTOM"
#endif

// =============================================================================
// GLOBAL STATE
// =============================================================================

// Motor controller instance (initialized when Bluetooth is ready)
static motor_controller_t g_motors;
static bool g_motors_initialized = false;

// Previous button state for edge detection (arm/disarm toggle)
static uint32_t g_prev_buttons = 0;
static uint8_t g_prev_misc_buttons = 0;

// Arming requires holding LB+RB for 5 seconds
#define ARM_HOLD_TIME_MS  5000
static uint32_t g_arm_hold_start = 0;
static bool g_arm_hold_active = false;
static int g_last_countdown = -1;  // Track last printed countdown number
static bool g_bumpers_held = false;  // Track if LB+RB are currently held

// Timer for arming countdown (runs independently of controller input)
static struct repeating_timer g_arming_timer;

// =============================================================================
// CONTROL MAPPING
// Map Xbox controller inputs to robot actions (see config.h for settings)
// =============================================================================

/**
 * Map a value from one range to another.
 */
static int map_range(int value, int in_min, int in_max, int out_min, int out_max) {
    return (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
}

/**
 * Check arming countdown - called periodically even when no input changes.
 * This ensures the countdown progresses while holding buttons.
 */
static void check_arming_countdown(void) {
    if (!g_motors_initialized) return;

    uint32_t now = to_ms_since_boot(get_absolute_time());

    if (g_bumpers_held && g_arm_hold_active && !motor_controller_is_weapon_armed(&g_motors)) {
        uint32_t held_time = now - g_arm_hold_start;
        int seconds_left = (ARM_HOLD_TIME_MS - held_time + 999) / 1000;  // Round up

        if (held_time >= ARM_HOLD_TIME_MS) {
            motor_controller_arm_weapon(&g_motors);
            g_last_countdown = -1;
        } else if (seconds_left != g_last_countdown && seconds_left >= 0) {
            g_last_countdown = seconds_left;
            if (seconds_left == 0) {
                printf(">>> ARMING! <<<\n");
            } else {
                printf("  %d...\n", seconds_left);
            }
        }
    }
}

/**
 * Timer callback for arming countdown - fires every 100ms.
 * Also polls CYW43 to ensure WiFi/lwIP packets get processed.
 */
static bool arming_timer_callback(struct repeating_timer *t) {
    (void)t;

    // Poll CYW43 to process WiFi/lwIP packets (DHCP, HTTP, etc.)
    // This is needed because btstack_run_loop_execute() may not service lwIP
    cyw43_arch_poll();

    check_arming_countdown();
    return true;  // Keep repeating
}

/**
 * Process controller input and drive motors.
 * Uses tank drive: left stick Y = left motor, right stick Y = right motor
 */
static void process_controller_input(uni_gamepad_t* gp) {
    if (!g_motors_initialized) {
        return;
    }

    // === DRIVE CONTROL ===
    // Tank drive: each stick controls one side
    // Left stick Y axis → left motor
    // Right stick Y axis → right motor
    int left_speed = map_range(gp->axis_y, STICK_MIN, STICK_MAX, -100, 100) * THROTTLE_INVERT;
    int right_speed = map_range(gp->axis_ry, STICK_MIN, STICK_MAX, -100, 100) * THROTTLE_INVERT;

    motor_controller_tank_drive(&g_motors, left_speed, right_speed);

    // === WEAPON CONTROL ===
    // Right trigger → weapon speed (only if armed)
    int weapon_speed = map_range(gp->throttle, 0, TRIGGER_MAX, 0, 100);
    motor_controller_set_weapon(&g_motors, weapon_speed);

    // === WEAPON ARM/DISARM ===
    // LB + RB held for 5 seconds → arm weapon (stays armed after release)
    // LB + RB tap when armed → disarm weapon
    bool lb_pressed = (gp->buttons & BUTTON_SHOULDER_L) != 0;
    bool rb_pressed = (gp->buttons & BUTTON_SHOULDER_R) != 0;
    bool both_held = lb_pressed && rb_pressed;

    if (both_held && !g_bumpers_held) {
        // Just started holding both bumpers
        g_bumpers_held = true;
        if (motor_controller_is_weapon_armed(&g_motors)) {
            // Already armed - disarm immediately
            motor_controller_disarm_weapon(&g_motors);
        } else {
            // Not armed - start arming sequence
            g_arm_hold_start = to_ms_since_boot(get_absolute_time());
            g_arm_hold_active = true;
            g_last_countdown = (ARM_HOLD_TIME_MS / 1000) + 1;
            printf("\n*** ARMING SEQUENCE ***\n");
            printf("Hold LB+RB for %d seconds...\n", ARM_HOLD_TIME_MS / 1000);
        }
    } else if (!both_held && g_bumpers_held) {
        // Released bumpers
        g_bumpers_held = false;
        if (!motor_controller_is_weapon_armed(&g_motors) && g_arm_hold_active) {
            // Was trying to arm but released early
            printf("Arming cancelled\n");
        }
        g_arm_hold_active = false;
        g_last_countdown = -1;
    }
    // Note: countdown handled by check_arming_countdown() called from timer

    // === EMERGENCY STOP ===
    // Xbox button (system button) → emergency stop all
    bool xbox_pressed = (gp->misc_buttons & MISC_BUTTON_SYSTEM) != 0;
    bool xbox_was_pressed = (g_prev_misc_buttons & MISC_BUTTON_SYSTEM) != 0;

    if (xbox_pressed && !xbox_was_pressed) {
        printf("!!! EMERGENCY STOP !!!\n");
        motor_controller_stop_all(&g_motors);
    }

    // Update previous button state for next iteration
    g_prev_buttons = gp->buttons;
    g_prev_misc_buttons = gp->misc_buttons;
}

// =============================================================================
// PLATFORM CALLBACKS
// =============================================================================

/**
 * Called once when Bluepad32 initializes.
 */
static void my_platform_init(int argc, const char** argv) {
    ARG_UNUSED(argc);
    ARG_UNUSED(argv);
    printf("Monster Book of Monsters - Controller initialized\n");
}

/**
 * Called when Bluetooth stack is fully initialized and ready.
 */
static void my_platform_on_init_complete(void) {
    printf("\n");
    printf("==================================================\n");
    printf("  %s - Ready!\n", ROBOT_NAME);
    printf("==================================================\n");
    printf("\n");

    // Initialize motor controller now that hardware is ready
    motor_controller_init(&g_motors);
    g_motors_initialized = true;

    // Start arming countdown timer (100ms interval)
    add_repeating_timer_ms(100, arming_timer_callback, NULL, &g_arming_timer);

    // Initialize web server (WiFi AP already started in main.c)
    printf("\n");
    web_server_init(&g_motors);

    printf("\n");
    printf("Controls (Tank Drive):\n");
    printf("  Left Stick Y  : Left motor\n");
    printf("  Right Stick Y : Right motor\n");
    printf("  Right Trigger : Weapon speed\n");
    printf("  LB + RB (5s)  : Arm weapon\n");
    printf("  LB + RB (tap) : Disarm weapon (when armed)\n");
    printf("  Xbox Button   : Emergency stop\n");
    printf("\n");
    printf("Waiting for Xbox controller...\n");
    printf("(Turn on controller or hold pair button)\n");
    printf("\n");

    // Start scanning for controllers
    uni_bt_start_scanning_and_autoconnect_unsafe();

    // LED off = waiting for controller
    cyw43_arch_gpio_put(CYW43_WL_GPIO_LED_PIN, 0);
}

/**
 * Called when a Bluetooth device is discovered.
 * Filter to only accept Xbox controllers.
 */
static uni_error_t my_platform_on_device_discovered(bd_addr_t addr, const char* name, uint16_t cod, uint8_t rssi) {
    // Allow devices with "Xbox" in name
    if (name != NULL && strstr(name, "Xbox") != NULL) {
        printf("Xbox controller found: %s (RSSI: %d)\n", name, rssi);
        return UNI_ERROR_SUCCESS;
    }

    // Also allow gamepads by Class of Device (Xbox BLE may have empty name initially)
    if ((cod & 0x050C) == 0x0508) {
        printf("Gamepad found (COD: 0x%04x, RSSI: %d)\n", cod, rssi);
        return UNI_ERROR_SUCCESS;
    }

    // Ignore everything else
    return UNI_ERROR_IGNORE_DEVICE;
}

/**
 * Called when a controller has connected.
 */
static void my_platform_on_device_connected(uni_hid_device_t* d) {
    printf("Controller connected!\n");

    // Stop scanning
    uni_bt_stop_scanning_safe();

    // LED on = controller connected
    cyw43_arch_gpio_put(CYW43_WL_GPIO_LED_PIN, 1);
}

/**
 * Called when a controller disconnects.
 */
static void my_platform_on_device_disconnected(uni_hid_device_t* d) {
    printf("\n");
    printf("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n");
    printf("!!!     CONTROLLER DISCONNECTED - E-STOP      !!!\n");
    printf("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n");

    // SAFETY: Emergency stop all motors immediately
    if (g_motors_initialized) {
        printf(">>> Stopping all motors...\n");
        motor_controller_stop_all(&g_motors);
        printf(">>> All motors stopped, weapon disarmed\n");
    }

    // LED off = no controller
    cyw43_arch_gpio_put(CYW43_WL_GPIO_LED_PIN, 0);

    // Resume scanning for reconnection
    printf("\nScanning for reconnect...\n");
    uni_bt_start_scanning_and_autoconnect_safe();
}

/**
 * Called when a controller is fully ready to use.
 */
static uni_error_t my_platform_on_device_ready(uni_hid_device_t* d) {
    printf("\n");
    printf("*** Controller ready - DRIVE ENABLED ***\n");
    printf("(Weapon is DISARMED - press LB+RB to arm)\n");
    printf("\n");
    return UNI_ERROR_SUCCESS;
}

// =============================================================================
// INPUT DISPLAY (for debugging)
// =============================================================================

static void print_buttons(uint32_t buttons, uint8_t misc_buttons) {
    printf("Buttons: ");

    if (buttons == 0 && misc_buttons == 0) {
        printf("none       ");
    } else {
        if (buttons & BUTTON_A) printf("A ");
        if (buttons & BUTTON_B) printf("B ");
        if (buttons & BUTTON_X) printf("X ");
        if (buttons & BUTTON_Y) printf("Y ");
        if (buttons & BUTTON_SHOULDER_L) printf("LB ");
        if (buttons & BUTTON_SHOULDER_R) printf("RB ");
        if (buttons & BUTTON_TRIGGER_L) printf("LT ");
        if (buttons & BUTTON_TRIGGER_R) printf("RT ");
        if (buttons & BUTTON_THUMB_L) printf("LS ");
        if (buttons & BUTTON_THUMB_R) printf("RS ");
        if (misc_buttons & MISC_BUTTON_START) printf("START ");
        if (misc_buttons & MISC_BUTTON_SELECT) printf("SELECT ");
        if (misc_buttons & MISC_BUTTON_SYSTEM) printf("XBOX ");
    }
}

static const char* dpad_to_string(uint8_t dpad) {
    switch (dpad) {
        case 0:                            return "none";
        case DPAD_UP:                      return "UP";
        case DPAD_DOWN:                    return "DOWN";
        case DPAD_RIGHT:                   return "RIGHT";
        case DPAD_LEFT:                    return "LEFT";
        case (DPAD_UP | DPAD_RIGHT):       return "UP+RIGHT";
        case (DPAD_DOWN | DPAD_RIGHT):     return "DOWN+RIGHT";
        case (DPAD_UP | DPAD_LEFT):        return "UP+LEFT";
        case (DPAD_DOWN | DPAD_LEFT):      return "DOWN+LEFT";
        default:                           return "?";
    }
}

/**
 * Called every time controller sends new input data.
 * This is the main control loop for the robot!
 */
static void my_platform_on_controller_data(uni_hid_device_t* d, uni_controller_t* ctl) {
    static uni_controller_t prev = {0};
    static uint32_t last_telemetry_update = 0;
    static uint32_t last_telemetry_print = 0;

    // Update telemetry periodically (not every frame)
    uint32_t now = to_ms_since_boot(get_absolute_time());
    if (now - last_telemetry_update > 100) {  // 10Hz
        telemetry_update(0);
        last_telemetry_update = now;

        // Check for critical battery
        if (ENABLE_LOW_BATTERY_CUTOFF && telemetry_is_battery_critical()) {
            if (g_motors_initialized && !g_motors.failsafe_triggered) {
                printf("\n!!! CRITICAL BATTERY - EMERGENCY STOP !!!\n");
                motor_controller_stop_all(&g_motors);
            }
        }
    }

    // Print telemetry summary periodically
    if (DEBUG_MODE && (now - last_telemetry_print > TELEMETRY_PRINT_INTERVAL_MS)) {
        telemetry_print_summary();
        last_telemetry_print = now;
    }

    // Check arming countdown (runs even when no input changes)
    check_arming_countdown();

    // Only process if something changed
    if (memcmp(&prev, ctl, sizeof(*ctl)) == 0) {
        // Even if nothing changed, check failsafe
        if (g_motors_initialized) {
            motor_controller_check_failsafe(&g_motors);
        }
        return;
    }
    prev = *ctl;

    if (ctl->klass == UNI_CONTROLLER_CLASS_GAMEPAD) {
        uni_gamepad_t* gp = &ctl->gamepad;

        // === MOTOR CONTROL ===
        process_controller_input(gp);

        // === DEBUG OUTPUT ===
        // Print motor status along with controller state
        int left, right, weapon;
        bool armed;
        motor_controller_get_status(&g_motors, &left, &right, &weapon, &armed);

        printf("Motors: L=%+4d%% R=%+4d%% W=%3d%% [%s] | ",
               left, right, weapon, armed ? "ARMED" : "safe");

        print_buttons(gp->buttons, gp->misc_buttons);
        printf("| DPad: %-10s", dpad_to_string(gp->dpad));
        printf("| Sticks: (%+4d,%+4d) (%+4d,%+4d)",
               gp->axis_x, gp->axis_y, gp->axis_rx, gp->axis_ry);
        printf("| Trig: %4d %4d\n", gp->brake, gp->throttle);
    }
}

/**
 * Called to get platform-specific properties.
 */
static const uni_property_t* my_platform_get_property(uni_property_idx_t idx) {
    ARG_UNUSED(idx);
    return NULL;
}

/**
 * Called for out-of-band events.
 */
static void my_platform_on_oob_event(uni_platform_oob_event_t event, void* data) {
    if (event == UNI_PLATFORM_OOB_BLUETOOTH_ENABLED) {
        printf("Bluetooth scanning: %s\n", (bool)(data) ? "on" : "off");
    }
}

// =============================================================================
// PLATFORM REGISTRATION
// =============================================================================

struct uni_platform* get_my_platform(void) {
    static struct uni_platform plat = {
        .name = "Monster Book of Monsters",
        .init = my_platform_init,
        .on_init_complete = my_platform_on_init_complete,
        .on_device_discovered = my_platform_on_device_discovered,
        .on_device_connected = my_platform_on_device_connected,
        .on_device_disconnected = my_platform_on_device_disconnected,
        .on_device_ready = my_platform_on_device_ready,
        .on_controller_data = my_platform_on_controller_data,
        .on_oob_event = my_platform_on_oob_event,
        .get_property = my_platform_get_property,
    };

    return &plat;
}
