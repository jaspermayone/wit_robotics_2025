# wifi_ap.py - WiFi Access Point Manager

import network
import time
from config import *

class WiFiAccessPoint:
    """Manages WiFi access point and connection tracking."""

    def __init__(self):
        # Connection tracking
        self.connected_clients = {}  # {mac: {'ip': str, 'connected_time': int, 'last_seen': int, 'rssi': int}}

        # Initialize access point
        self.ap = self._init_access_point()

    def _init_access_point(self):
        """Initialize WiFi access point"""
        ap = network.WLAN(network.AP_IF)
        ap.active(True)

        # Configure AP
        ap.config(essid=AP_SSID)
        ap.config(password=AP_PASSWORD)
        ap.config(channel=AP_CHANNEL)

        # Wait for AP to become active
        while not ap.active():
            time.sleep(0.1)

        print(f"\n{'='*40}")
        print(f"AP '{AP_SSID}' active")
        print(f"http://{ap.ifconfig()[0]}")
        print(f"{'='*40}\n")

        return ap

    def _bytes_to_mac(self, data):
        """Convert various byte formats to MAC address string"""
        parts = []
        for b in data:
            if isinstance(b, int):
                parts.append('%02x' % b)
            elif isinstance(b, bytes):
                parts.append('%02x' % b[0])
            else:
                parts.append('%02x' % int(b))
        return ':'.join(parts)

    def update_connected_devices(self):
        """Update the list of connected devices from AP"""
        try:
            stations = self.ap.status('stations')

            # Check if stations is valid (Pico W might not support this or return None/empty)
            if not stations:
                return

            # If stations is a single bytes object (raw response), we can't parse it
            if isinstance(stations, (bytes, bytearray)):
                if DEBUG_MODE:
                    print(f"  Warning: stations returned as bytes: {stations}")
                return

            if not hasattr(stations, '__iter__'):
                return

            current_time = time.time()

            current_macs = set()

            for station in stations:
                try:
                    # Handle different formats: (mac_bytes, rssi) or just mac_bytes
                    if isinstance(station, tuple) and len(station) >= 2:
                        mac_bytes, rssi = station[0], station[1]
                        # Convert rssi from bytes if needed
                        if isinstance(rssi, bytes):
                            rssi = int.from_bytes(rssi, 'little', signed=True) if rssi else None
                    else:
                        mac_bytes = station
                        rssi = None

                    mac = self._bytes_to_mac(mac_bytes)
                    current_macs.add(mac)
                except Exception as parse_err:
                    if DEBUG_MODE:
                        print(f"  Skipping station, parse error: {parse_err}, data: {station}")
                    continue

                # Add or update device
                if mac not in self.connected_clients:
                    self.connected_clients[mac] = {
                        'ip': None,
                        'connected_time': current_time,
                        'last_seen': current_time,
                        'rssi': rssi
                    }
                else:
                    self.connected_clients[mac]['last_seen'] = current_time
                    if rssi is not None:
                        self.connected_clients[mac]['rssi'] = rssi

            # Remove devices that are no longer connected (not seen for 30 seconds)
            macs_to_remove = []
            for mac in self.connected_clients:
                if mac not in current_macs and (current_time - self.connected_clients[mac]['last_seen'] > 30):
                    macs_to_remove.append(mac)

            for mac in macs_to_remove:
                del self.connected_clients[mac]

        except Exception as e:
            pass  # Station tracking not supported on this device

    def update_client_ip(self, client_ip):
        """Update IP address for a connected device, or add if not tracked"""
        current_time = time.time()

        # Check if we already have this IP
        for mac, info in self.connected_clients.items():
            if info['ip'] == client_ip:
                info['last_seen'] = current_time
                return

        # If no station tracking available, add client by IP
        # Use IP as a pseudo-MAC since we can't get real MAC
        if client_ip not in [info['ip'] for info in self.connected_clients.values()]:
            pseudo_mac = f"ip:{client_ip}"
            self.connected_clients[pseudo_mac] = {
                'ip': client_ip,
                'connected_time': current_time,
                'last_seen': current_time,
                'rssi': None
            }
            if DEBUG_MODE:
                print(f"Client tracked: {client_ip}")

    def get_connected_devices(self):
        """Get list of connected devices"""
        self.update_connected_devices()
        return list(self.connected_clients.values())

    def get_device_count(self):
        """Get count of connected devices"""
        return len(self.connected_clients)

    def get_ip_address(self):
        """Get the AP's IP address"""
        return self.ap.ifconfig()[0]