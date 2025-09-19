#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CloudSync V3 - Web Configuration Server
Simple HTTP server for easy MQTT configuration from browser
"""

import json
import socket
import threading
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional

import xbmc
import xbmcaddon


class CloudSyncConfigHandler(BaseHTTPRequestHandler):
    """HTTP request handler for CloudSync web configuration"""

    def do_GET(self):
        """Handle GET requests"""
        try:
            if self.path == '/' or self.path == '/index.html':
                self._serve_config_page()
            elif self.path == '/api/settings':
                self._serve_settings_api()
            elif self.path.startswith('/api/'):
                self._serve_404()
            else:
                self._serve_404()
        except Exception as e:
            self._log(f"Error handling GET {self.path}: {e}")
            self._serve_500()

    def do_POST(self):
        """Handle POST requests"""
        try:
            if self.path == '/api/settings':
                self._handle_settings_update()
            else:
                self._serve_404()
        except Exception as e:
            self._log(f"Error handling POST {self.path}: {e}")
            self._serve_500()

    def _serve_config_page(self):
        """Serve the main configuration HTML page"""
        html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CloudSync V3 Configuration</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; text-align: center; margin-bottom: 30px; }
        .form-group { margin-bottom: 20px; }
        label { display: block; font-weight: bold; margin-bottom: 5px; color: #555; }
        input[type="text"], input[type="password"], select { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box; }
        input[type="checkbox"] { margin-right: 10px; }
        .button { background-color: #007cba; color: white; padding: 12px 24px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; width: 100%; }
        .button:hover { background-color: #005a87; }
        .button:disabled { background-color: #ccc; cursor: not-allowed; }
        .status { margin-top: 20px; padding: 10px; border-radius: 5px; text-align: center; }
        .success { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .error { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .info { background-color: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔧 CloudSync V3 Configuration</h1>
        <form id="configForm">
            <div class="form-group">
                <label for="broker_host">MQTT Broker Host:</label>
                <input type="text" id="broker_host" name="broker_host" placeholder="your-broker.hivemq.cloud" required>
            </div>

            <div class="form-group">
                <label for="broker_port">MQTT Broker Port:</label>
                <input type="text" id="broker_port" name="broker_port" value="8883" required>
            </div>

            <div class="form-group">
                <label for="username">MQTT Username:</label>
                <input type="text" id="username" name="username" required>
            </div>

            <div class="form-group">
                <label for="password">MQTT Password:</label>
                <input type="password" id="password" name="password" required>
            </div>

            <div class="form-group">
                <label>
                    <input type="checkbox" id="use_ssl" name="use_ssl" checked>
                    Use SSL/TLS (recommended)
                </label>
            </div>

            <button type="submit" class="button">💾 Save Configuration</button>
        </form>

        <div id="status"></div>
    </div>

    <script>
        // Load current settings on page load
        window.addEventListener('load', loadSettings);

        async function loadSettings() {
            try {
                const response = await fetch('/api/settings');
                if (response.ok) {
                    const settings = await response.json();
                    document.getElementById('broker_host').value = settings.mqtt_broker_host || '';
                    document.getElementById('broker_port').value = settings.mqtt_broker_port || '8883';
                    document.getElementById('username').value = settings.mqtt_username || '';
                    document.getElementById('password').value = settings.mqtt_password || '';
                    document.getElementById('use_ssl').checked = settings.mqtt_use_ssl !== 'false';
                }
            } catch (error) {
                showStatus('Failed to load current settings', 'error');
            }
        }

        document.getElementById('configForm').addEventListener('submit', async function(e) {
            e.preventDefault();

            const formData = new FormData(e.target);
            const settings = {
                mqtt_broker_host: formData.get('broker_host'),
                mqtt_broker_port: formData.get('broker_port'),
                mqtt_username: formData.get('username'),
                mqtt_password: formData.get('password'),
                mqtt_use_ssl: formData.get('use_ssl') ? 'true' : 'false'
            };

            try {
                const response = await fetch('/api/settings', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(settings)
                });

                if (response.ok) {
                    showStatus('✅ Settings saved successfully! CloudSync will restart to apply changes.', 'success');
                } else {
                    showStatus('❌ Failed to save settings', 'error');
                }
            } catch (error) {
                showStatus('❌ Error saving settings: ' + error.message, 'error');
            }
        });

        function showStatus(message, type) {
            const status = document.getElementById('status');
            status.textContent = message;
            status.className = 'status ' + type;
        }
    </script>
</body>
</html>"""

        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.send_header('Content-Length', len(html.encode('utf-8')))
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def _serve_settings_api(self):
        """Serve current settings as JSON"""
        try:
            addon = xbmcaddon.Addon('service.cloudsync')
            settings = {
                'mqtt_broker_host': addon.getSetting('mqtt_broker_host'),
                'mqtt_broker_port': addon.getSetting('mqtt_broker_port'),
                'mqtt_username': addon.getSetting('mqtt_username'),
                'mqtt_password': addon.getSetting('mqtt_password'),
                'mqtt_use_ssl': addon.getSetting('mqtt_use_ssl')
            }

            response = json.dumps(settings)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Content-Length', len(response.encode('utf-8')))
            self.end_headers()
            self.wfile.write(response.encode('utf-8'))

        except Exception as e:
            self._log(f"Error serving settings API: {e}")
            self._serve_500()

    def _handle_settings_update(self):
        """Handle settings update from POST request"""
        try:
            # Read POST data
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            settings = json.loads(post_data.decode('utf-8'))

            # Update addon settings
            addon = xbmcaddon.Addon('service.cloudsync')
            for key, value in settings.items():
                if key.startswith('mqtt_'):
                    addon.setSetting(key, str(value))
                    self._log(f"Updated setting {key} = {value}")

            # Send success response
            response = json.dumps({'status': 'success', 'message': 'Settings updated'})
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Content-Length', len(response.encode('utf-8')))
            self.end_headers()
            self.wfile.write(response.encode('utf-8'))

            self._log("MQTT settings updated via web interface")

        except Exception as e:
            self._log(f"Error updating settings: {e}")
            self._serve_500()

    def _serve_404(self):
        """Serve 404 Not Found"""
        self.send_response(404)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'<h1>404 - Not Found</h1>')

    def _serve_500(self):
        """Serve 500 Internal Server Error"""
        self.send_response(500)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'<h1>500 - Internal Server Error</h1>')

    def _log(self, message: str):
        """Log message"""
        xbmc.log(f"CloudSync V3 WebConfig: {message}", xbmc.LOGINFO)

    def log_message(self, format, *args):
        """Override default log message to use Kodi logging"""
        self._log(f"HTTP {format % args}")


