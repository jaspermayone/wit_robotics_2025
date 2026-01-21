// =============================================================================
// WiFi Access Point for Monster Book of Monsters
// Creates a hotspot for web dashboard access
// =============================================================================

#ifndef WIFI_AP_H
#define WIFI_AP_H

#include <stdint.h>
#include <stdbool.h>
#include "config.h"  // All settings centralized

// =============================================================================
// API
// =============================================================================

/**
 * Initialize and start the WiFi access point.
 * @return true on success, false on failure
 */
bool wifi_ap_init(void);

/**
 * Check if WiFi AP is running.
 */
bool wifi_ap_is_active(void);

/**
 * Get the AP's IP address as a string.
 */
const char* wifi_ap_get_ip(void);

/**
 * Get number of connected clients.
 * Note: This may not be accurate on all platforms.
 */
int wifi_ap_get_client_count(void);

/**
 * Stop the WiFi access point.
 */
void wifi_ap_stop(void);

#endif // WIFI_AP_H
