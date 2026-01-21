// =============================================================================
// Xbox Controller Reader - Main Entry Point
// Pico 2 W + Bluepad32 Bluetooth Controller Support
// =============================================================================

#include <btstack_run_loop.h>  // BTstack event loop (handles all BT communication)
#include <pico/cyw43_arch.h>   // CYW43 WiFi/BT chip driver (controls the wireless hardware)
#include <pico/stdlib.h>       // Pico standard library (stdio, GPIO, etc.)
#include <uni.h>               // Bluepad32 main header

#include "sdkconfig.h"         // Bluepad32 configuration defines

// Verify we're using custom platform mode (required for Pico W)
#ifndef CONFIG_BLUEPAD32_PLATFORM_CUSTOM
#error "Pico W must use BLUEPAD32_PLATFORM_CUSTOM"
#endif

// Forward declaration - implemented in my_platform.c
// This returns our custom platform callbacks
struct uni_platform* get_my_platform(void);

/**
 * Main entry point
 *
 * Initialization sequence:
 * 1. stdio_init_all() - Set up USB serial for printf output
 * 2. cyw43_arch_init() - Initialize the CYW43 wireless chip (enables Bluetooth)
 * 3. uni_platform_set_custom() - Register our callback functions with Bluepad32
 * 4. uni_init() - Initialize Bluepad32 library
 * 5. btstack_run_loop_execute() - Start the BTstack event loop (never returns)
 */
int main() {
    // Initialize USB serial output so printf() works
    // Connect with: screen /dev/tty.usbmodem* 115200
    stdio_init_all();

    // Initialize the CYW43 wireless chip
    // This powers on the Bluetooth/WiFi hardware on the Pico W
    // Returns non-zero on failure
    if (cyw43_arch_init()) {
        printf("Failed to initialize CYW43 wireless chip!\n");
        return -1;
    }

    // Turn on LED while we're setting up
    // LED will turn off once Bluetooth is ready (in my_platform.c)
    cyw43_arch_gpio_put(CYW43_WL_GPIO_LED_PIN, 1);

    // Register our custom platform callbacks BEFORE initializing Bluepad32
    // This tells Bluepad32 which functions to call for various events
    uni_platform_set_custom(get_my_platform());

    // Initialize Bluepad32 library
    // Parameters: argc, argv (we pass 0, NULL since we're not using command line args)
    uni_init(0, NULL);

    // Start the BTstack event loop
    // This handles all Bluetooth communication and NEVER RETURNS
    // All our code now runs via callbacks defined in my_platform.c
    btstack_run_loop_execute();

    // We never get here
    return 0;
}
