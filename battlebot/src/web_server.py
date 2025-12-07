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
                print(f"Request from {client_ip} (MAC: {client_mac}) - {'ALLOWED' if allowed else 'BLOCKED'}")
                if not allowed:
                    response = self._page_blocked(client_ip, client_mac)
                    conn.send(response.encode())
                    conn.close()
                    return

                # Route request
                response = self._route_request(method, path, client_ip, request)

                # Send response
                if response:
                    # Send in chunks for large responses
                    data = response.encode()
                    print(f"Sending {len(data)} bytes for {path}")
                    chunk_size = 1024
                    for i in range(0, len(data), chunk_size):
                        conn.send(data[i:i+chunk_size])
                else:
                    print(f"Warning: No response generated for {path}")

            except Exception as e:
                if DEBUG_MODE:
                    import sys
                    print(f"Request handling error: {e}")
                    sys.print_exception(e)
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

        try:
            motor_status = self.motor_controller.get_status()
            telemetry = self.telemetry.get_summary()
        except Exception as e:
            print(f"Error getting status: {e}")
            return self._response_error("Status error")

        # Pre-compute conditional values to avoid complex f-string expressions
        status_class = 'good' if motor_status['failsafe_ok'] else 'critical'
        failsafe_text = 'OK' if motor_status['failsafe_ok'] else 'TRIGGERED'
        weapon_text = 'ARMED' if motor_status['armed'] else 'DISARMED'
        device_count = len(self.wifi_ap.connected_clients)

        # Build connected devices HTML
        devices_html = ""
        for mac, info in self.wifi_ap.connected_clients.items():
            session_active = info['ip'] in self.sessions if info['ip'] else False
            ip_text = info['ip'] if info['ip'] else '--'
            rssi_text = str(info.get('rssi', '--'))
            badge_class = 'badge active' if session_active else 'badge'
            status_text = 'ACTIVE' if session_active else 'IDLE'
            devices_html += f"""
                <tr>
                    <td style="font-size:0.85em">{mac}</td>
                    <td>{ip_text}</td>
                    <td><span class="{badge_class}">{status_text}</span></td>
                    <td>{rssi_text} dBm</td>
                </tr>
            """

        if not devices_html:
            devices_html = '<tr><td colspan="4" style="text-align:center;color:#606070">NO DEVICES</td></tr>'

        html = f"""HTTP/1.1 200 OK
Content-Type: text/html
Connection: close

<!DOCTYPE html><html><head><title>BATTLEBOT</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:monospace;background:#0a0a0f;color:#e0e0e0;padding:15px}}
.c{{max-width:800px;margin:0 auto}}
h1{{color:#0ff;font-size:1.2em;letter-spacing:3px;padding:10px;border:1px solid #333;margin-bottom:15px;text-shadow:0 0 10px #0ff4}}
.dot{{display:inline-block;width:8px;height:8px;background:#0f6;border-radius:50%;margin-right:8px;box-shadow:0 0 8px #0f6}}
.dot.err{{background:#f22;box-shadow:0 0 8px #f22}}
.g{{display:grid;grid-template-columns:1fr 1fr;gap:10px}}
.p{{background:#12121a;border:1px solid #333;margin-bottom:10px}}
.p.w{{grid-column:span 2}}
.ph{{background:#0ff2;padding:6px 12px;font-size:.7em;letter-spacing:2px;color:#0ff;border-bottom:1px solid #333}}
.pb{{padding:12px}}
.r{{display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #fff1}}
.l{{color:#666;font-size:.75em}}
.v{{color:#0ff;font-weight:bold}}
.v.ok{{color:#0f6}}
.v.w{{color:#f60}}
.v.cr{{color:#f22}}
.mg{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;text-align:center}}
.mv{{font-size:1.8em;color:#0ff}}
.ml{{font-size:.6em;color:#666;letter-spacing:1px}}
.bar{{height:4px;background:#333;margin-top:4px}}
.bf{{height:100%;background:linear-gradient(90deg,#0ff,#0f6);transition:width .2s}}
table{{width:100%;font-size:.75em}}
th{{text-align:left;color:#666;padding:6px;border-bottom:1px solid #333}}
td{{padding:6px}}
.badge{{padding:2px 6px;font-size:.7em;background:#0ff2;color:#0ff;border:1px solid #0ff}}
.badge.on{{background:#0f62;color:#0f6;border-color:#0f6}}
a{{color:#0ff}}
@media(max-width:600px){{.g{{grid-template-columns:1fr}}.p.w{{grid-column:span 1}}.mg{{grid-template-columns:1fr}}}}
</style></head>
<body><div class="c">
<h1><span class="dot" id="dot"></span>BATTLEBOT <span id="st" style="float:right;font-size:.6em">LIVE</span></h1>
<div class="g">
<div class="p" id="sp"><div class="ph">SYSTEM</div><div class="pb">
<div class="r"><span class="l">FAILSAFE</span><span class="v ok" id="fs">{failsafe_text}</span></div>
<div class="r"><span class="l">WEAPON</span><span class="v" id="wp">{weapon_text}</span></div>
</div></div>
<div class="p"><div class="ph">TELEMETRY</div><div class="pb">
<div class="r"><span class="l">BATTERY</span><span class="v" id="bat">{telemetry['Battery']}</span></div>
<div class="r"><span class="l">CPU</span><span class="v" id="cpu">{telemetry['CPU Temp']}</span></div>
<div class="r"><span class="l">UPTIME</span><span class="v" id="up">{telemetry['Uptime']}</span></div>
</div></div>
<div class="p w"><div class="ph">MOTORS</div><div class="pb"><div class="mg">
<div><div class="mv" id="ml">{motor_status['left']}</div><div class="ml">LEFT</div><div class="bar"><div class="bf" id="bl" style="width:{abs(motor_status['left'])}%"></div></div></div>
<div><div class="mv" id="mr">{motor_status['right']}</div><div class="ml">RIGHT</div><div class="bar"><div class="bf" id="br" style="width:{abs(motor_status['right'])}%"></div></div></div>
<div><div class="mv" id="mw">{motor_status['weapon']}</div><div class="ml">WEAPON</div><div class="bar"><div class="bf" id="bw" style="width:{motor_status['weapon']}%"></div></div></div>
</div></div></div>
<div class="p w"><div class="ph">NETWORK [{device_count}]</div><div class="pb">
<table><tr><th>MAC</th><th>IP</th><th>STATUS</th></tr>{devices_html}</table>
</div></div>
</div>
<p style="text-align:center;margin-top:15px"><a href="/logout">[LOGOUT]</a></p>
</div>
<script>
function u(){{fetch('/api/status').then(r=>r.json()).then(d=>{{
document.getElementById('dot').className='dot';
document.getElementById('st').textContent='LIVE';
document.getElementById('ml').textContent=d.motors.left;
document.getElementById('mr').textContent=d.motors.right;
document.getElementById('mw').textContent=d.motors.weapon;
document.getElementById('bl').style.width=Math.abs(d.motors.left)+'%';
document.getElementById('br').style.width=Math.abs(d.motors.right)+'%';
document.getElementById('bw').style.width=d.motors.weapon+'%';
var fs=document.getElementById('fs');
fs.textContent=d.motors.failsafe_ok?'OK':'FAIL';
fs.className=d.motors.failsafe_ok?'v ok':'v cr';
var wp=document.getElementById('wp');
wp.textContent=d.motors.armed?'ARMED':'SAFE';
wp.className=d.motors.armed?'v w':'v';
if(d.telemetry){{var t=d.telemetry;
document.getElementById('bat').textContent=t.battery_voltage.toFixed(2)+'V';
document.getElementById('cpu').textContent=t.cpu_temp.toFixed(1)+'C';
document.getElementById('up').textContent=(t.uptime_ms/1000).toFixed(0)+'s';
}}}}).catch(e=>{{
document.getElementById('dot').className='dot err';
document.getElementById('st').textContent='OFFLINE';
}});}}
setInterval(u,500);
</script></body></html>"""

        return html

    def _page_login(self, error=""):
        """Login page"""
        err = '<p style="color:#f22;margin-top:10px;text-align:center">' + error + '</p>' if error else ''
        html = f"""HTTP/1.1 200 OK
Content-Type: text/html
Connection: close

<!DOCTYPE html><html><head><title>BATTLEBOT</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:monospace;background:#0a0a0f;color:#e0e0e0;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}}
.box{{background:#12121a;border:1px solid #333;padding:30px;width:100%;max-width:320px;text-align:center}}
h1{{color:#0ff;font-size:1.2em;letter-spacing:3px;margin-bottom:5px;text-shadow:0 0 10px #0ff4}}
.sub{{color:#666;font-size:.7em;letter-spacing:2px;margin-bottom:20px}}
input{{width:100%;padding:12px;background:#0a0a0f;border:1px solid #333;color:#0ff;font-family:monospace;margin-bottom:15px}}
input:focus{{border-color:#0ff;outline:none;box-shadow:0 0 10px #0ff4}}
button{{width:100%;padding:12px;background:transparent;border:1px solid #0ff;color:#0ff;font-family:monospace;cursor:pointer;letter-spacing:2px}}
button:hover{{background:#0ff;color:#0a0a0f}}
</style></head>
<body><div class="box">
<h1>BATTLEBOT</h1>
<p class="sub">AUTHENTICATION REQUIRED</p>
<form method="POST" action="/login">
<input type="password" name="password" placeholder="Access code" autofocus>
<button type="submit">[AUTHENTICATE]</button>
{err}</form></div></body></html>"""
        return html

    def _page_blocked(self, ip, mac):
        """Access denied page for blocked MACs"""
        html = f"""HTTP/1.1 403 Forbidden
Content-Type: text/html
Connection: close

<!DOCTYPE html><html><head><title>DENIED</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:monospace;background:#0a0a0f;color:#e0e0e0;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}}
.box{{background:#12121a;border:2px solid #f22;padding:30px;width:100%;max-width:350px;text-align:center}}
h1{{color:#f22;font-size:1.1em;letter-spacing:4px;margin-bottom:15px}}
p{{color:#666;font-size:.8em;margin-bottom:20px}}
.r{{display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #222;font-size:.8em}}
.l{{color:#666}}.v{{color:#f22}}
</style></head>
<body><div class="box">
<h1>ACCESS DENIED</h1>
<p>DEVICE NOT AUTHORIZED</p>
<div class="r"><span class="l">MAC</span><span class="v">{mac}</span></div>
<div class="r"><span class="l">IP</span><span class="v">{ip}</span></div>
</div></body></html>"""
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

    def _response_error(self, msg):
        """Simple error response"""
        return f"""HTTP/1.1 500 Error
Content-Type: text/html
Connection: close

<html><body><h1>Error: {msg}</h1></body></html>"""