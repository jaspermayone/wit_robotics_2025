// =============================================================================
// Monster Book of Monsters - Main Entry Point
// Pico 2 W + Bluepad32 Bluetooth + WiFi Dashboard
// =============================================================================

#include <btstack_run_loop.h>  // BTstack event loop
#include <pico/cyw43_arch.h>   // CYW43 WiFi/BT chip driver
#include <pico/stdlib.h>       // Pico standard library
#include <uni.h>               // Bluepad32 main header

#include "config.h"            // Central configuration
#include "sdkconfig.h"         // Bluepad32 configuration
#include "telemetry.h"         // Battery, CPU temp monitoring
#include "wifi_ap.h"           // WiFi access point

// Verify we're using custom platform mode (required for Pico W)
#ifndef CONFIG_BLUEPAD32_PLATFORM_CUSTOM
#error "Pico W must use BLUEPAD32_PLATFORM_CUSTOM"
#endif

// Forward declaration - implemented in my_platform.c
struct uni_platform* get_my_platform(void);

/**
 * Main entry point
 *
 * Initialization sequence:
 * 1. stdio_init_all() - USB serial for printf
 * 2. cyw43_arch_init() - Initialize WiFi/BT chip
 * 3. wifi_ap_init() - Start WiFi access point
 * 4. telemetry_init() - Start battery/temp monitoring
 * 5. uni_platform_set_custom() - Register Bluepad32 callbacks
 * 6. uni_init() - Initialize Bluepad32
 * 7. btstack_run_loop_execute() - Start event loop (never returns)
 *
 * Note: Motor controller and web server are initialized in my_platform.c
 * after Bluetooth is fully ready.
 */
int main() {
    // Initialize USB serial output
    // Connect with: screen /dev/tty.usbmodem* 115200
    stdio_init_all();

    // Small delay to allow USB serial to connect
    sleep_ms(2000);

    printf("\n\n");
    printf("==================================================\n");
    printf("  %s\n", ROBOT_NAME);
    printf("  Initializing...\n");
    printf("==================================================\n\n");

    // Initialize the CYW43 wireless chip (WiFi + Bluetooth)
    printf("Initializing CYW43 wireless chip...\n");
    if (cyw43_arch_init()) {
        printf("FATAL: Failed to initialize CYW43!\n");
        return -1;
    }
    printf("CYW43 ready\n");

    // Turn on LED while setting up
    cyw43_arch_gpio_put(CYW43_WL_GPIO_LED_PIN, 1);

    // Start WiFi access point
    printf("\n");
    if (!wifi_ap_init()) {
        printf("WARNING: WiFi AP failed to start\n");
        // Continue anyway - Bluetooth control will still work
    }

    // Initialize telemetry (battery monitoring, CPU temp)
    printf("\n");
    telemetry_init();

    // Register our custom platform callbacks with Bluepad32
    printf("\n");
    printf("Initializing Bluetooth...\n");
    uni_platform_set_custom(get_my_platform());

    // Initialize Bluepad32 library
    uni_init(0, NULL);

    // Start the BTstack event loop
    // This handles all Bluetooth communication and NEVER RETURNS
    // Motor controller and web server are initialized in my_platform.c
    // once Bluetooth is fully ready
    printf("Starting BTstack event loop...\n\n");
    btstack_run_loop_execute();

    // We never get here
    return 0;
}
