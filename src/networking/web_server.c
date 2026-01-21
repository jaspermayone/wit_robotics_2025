// =============================================================================
// Web Server Implementation
// Simple HTTP server using lwIP for status dashboard
// =============================================================================

#include "web_server.h"
#include "telemetry.h"
#include "wifi_ap.h"
#include <stdio.h>
#include <string.h>
#include "pico/stdlib.h"
#include "lwip/tcp.h"

// State
static struct tcp_pcb* g_server_pcb = NULL;
static motor_controller_t* g_motors = NULL;
static bool g_running = false;

// Buffer for building HTTP responses
#define RESPONSE_BUFFER_SIZE 2048
static char g_response_buffer[RESPONSE_BUFFER_SIZE];

// Forward declarations
static err_t http_accept(void* arg, struct tcp_pcb* newpcb, err_t err);
static err_t http_recv(void* arg, struct tcp_pcb* tpcb, struct pbuf* p, err_t err);
static void http_close(struct tcp_pcb* tpcb);

// =============================================================================
// HTML Generation
// =============================================================================

static int generate_status_page(char* buffer, int max_len) {
    telemetry_data_t* tel = telemetry_get_data();

    int left = 0, right = 0, weapon = 0;
    bool armed = false;
    if (g_motors) {
        motor_controller_get_status(g_motors, &left, &right, &weapon, &armed);
    }

    // Generate HTML
    int len = snprintf(buffer, max_len,
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: text/html\r\n"
        "Connection: close\r\n"
        "Refresh: 2\r\n"  // Auto-refresh every 2 seconds
        "\r\n"
        "<!DOCTYPE html>"
        "<html><head>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<title>%s</title>"
        "<style>"
        "body{font-family:monospace;background:#1a1a2e;color:#eee;padding:20px;}"
        "h1{color:#e94560;}"
        ".box{background:#16213e;padding:15px;margin:10px 0;border-radius:8px;}"
        ".label{color:#888;}"
        ".value{font-size:1.5em;}"
        ".armed{color:#ff4444;font-weight:bold;}"
        ".safe{color:#44ff44;}"
        ".warn{color:#ffaa00;}"
        ".crit{color:#ff0000;}"
        ".bar{background:#333;height:20px;border-radius:4px;overflow:hidden;}"
        ".bar-fill{background:#e94560;height:100%%;}"
        "</style>"
        "</head><body>"
        "<h1>%s</h1>"

        "<div class='box'>"
        "<div class='label'>WEAPON STATUS</div>"
        "<div class='value %s'>%s</div>"
        "</div>"

        "<div class='box'>"
        "<div class='label'>Motors</div>"
        "<div>Left: %+d%% | Right: %+d%% | Weapon: %d%%</div>"
        "</div>"

        "<div class='box'>"
        "<div class='label'>Battery</div>"
        "<div class='value %s'>%.2fV (%d%%)</div>"
        "<div class='bar'><div class='bar-fill' style='width:%d%%;'></div></div>"
        "</div>"

        "<div class='box'>"
        "<div class='label'>CPU Temperature</div>"
        "<div class='value'>%.1f&deg;C</div>"
        "</div>"

        "<div class='box'>"
        "<div class='label'>Uptime</div>"
        "<div>%lu seconds</div>"
        "</div>"

        "<p style='color:#666;'>Auto-refresh every 2 seconds</p>"
        "</body></html>",

        ROBOT_NAME,  // <title>
        ROBOT_NAME,  // <h1>
        armed ? "armed" : "safe",
        armed ? "ARMED" : "SAFE",
        left, right, weapon,
        tel->battery_critical ? "crit" : (tel->battery_low ? "warn" : ""),
        tel->battery_voltage,
        tel->battery_percent,
        tel->battery_percent,
        tel->cpu_temp_c,
        tel->uptime_ms / 1000
    );

    return len;
}

static int generate_404(char* buffer, int max_len) {
    return snprintf(buffer, max_len,
        "HTTP/1.1 404 Not Found\r\n"
        "Content-Type: text/html\r\n"
        "Connection: close\r\n"
        "\r\n"
        "<html><body><h1>404 Not Found</h1></body></html>"
    );
}

// =============================================================================
// TCP Callbacks
// =============================================================================

static err_t http_recv(void* arg, struct tcp_pcb* tpcb, struct pbuf* p, err_t err) {
    if (p == NULL) {
        // Connection closed by client
        http_close(tpcb);
        return ERR_OK;
    }

    // Get request data
    char* request = (char*)p->payload;

    // Parse HTTP request (very basic)
    int response_len = 0;
    if (strncmp(request, "GET / ", 6) == 0 ||
        strncmp(request, "GET /index", 10) == 0) {
        response_len = generate_status_page(g_response_buffer, RESPONSE_BUFFER_SIZE);
    } else {
        response_len = generate_404(g_response_buffer, RESPONSE_BUFFER_SIZE);
    }

    // Send response
    tcp_write(tpcb, g_response_buffer, response_len, TCP_WRITE_FLAG_COPY);
    tcp_output(tpcb);

    // Free the pbuf
    pbuf_free(p);

    // Close connection after response
    http_close(tpcb);

    return ERR_OK;
}

static void http_err(void* arg, err_t err) {
    // Error occurred, connection will be freed automatically
    (void)arg;
    (void)err;
}

static err_t http_accept(void* arg, struct tcp_pcb* newpcb, err_t err) {
    if (err != ERR_OK || newpcb == NULL) {
        return ERR_VAL;
    }

    // Set up callbacks for this connection
    tcp_recv(newpcb, http_recv);
    tcp_err(newpcb, http_err);

    return ERR_OK;
}

static void http_close(struct tcp_pcb* tpcb) {
    tcp_recv(tpcb, NULL);
    tcp_err(tpcb, NULL);
    tcp_close(tpcb);
}

// =============================================================================
// Public API
// =============================================================================

bool web_server_init(motor_controller_t* motors) {
    g_motors = motors;

    printf("Starting web server on port %d...\n", WEB_SERVER_PORT);

    // Create new TCP PCB
    g_server_pcb = tcp_new();
    if (!g_server_pcb) {
        printf("Failed to create TCP PCB\n");
        return false;
    }

    // Bind to port 80
    err_t err = tcp_bind(g_server_pcb, IP_ADDR_ANY, WEB_SERVER_PORT);
    if (err != ERR_OK) {
        printf("Failed to bind to port %d\n", WEB_SERVER_PORT);
        tcp_close(g_server_pcb);
        g_server_pcb = NULL;
        return false;
    }

    // Start listening
    g_server_pcb = tcp_listen(g_server_pcb);
    if (!g_server_pcb) {
        printf("Failed to listen\n");
        return false;
    }

    // Set accept callback
    tcp_accept(g_server_pcb, http_accept);

    g_running = true;
    printf("Web server ready at http://%s/\n", wifi_ap_get_ip());

    return true;
}

void web_server_poll(void) {
    // lwIP handles callbacks, nothing to poll explicitly
    // The threadsafe_background arch handles this
}

void web_server_stop(void) {
    if (g_server_pcb) {
        tcp_close(g_server_pcb);
        g_server_pcb = NULL;
    }
    g_running = false;
    printf("Web server stopped\n");
}

bool web_server_is_running(void) {
    return g_running;
}
