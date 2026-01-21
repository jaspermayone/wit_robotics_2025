// =============================================================================
// Telemetry Module for Monster Book of Monsters
// Battery monitoring, CPU temp, uptime tracking
// =============================================================================

#ifndef TELEMETRY_H
#define TELEMETRY_H

#include <stdint.h>
#include <stdbool.h>
#include "config.h"  // All settings centralized

// =============================================================================
// TELEMETRY DATA
// =============================================================================

typedef struct {
    // Battery
    float battery_voltage;
    uint8_t battery_percent;

    // System
    float cpu_temp_c;
    uint32_t uptime_ms;
    uint32_t loop_time_us;

    // Status flags
    bool battery_low;
    bool battery_critical;
    bool overtemp;
} telemetry_data_t;

// =============================================================================
// API
// =============================================================================

/**
 * Initialize telemetry (ADC, etc.)
 */
void telemetry_init(void);

/**
 * Update all telemetry readings.
 * Call this periodically (e.g., 10-50Hz).
 *
 * @param loop_time_us  Optional: microseconds since last call (for tracking)
 */
void telemetry_update(uint32_t loop_time_us);

/**
 * Get current telemetry data.
 */
telemetry_data_t* telemetry_get_data(void);

/**
 * Read battery voltage.
 * @return Voltage in volts
 */
float telemetry_read_battery(void);

/**
 * Read CPU temperature.
 * @return Temperature in Celsius
 */
float telemetry_read_cpu_temp(void);

/**
 * Check if battery is critically low (should trigger emergency stop).
 */
bool telemetry_is_battery_critical(void);

/**
 * Check if battery is low (should warn user).
 */
bool telemetry_is_battery_low(void);

/**
 * Get uptime in milliseconds.
 */
uint32_t telemetry_get_uptime_ms(void);

/**
 * Print telemetry summary to console.
 */
void telemetry_print_summary(void);

#endif // TELEMETRY_H
