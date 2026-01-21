// =============================================================================
// Web Server for Monster Book of Monsters
// Simple HTTP server for status dashboard
// =============================================================================

#ifndef WEB_SERVER_H
#define WEB_SERVER_H

#include <stdint.h>
#include <stdbool.h>
#include "config.h"  // All settings centralized
#include "motor_controller.h"

// =============================================================================
// API
// =============================================================================

/**
 * Initialize and start the web server.
 * WiFi AP must be initialized first.
 *
 * @param motors  Pointer to motor controller for status display
 * @return true on success
 */
bool web_server_init(motor_controller_t* motors);

/**
 * Poll for incoming HTTP requests.
 * Call this periodically in main loop.
 * Uses non-blocking I/O.
 */
void web_server_poll(void);

/**
 * Stop the web server.
 */
void web_server_stop(void);

/**
 * Check if web server is running.
 */
bool web_server_is_running(void);

#endif // WEB_SERVER_H
