# web_server.py - Web Interface for Monitoring

import socket
import time
from config import *

class WebServer:
    """
    Web-based monitoring interface for battlebot.
    Authentication and connection tracking only - no control features.
    """

    def __init__(self, wifi_ap, motor_controller, telemetry_collector):
        self.wifi_ap = wifi_ap
        self.motor_controller = motor_controller
        self.telemetry = telemetry_collector

        # Session management
        self.sessions = {}  # {ip: {'token': str, 'time': int, 'authenticated': bool, 'mac': str}}

        # Web server socket
        self.server_socket = None

    def start_server(self, port=80):
        """Start the web server"""
        addr = socket.getaddrinfo('0.0.0.0', port)[0][-1]

        self.server_socket = socket.socket()
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(addr)
        self.server_socket.listen(5)
        self.server_socket.setblocking(False)  # Non-blocking

        print(f"Web server listening on port {port}")

    def handle_requests(self):
        """
        Non-blocking request handler.
        Call this frequently in main loop.
        """
        if not self.server_socket:
            return

        # Periodically update connected devices
        self.wifi_ap.update_connected_devices()

        try:
            conn, addr = self.server_socket.accept()
            conn.settimeout(2.0)

            try:
                request = conn.recv(1024).decode()

                # Parse request
                lines = request.split('\r\n')
                if not lines:
                    conn.close()
                    return

                method, path, _ = lines[0].split(' ')
                client_ip = addr[0]

                # Update IP for connected device
                self.wifi_ap.update_client_ip(client_ip)

                # Check MAC whitelist
                allowed, client_mac = self.wifi_ap.check_mac_whitelist(client_ip)
                if not allowed:
                    response = self._page_blocked(client_ip, client_mac)
                    conn.send(response.encode())
                    conn.close()
                    return

                # Route request
                response = self._route_request(method, path, client_ip, request)

                # Send response
                conn.send(response.encode())

            except Exception as e:
                if DEBUG_MODE:
                    print(f"Request handling error: {e}")
            finally:
                conn.close()

        except OSError:
            pass  # No pending connections (non-blocking)

    def _route_request(self, method, path, client_ip, full_request):
        """Route incoming request to appropriate handler"""

        # Check authentication for protected routes
        authenticated = self._check_auth(client_ip, full_request)

        # Public routes
        if path == '/' or path == '/index.html':
            return self._page_index(authenticated)

        elif path == '/login' and method == 'POST':
            return self._handle_login(client_ip, full_request)

        # Protected routes
        elif not authenticated:
            return self._response_redirect('/login')

        elif path == '/api/status':
            return self._api_status()

        elif path == '/api/devices':
            return self._api_devices()

        elif path == '/logout':
            self._logout(client_ip)
            return self._response_redirect('/')

        else:
            return self._response_404()

    def _check_auth(self, client_ip, request):
        """Check if client is authenticated"""
        # Simple session check
        if client_ip in self.sessions:
            session = self.sessions[client_ip]
            # Check if session is still valid
            if time.time() - session['time'] < SESSION_TIMEOUT:
                return session['authenticated']

        return False

    def _handle_login(self, client_ip, request):
        """Handle login POST request"""
        # Extract password from POST body
        lines = request.split('\r\n')
        body = lines[-1]

        # Simple form parsing (password=xxx)
        if 'password=' in body:
            password = body.split('password=')[1].split('&')[0]

            if password == ADMIN_PASSWORD:
                # Get MAC address for this IP
                client_mac = None
                for mac, info in self.wifi_ap.connected_clients.items():
                    if info['ip'] == client_ip:
                        client_mac = mac
                        break

                # Create session
                self.sessions[client_ip] = {
                    'authenticated': True,
                    'time': time.time(),
                    'token': str(time.time()),
                    'mac': client_mac
                }

                print(f"✓ Login: {client_ip} ({client_mac})")
                return self._response_redirect('/')

        # Failed login
        return self._page_login(error="Invalid password")

    def _logout(self, client_ip):
        """Logout user"""
        if client_ip in self.sessions:
            print(f"✓ Logout: {client_ip}")
            del self.sessions[client_ip]

    def _page_index(self, authenticated):
        """Main dashboard page - monitoring only"""
        if not authenticated:
            return self._page_login()

        motor_status = self.motor_controller.get_status()
        telemetry = self.telemetry.get_summary()

        # Build connected devices HTML
        devices_html = ""
        for mac, info in self.wifi_ap.connected_clients.items():
            session_active = info['ip'] in self.sessions if info['ip'] else False
            uptime = int(time.time() - info['connected_time'])
            devices_html += f"""
                <tr>
                    <td>{mac}</td>
                    <td>{info['ip'] or 'N/A'}</td>
                    <td>{'🟢 Active' if session_active else '⚪ Connected'}</td>
                    <td>{uptime}s</td>
                    <td>{info.get('rssi', 'N/A')} dBm</td>
                </tr>
            """

        html = f"""HTTP/1.1 200 OK
Content-Type: text/html
Connection: close

<!DOCTYPE html>
<html>
<head>
    <title>BattleBot Monitor</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta http-equiv="refresh" content="2">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #1a1a1a; color: #fff; }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        .status-box {{ background: #2a2a2a; padding: 15px; margin: 10px 0; border-radius: 5px; }}
        .critical {{ background: #ff4444; }}
        .warning {{ background: #ffaa00; }}
        .good {{ background: #44ff44; color: #000; }}
        h1 {{ color: #00ffff; }}
        h2 {{ color: #00ffff; font-size: 1.2em; margin-top: 0; }}
        .telemetry {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
        th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #444; }}
        th {{ color: #00ffff; }}
        .monitor-only {{ background: #ffaa00; color: #000; padding: 10px; border-radius: 5px; text-align: center; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 BattleBot Monitor</h1>

        <div class="monitor-only">
            📊 MONITORING ONLY - No control features available via web interface
        </div>

        <div class="status-box {'good' if motor_status['failsafe_ok'] else 'critical'}">
            <h2>System Status</h2>
            <p><strong>Failsafe:</strong> {'✓ OK' if motor_status['failsafe_ok'] else '✗ TRIGGERED'}</p>
            <p><strong>Weapon:</strong> {'🔴 ARMED' if motor_status['armed'] else '⚪ DISARMED'}</p>
        </div>

        <div class="status-box">
            <h2>Telemetry</h2>
            <div class="telemetry">
                <p><strong>Battery:</strong> {telemetry['Battery']}</p>
                <p><strong>CPU Temp:</strong> {telemetry['CPU Temp']}</p>
                <p><strong>Uptime:</strong> {telemetry['Uptime']}</p>
                <p><strong>Loop Time:</strong> {telemetry['Loop Time']}</p>
            </div>
        </div>

        <div class="status-box">
            <h2>Motor Status</h2>
            <p><strong>Left:</strong> {motor_status['left']}%</p>
            <p><strong>Right:</strong> {motor_status['right']}%</p>
            <p><strong>Weapon:</strong> {motor_status['weapon']}%</p>
        </div>

        <div class="status-box">
            <h2>Connected Devices ({len(self.wifi_ap.connected_clients)})</h2>
            <table>
                <tr>
                    <th>MAC Address</th>
                    <th>IP</th>
                    <th>Status</th>
                    <th>Uptime</th>
                    <th>Signal</th>
                </tr>
                {devices_html if devices_html else '<tr><td colspan="5">No devices connected</td></tr>'}
            </table>
        </div>

        <p><a href="/logout" style="color: #00ffff;">Logout</a></p>
    </div>
</body>
</html>"""

        return html

    def _page_login(self, error=""):
        """Login page"""
        html = f"""HTTP/1.1 200 OK
Content-Type: text/html
Connection: close

<!DOCTYPE html>
<html>
<head>
    <title>BattleBot Login</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px;
               background: #1a1a1a; color: #fff; display: flex;
               justify-content: center; align-items: center; min-height: 100vh; }}
        .login-box {{ background: #2a2a2a; padding: 30px; border-radius: 10px;
                     box-shadow: 0 0 20px rgba(0,255,255,0.3); }}
        h1 {{ color: #00ffff; margin-top: 0; }}
        input {{ padding: 10px; font-size: 16px; width: 100%; margin: 10px 0; }}
        button {{ padding: 15px; font-size: 16px; width: 100%;
                 background: #00ffff; border: none; cursor: pointer; }}
        .error {{ color: #ff4444; }}
    </style>
</head>
<body>
    <div class="login-box">
        <h1>🤖 BattleBot Monitor</h1>
        <form method="POST" action="/login">
            <input type="password" name="password" placeholder="Enter password" autofocus>
            <button type="submit">Login</button>
            {f'<p class="error">{error}</p>' if error else ''}
        </form>
    </div>
</body>
</html>"""

        return html

    def _page_blocked(self, ip, mac):
        """Access denied page for blocked MACs"""
        html = f"""HTTP/1.1 403 Forbidden
Content-Type: text/html
Connection: close

<!DOCTYPE html>
<html>
<head>
    <title>Access Denied</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px;
               background: #1a1a1a; color: #fff; display: flex;
               justify-content: center; align-items: center; min-height: 100vh; }}
        .error-box {{ background: #ff4444; padding: 30px; border-radius: 10px;
                     box-shadow: 0 0 20px rgba(255,0,0,0.5); }}
        h1 {{ margin-top: 0; }}
        code {{ background: #000; padding: 5px; border-radius: 3px; }}
    </style>
</head>
<body>
    <div class="error-box">
        <h1>🚫 Access Denied</h1>
        <p>Your device is not authorized to access this BattleBot.</p>
        <p>MAC: <code>{mac}</code></p>
        <p>IP: <code>{ip}</code></p>
    </div>
</body>
</html>"""

        return html

    def _api_status(self):
        """API endpoint for status JSON"""
        motor_status = self.motor_controller.get_status()
        telemetry = self.telemetry.last_telemetry

        data = {
            'motors': motor_status,
            'telemetry': telemetry,
            'timestamp': time.time()
        }

        return self._response_json(data)

    def _api_devices(self):
        """API endpoint for connected devices"""
        devices = []
        for mac, info in self.wifi_ap.connected_clients.items():
            devices.append({
                'mac': mac,
                'ip': info['ip'],
                'connected_time': info['connected_time'],
                'last_seen': info['last_seen'],
                'rssi': info.get('rssi'),
                'authenticated': info['ip'] in self.sessions if info['ip'] else False
            })

        return self._response_json({
            'devices': devices,
            'total': len(devices),
            'blocked_attempts': len(self.wifi_ap.blocked_attempts)
        })

    def _response_json(self, data):
        """JSON response"""
        import json
        return f"""HTTP/1.1 200 OK
Content-Type: application/json
Connection: close

{json.dumps(data)}"""

    def _response_redirect(self, location):
        """Redirect response"""
        return f"""HTTP/1.1 302 Found
Location: {location}
Connection: close

"""

    def _response_404(self):
        """404 Not Found"""
        return """HTTP/1.1 404 Not Found
Content-Type: text/html
Connection: close

<html><body><h1>404 Not Found</h1></body></html>"""