// =============================================================================
// Telemetry Module Implementation
// ADC-based battery monitoring and system health tracking
// =============================================================================

#include "telemetry.h"
#include <stdio.h>
#include "pico/stdlib.h"
#include "hardware/adc.h"

// Global telemetry data
static telemetry_data_t g_telemetry = {0};
static uint32_t g_start_time_ms = 0;

void telemetry_init(void) {
    printf("Initializing telemetry...\n");

    // Initialize ADC
    adc_init();

    // Configure battery ADC pin (GPIO 26 = ADC0)
    adc_gpio_init(PIN_BATTERY_ADC);

    // Enable temperature sensor (ADC4)
    adc_set_temp_sensor_enabled(true);

    // Record start time
    g_start_time_ms = to_ms_since_boot(get_absolute_time());

    // Initial readings
    telemetry_update(0);

    printf("Telemetry ready - Battery: %.2fV (%d%%), CPU: %.1fC\n",
           g_telemetry.battery_voltage,
           g_telemetry.battery_percent,
           g_telemetry.cpu_temp_c);
}

float telemetry_read_battery(void) {
    // Select ADC input 0 (GPIO 26)
    adc_select_input(0);

    // Read ADC (12-bit, 0-4095)
    uint16_t raw = adc_read();

    // Convert to voltage
    // ADC reference is 3.3V, 12-bit resolution
    // Then apply voltage divider ratio
    float voltage = (raw / 4095.0f) * 3.3f * BATTERY_ADC_RATIO;

    g_telemetry.battery_voltage = voltage;

    // Calculate percentage (linear approximation)
    float percent = ((voltage - BATTERY_MIN_VOLTAGE) /
                    (BATTERY_MAX_VOLTAGE - BATTERY_MIN_VOLTAGE)) * 100.0f;

    if (percent < 0) percent = 0;
    if (percent > 100) percent = 100;
    g_telemetry.battery_percent = (uint8_t)percent;

    // Update status flags
    g_telemetry.battery_low = (voltage < BATTERY_LOW_VOLTAGE);
    g_telemetry.battery_critical = (voltage < BATTERY_CRITICAL_VOLTAGE);

    return voltage;
}

float telemetry_read_cpu_temp(void) {
    // Select ADC input 4 (internal temperature sensor)
    adc_select_input(4);

    // Read ADC
    uint16_t raw = adc_read();

    // Convert to voltage
    float voltage = raw * (3.3f / 4095.0f);

    // Convert to temperature using datasheet formula
    // T = 27 - (V - 0.706) / 0.001721
    float temp = 27.0f - (voltage - 0.706f) / 0.001721f;

    g_telemetry.cpu_temp_c = temp;
    g_telemetry.overtemp = (temp > 70.0f);

    return temp;
}

void telemetry_update(uint32_t loop_time_us) {
    // Update uptime
    g_telemetry.uptime_ms = to_ms_since_boot(get_absolute_time()) - g_start_time_ms;
    g_telemetry.loop_time_us = loop_time_us;

    // Read sensors
    telemetry_read_battery();
    telemetry_read_cpu_temp();
}

telemetry_data_t* telemetry_get_data(void) {
    return &g_telemetry;
}

bool telemetry_is_battery_critical(void) {
    return g_telemetry.battery_critical;
}

bool telemetry_is_battery_low(void) {
    return g_telemetry.battery_low;
}

uint32_t telemetry_get_uptime_ms(void) {
    return g_telemetry.uptime_ms;
}

void telemetry_print_summary(void) {
    printf("--- Telemetry ---\n");
    printf("Battery: %.2fV (%d%%)%s%s\n",
           g_telemetry.battery_voltage,
           g_telemetry.battery_percent,
           g_telemetry.battery_low ? " [LOW]" : "",
           g_telemetry.battery_critical ? " [CRITICAL]" : "");
    printf("CPU Temp: %.1fC%s\n",
           g_telemetry.cpu_temp_c,
           g_telemetry.overtemp ? " [OVERTEMP]" : "");
    printf("Uptime: %lu ms\n", g_telemetry.uptime_ms);
    printf("Loop: %lu us\n", g_telemetry.loop_time_us);
}
