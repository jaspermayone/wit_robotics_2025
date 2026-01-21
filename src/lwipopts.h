// =============================================================================
// lwIP Options for Monster Book of Monsters
// Minimal configuration for WiFi AP with HTTP server
// =============================================================================

#ifndef LWIPOPTS_H
#define LWIPOPTS_H

// Common settings for pico_cyw43_arch
#define NO_SYS                      1
#define LWIP_SOCKET                 0
#define LWIP_NETCONN                0

// Memory settings
#define MEM_LIBC_MALLOC             0
#define MEM_ALIGNMENT               4
#define MEM_SIZE                    4096
#define MEMP_NUM_TCP_SEG            32
#define MEMP_NUM_ARP_QUEUE          10
#define PBUF_POOL_SIZE              24
#define LWIP_ARP                    1
#define LWIP_ETHERNET               1
#define LWIP_ICMP                   1
#define LWIP_RAW                    1

// TCP settings
#define LWIP_TCP                    1
#define TCP_WND                     (8 * TCP_MSS)
#define TCP_MSS                     1460
#define TCP_SND_BUF                 (8 * TCP_MSS)
#define TCP_SND_QUEUELEN            ((4 * (TCP_SND_BUF) + (TCP_MSS - 1)) / (TCP_MSS))
#define LWIP_TCP_KEEPALIVE          1

// UDP settings
#define LWIP_UDP                    1

// DHCP server (we're the AP, so we serve DHCP)
#define LWIP_DHCP                   0
#define LWIP_DHCP_SERVER            1

// DNS
#define LWIP_DNS                    0

// IPv4 only
#define LWIP_IPV4                   1
#define LWIP_IPV6                   0

// Callbacks
#define LWIP_CALLBACK_API           1
#define LWIP_NETIF_STATUS_CALLBACK  1
#define LWIP_NETIF_LINK_CALLBACK    1

// Checksum
#define LWIP_CHKSUM_ALGORITHM       3

// Debug (disable for production)
#define LWIP_DEBUG                  0

// Stats (disable for smaller binary)
#define LWIP_STATS                  0
#define LWIP_STATS_DISPLAY          0

// Threading
#define LWIP_TCPIP_CORE_LOCKING     1

// Timeouts
#define MEMP_NUM_SYS_TIMEOUT        (LWIP_NUM_SYS_TIMEOUT_INTERNAL + 4)

#endif // LWIPOPTS_H
