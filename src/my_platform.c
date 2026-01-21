// =============================================================================
// Xbox Controller Reader for Pico 2 W
// Using Bluepad32 library for Bluetooth gamepad support
// =============================================================================

#include <stddef.h>
#include <string.h>
#include <stdio.h>

#include <pico/cyw43_arch.h>  // For controlling the onboard LED
#include <uni.h>              // Bluepad32 main header

#include "sdkconfig.h"        // Bluepad32 configuration

// Sanity check - Pico W requires custom platform mode
#ifndef CONFIG_BLUEPAD32_PLATFORM_CUSTOM
#error "Pico W must use BLUEPAD32_PLATFORM_CUSTOM"
#endif

// =============================================================================
// PLATFORM CALLBACKS
// These functions are called by Bluepad32 at various points in the
// Bluetooth connection lifecycle. We implement them to customize behavior.
// =============================================================================

/**
 * Called once when Bluepad32 initializes.
 * Use this for one-time setup that doesn't depend on Bluetooth being ready.
 */
static void my_platform_init(int argc, const char** argv) {
    ARG_UNUSED(argc);
    ARG_UNUSED(argv);
    printf("Xbox Controller Reader initialized\n");
}

/**
 * Called when Bluetooth stack is fully initialized and ready.
 * This is where we start scanning for controllers.
 */
static void my_platform_on_init_complete(void) {
    printf("Bluetooth ready - waiting for controller...\n");
    printf("Turn on your Xbox controller (or hold pair button for new pairing)\n");

    // Start scanning for Bluetooth devices and auto-connect to known controllers
    // "unsafe" means it's called from the BT thread context (which is fine here)
    uni_bt_start_scanning_and_autoconnect_unsafe();

    // Note: We keep stored keys so previously paired controllers auto-reconnect
    // To force fresh pairing (forget all devices), uncomment this line:
    // uni_bt_del_keys_unsafe();

    // Turn off LED to indicate we're ready and waiting
    cyw43_arch_gpio_put(CYW43_WL_GPIO_LED_PIN, 0);
}

/**
 * Called when a Bluetooth device is discovered during scanning.
 *
 * @param addr  - Bluetooth MAC address of the device
 * @param name  - Device name (may be NULL if not yet known)
 * @param cod   - Class of Device (identifies device type)
 * @param rssi  - Signal strength (higher = closer/stronger)
 *
 * @return UNI_ERROR_SUCCESS to allow connection,
 *         UNI_ERROR_IGNORE_DEVICE to skip this device
 */
static uni_error_t my_platform_on_device_discovered(bd_addr_t addr, const char* name, uint16_t cod, uint8_t rssi) {
    // Allow devices with "Xbox" in name
    if (name != NULL && strstr(name, "Xbox") != NULL) {
        printf("Xbox controller found: %s (RSSI: %d)\n", name, rssi);
        return UNI_ERROR_SUCCESS;
    }

    // Also allow gamepads (COD 0x508 = gamepad) - Xbox controller over BLE may have empty name
    // COD minor class 0x08 in bits 2-7 = gamepad
    if ((cod & 0x050C) == 0x0508) {
        printf("Gamepad found (COD: 0x%04x, RSSI: %d)\n", cod, rssi);
        return UNI_ERROR_SUCCESS;
    }

    // Silently ignore everything else (8BitDo adapter, mice, keyboards, etc.)
    return UNI_ERROR_IGNORE_DEVICE;
}

/**
 * Called when a controller has connected (but may not be fully ready yet).
 */
static void my_platform_on_device_connected(uni_hid_device_t* d) {
    printf("Controller connected!\n");

    // Stop scanning - we have our controller, no need to keep looking
    // This eliminates the noisy log messages from other BT devices
    uni_bt_stop_scanning_safe();

    // LED on to indicate we're connected
    cyw43_arch_gpio_put(CYW43_WL_GPIO_LED_PIN, 1);
}

/**
 * Called when a controller disconnects.
 */
static void my_platform_on_device_disconnected(uni_hid_device_t* d) {
    printf("Controller disconnected - scanning for reconnect...\n");

    // LED off to indicate disconnection
    cyw43_arch_gpio_put(CYW43_WL_GPIO_LED_PIN, 0);

    // Resume scanning so we can reconnect when controller turns back on
    uni_bt_start_scanning_and_autoconnect_safe();
}

/**
 * Called when a controller is fully ready to use.
 * At this point we can start receiving input data.
 */
static uni_error_t my_platform_on_device_ready(uni_hid_device_t* d) {
    printf("Controller ready to use!\n");
    return UNI_ERROR_SUCCESS;
}

// =============================================================================
// INPUT DISPLAY HELPERS
// These functions format controller input for readable serial output
// =============================================================================

/**
 * Print human-readable button names instead of hex codes.
 * Main buttons are in 'buttons' field, misc buttons (start/select/xbox) are separate.
 */