class CloudSyncWebConfig:
    """Web configuration server for CloudSync"""

    def __init__(self):
        self.server: Optional[HTTPServer] = None
        self.server_thread: Optional[threading.Thread] = None
        self.running = False

    def _log(self, message: str):
        """Log message"""
        xbmc.log(f"CloudSync V3 WebConfig: {message}", xbmc.LOGINFO)

    def start(self, port: int = 8090) -> bool:
        """Start the web configuration server"""
        if self.running:
            self._log("Web config server already running")
            return True

        try:
            # Create HTTP server
            self.server = HTTPServer(('', port), CloudSyncConfigHandler)

            # Start server in background thread
            self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.server_thread.start()

            self.running = True

            # Get local IP for user info
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)

            self._log(f"Web configuration server started on http://{local_ip}:{port}")
            self._log(f"Access configuration page at: http://{local_ip}:{port}")

            return True

        except Exception as e:
            self._log(f"Failed to start web config server: {e}")
            return False

    def stop(self):
        """Stop the web configuration server"""
        if not self.running:
            return

        try:
            if self.server:
                self.server.shutdown()
                self.server.server_close()

            if self.server_thread:
                self.server_thread.join(timeout=2)

            self.running = False
            self._log("Web configuration server stopped")

        except Exception as e:
            self._log(f"Error stopping web config server: {e}")

    def is_running(self) -> bool:
        """Check if server is running"""
        return self.running