static void print_buttons(uint32_t buttons, uint8_t misc_buttons) {
    printf("Buttons: ");

    if (buttons == 0 && misc_buttons == 0) {
        printf("none       ");  // Padding for alignment
    } else {
        // Check each button bit and print its name if pressed
        if (buttons & BUTTON_A) printf("A ");
        if (buttons & BUTTON_B) printf("B ");
        if (buttons & BUTTON_X) printf("X ");
        if (buttons & BUTTON_Y) printf("Y ");
        if (buttons & BUTTON_SHOULDER_L) printf("LB ");      // Left bumper
        if (buttons & BUTTON_SHOULDER_R) printf("RB ");      // Right bumper
        if (buttons & BUTTON_TRIGGER_L) printf("LT ");       // Left trigger click
        if (buttons & BUTTON_TRIGGER_R) printf("RT ");       // Right trigger click
        if (buttons & BUTTON_THUMB_L) printf("LS ");         // Left stick click
        if (buttons & BUTTON_THUMB_R) printf("RS ");         // Right stick click

        // Misc buttons are in a separate field
        if (misc_buttons & MISC_BUTTON_START) printf("START ");   // Menu button
        if (misc_buttons & MISC_BUTTON_SELECT) printf("SELECT "); // View button
        if (misc_buttons & MISC_BUTTON_SYSTEM) printf("XBOX ");   // Xbox button
    }
}

/**
 * Convert D-pad bitmask to readable direction string.
 * D-pad uses bits: UP=1, DOWN=2, RIGHT=4, LEFT=8
 */
static const char* dpad_to_string(uint8_t dpad) {
    // D-pad is a bitmask, not sequential values
    // DPAD_UP=1, DPAD_DOWN=2, DPAD_RIGHT=4, DPAD_LEFT=8
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
 * This is the main function where you'd add your robot control logic!
 *
 * @param d   - Device handle (for sending rumble, etc.)
 * @param ctl - Controller data (buttons, sticks, triggers)
 */
static void my_platform_on_controller_data(uni_hid_device_t* d, uni_controller_t* ctl) {
    // Keep track of previous state to only print when something changes
    static uni_controller_t prev = {0};

    // Skip printing if nothing changed (reduces serial spam)
    if (memcmp(&prev, ctl, sizeof(*ctl)) == 0) {
        return;
    }
    prev = *ctl;

    // Only handle gamepad-type controllers
    if (ctl->klass == UNI_CONTROLLER_CLASS_GAMEPAD) {
        uni_gamepad_t* gp = &ctl->gamepad;

        // Print current controller state:
        // - buttons: Bitmask of pressed buttons
        // - dpad: D-pad direction (0-8)
        // - axis_x, axis_y: Left stick (-512 to 511)
        // - axis_rx, axis_ry: Right stick (-512 to 511)
        // - brake: Left trigger (0 to 1023)
        // - throttle: Right trigger (0 to 1023)

        print_buttons(gp->buttons, gp->misc_buttons);
        printf("| DPad: %-10s", dpad_to_string(gp->dpad));
        printf("| L(%5d,%5d) ", gp->axis_x, gp->axis_y);
        printf("| R(%5d,%5d) ", gp->axis_rx, gp->axis_ry);
        printf("| LT:%4d RT:%4d\n", gp->brake, gp->throttle);

        // === ADD YOUR ROBOT CONTROL CODE HERE ===
        // Example: Use gp->axis_y for forward/back, gp->axis_x for turning
        // Example: Use gp->throttle and gp->brake for motor speed

        // Simple demo: Toggle LED with A button
        if (gp->buttons & BUTTON_A) {
            cyw43_arch_gpio_put(CYW43_WL_GPIO_LED_PIN, 1);
        } else {
            cyw43_arch_gpio_put(CYW43_WL_GPIO_LED_PIN, 0);
        }
    }
}

/**
 * Called to get platform-specific properties.
 * We don't use this, so just return NULL.
 */
static const uni_property_t* my_platform_get_property(uni_property_idx_t idx) {
    ARG_UNUSED(idx);
    return NULL;
}

/**
 * Called for out-of-band events (special events outside normal flow).
 * Examples: Xbox button pressed, Bluetooth state changes
 */
static void my_platform_on_oob_event(uni_platform_oob_event_t event, void* data) {
    if (event == UNI_PLATFORM_OOB_BLUETOOTH_ENABLED) {
        printf("Bluetooth scanning: %s\n", (bool)(data) ? "on" : "off");
    }
}

// =============================================================================
// PLATFORM REGISTRATION
// This struct tells Bluepad32 which callbacks to use for our platform.
// =============================================================================

/**
 * Returns our platform configuration to Bluepad32.
 * Called from main.c during initialization.
 */
struct uni_platform* get_my_platform(void) {
    static struct uni_platform plat = {
        .name = "Xbox Controller Reader",
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
