"""
Web-based OAuth2 setup server
Provides HTML interface for easy credential entry from any device on network
"""

import socket
import threading
import urllib.parse
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import xbmc
import xbmcaddon


class WebOAuthHandler(BaseHTTPRequestHandler):
    """HTTP request handler for web-based OAuth2 setup."""

    def do_GET(self):
        """Handle GET requests - serve HTML forms."""
        try:
            if self.path == '/' or self.path == '/setup':
                self.serve_setup_form()
            elif self.path == '/status':
                self.serve_status_page()
            elif self.path.startswith('/static/'):
                self.serve_static_file()
            else:
                self.send_404()
        except Exception as e:
            xbmc.log(f"[CloudSync] Web server GET error: {e}", xbmc.LOGERROR)
            self.send_error(500)

    def do_POST(self):
        """Handle POST requests - process form submissions."""
        try:
            if self.path == '/setup':
                self.handle_setup_form()
            elif self.path == '/oauth':
                self.handle_oauth_callback()
            else:
                self.send_404()
        except Exception as e:
            xbmc.log(f"[CloudSync] Web server POST error: {e}", xbmc.LOGERROR)
            self.send_error(500)

    def serve_setup_form(self):
        """Serve the main setup form."""
        html = """
<!DOCTYPE html>
<html>
<head>
    <title>CloudSync - Dropbox OAuth2 Setup</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }
        .container { background: #f5f5f5; padding: 30px; border-radius: 10px; }
        input[type="text"], textarea { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; }
        button { background: #007acc; color: white; padding: 12px 20px; border: none; border-radius: 5px; cursor: pointer; }
        button:hover { background: #005fa3; }
        .step { margin: 20px 0; padding: 15px; background: white; border-radius: 5px; }
        .code-box { background: #f8f8f8; padding: 15px; border-radius: 5px; font-family: monospace; }
        h1 { color: #333; }
        h2 { color: #007acc; }
        .status { padding: 10px; border-radius: 5px; margin: 10px 0; }
        .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .info { background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔗 CloudSync - Dropbox OAuth2 Setup</h1>

        <div class="step">
            <h2>Step 1: Prepare Dropbox App</h2>
            <p>First, add these redirect URIs to your Dropbox app:</p>
            <div class="code-box">
                http://localhost:8765<br>
                http://""" + self.get_server_ip() + """:""" + str(self.server.server_port) + """/oauth<br>
                http://""" + socket.gethostname() + """:""" + str(self.server.server_port) + """/oauth
            </div>
        </div>

        <form method="post" action="/setup">
            <div class="step">
                <h2>Step 2: Enter App Credentials</h2>
                <label>Dropbox App Key:</label>
                <input type="text" name="app_key" placeholder="Enter your Dropbox App Key" required>

                <label>Dropbox App Secret:</label>
                <input type="text" name="app_secret" placeholder="Enter your Dropbox App Secret" required>

                <button type="submit">Start OAuth2 Process</button>
            </div>
        </form>

        <div class="step">
            <h2>Alternative: Manual Token Entry</h2>
            <p>If you already have tokens, enter them below:</p>
            <form method="post" action="/manual">
                <label>Access Token:</label>
                <textarea name="access_token" placeholder="Enter existing access token (optional)"></textarea>

                <label>Refresh Token:</label>
                <textarea name="refresh_token" placeholder="Enter refresh token (optional)"></textarea>

                <button type="submit">Save Manual Tokens</button>
            </form>
        </div>

        <div class="status info">
            <strong>💡 Tip:</strong> You can access this page from any device on your network!<br>
            <strong>🌍 URL:</strong> http://""" + self.get_server_ip() + """:""" + str(self.server.server_port) + """<br>
            <strong>🏠 Local:</strong> http://localhost:""" + str(self.server.server_port) + """
        </div>
    </div>
</body>
</html>
        """

        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def handle_setup_form(self):
        """Handle the setup form submission."""
        content_length = int(self.headers.get('content-length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8')
        form_data = urllib.parse.parse_qs(post_data)

        app_key = form_data.get('app_key', [''])[0]
        app_secret = form_data.get('app_secret', [''])[0]

        if app_key and app_secret:
            # Store credentials temporarily
            self.server.app_key = app_key
            self.server.app_secret = app_secret

            # Generate OAuth URL
            oauth_url = (f"https://www.dropbox.com/oauth2/authorize?"
                        f"client_id={app_key}&"
                        f"response_type=code&"
                        f"token_access_type=offline&"
                        f"redirect_uri=http://{self.get_server_ip()}:{self.server.server_port}/oauth")

            # Send response with OAuth URL
            html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>CloudSync - OAuth Authorization</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }}
        .container {{ background: #f5f5f5; padding: 30px; border-radius: 10px; }}
        .auth-link {{ background: #007acc; color: white; padding: 15px 20px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 20px 0; }}
        .auth-link:hover {{ background: #005fa3; }}
        .status {{ padding: 15px; border-radius: 5px; margin: 20px 0; background: #d1ecf1; color: #0c5460; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>✅ Ready for Authorization!</h1>
        <div class="status">
            <p><strong>Click the button below to authorize CloudSync with Dropbox:</strong></p>
        </div>

        <a href="{oauth_url}" target="_blank" class="auth-link">🔗 Authorize with Dropbox</a>

        <p>After clicking "Allow" in Dropbox, you'll be redirected back here automatically.</p>

        <div style="margin-top: 30px; padding: 15px; background: #fff3cd; color: #856404; border-radius: 5px;">
            <strong>⏳ Waiting for authorization...</strong><br>
            This page will update automatically once you complete the Dropbox authorization.
        </div>

        <script>
            // Auto-refresh to check for completion
            setTimeout(() => {{ window.location.href = '/status'; }}, 5000);
        </script>
    </div>
</body>
</html>
            """

            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
        else:
            self.send_error(400, "Missing app key or secret")

    def handle_oauth_callback(self):
        """Handle OAuth callback with authorization code."""
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if 'code' in params:
            auth_code = params['code'][0]
            xbmc.log(f"[CloudSync] Web OAuth code received: {auth_code[:10]}...", xbmc.LOGINFO)

            # Exchange code for tokens
            try:
                self.exchange_code_for_tokens(auth_code)
            except Exception as e:
                xbmc.log(f"[CloudSync] Token exchange failed: {e}", xbmc.LOGERROR)
                self.send_error_page(f"Token exchange failed: {e}")
                return
        else:
            error = params.get('error', ['unknown'])[0]
            xbmc.log(f"[CloudSync] OAuth error: {error}", xbmc.LOGERROR)
            self.send_error_page(f"OAuth error: {error}")

    def exchange_code_for_tokens(self, auth_code):
        """Exchange authorization code for access and refresh tokens."""
        import urllib.request

        data = {
            'code': auth_code,
            'grant_type': 'authorization_code',
            'client_id': self.server.app_key,
            'client_secret': self.server.app_secret
        }

        encoded_data = urllib.parse.urlencode(data).encode('utf-8')

        req = urllib.request.Request(
            "https://api.dropboxapi.com/oauth2/token",
            data=encoded_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )

        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))

            if 'access_token' in result and 'refresh_token' in result:
                # Save tokens to Kodi settings
                addon = xbmcaddon.Addon('service.cloudsync')
                addon.setSetting('dropbox_app_key', self.server.app_key)
                addon.setSetting('dropbox_app_secret', self.server.app_secret)
                addon.setSetting('dropbox_access_token', result['access_token'])
                addon.setSetting('dropbox_refresh_token', result['refresh_token'])
                addon.setSetting('dropbox_enabled', 'true')

                self.server.setup_complete = True

                html = """
<!DOCTYPE html>
<html>
<head>
    <title>CloudSync - Setup Complete</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; text-align: center; }
        .success { background: #d4edda; color: #155724; padding: 30px; border-radius: 10px; }
        h1 { color: #155724; }
    </style>
</head>
<body>
    <div class="success">
        <h1>🎉 Setup Complete!</h1>
        <p>CloudSync OAuth2 setup was successful!</p>
        <p>You can now close this browser window and return to Kodi.</p>
        <p>The addon will automatically sync your data in the background.</p>
    </div>
</body>
</html>
                """

                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(html.encode('utf-8'))
            else:
                raise Exception("Invalid token response from Dropbox")

    def send_error_page(self, error_message):
        """Send error page."""
        html = f"""
<!DOCTYPE html>
<html>
<head><title>CloudSync - Error</title></head>
<body style="font-family: Arial; text-align: center; margin-top: 100px;">
    <h1 style="color: #dc3545;">❌ Setup Failed</h1>
    <p>{error_message}</p>
    <p><a href="/">← Back to Setup</a></p>
</body>
</html>
        """
        self.send_response(400)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def send_404(self):
        """Send 404 page."""
        self.send_response(404)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"<h1>404 - Page not found</h1><p><a href='/'>Go to setup</a></p>")

    def get_server_ip(self):
        """Get server IP address."""
        try:
            # Get local IP address
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except:
            return "localhost"

    def log_message(self, format, *args):
        """Override to use Kodi logging."""
        xbmc.log(f"[CloudSync] Web Server: {format % args}", xbmc.LOGDEBUG)


class WebOAuthServer:
    """Web server for OAuth2 setup with HTML interface."""

    def __init__(self):
        self.server = None
        self.thread = None
        self.port = None
        self.setup_complete = False

    def find_free_port(self):
        """Find a free port for web server."""
        # Use different ports than OAuth server
        for port in range(8090, 8110):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('', port))  # Bind to all interfaces
                    return port
            except OSError:
                continue
        raise OSError("No free ports available for web server")

    def start_server(self):
        """Start the web server."""
        try:
            self.port = self.find_free_port()
            self.server = HTTPServer(('', self.port), WebOAuthHandler)
            self.server.setup_complete = False
            self.server.app_key = None
            self.server.app_secret = None

            # Start server in background thread
            self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.thread.start()

            xbmc.log(f"[CloudSync] Web OAuth server started on port {self.port}", xbmc.LOGINFO)
            return True

        except Exception as e:
            xbmc.log(f"[CloudSync] Failed to start web server: {e}", xbmc.LOGERROR)
            return False

    def stop_server(self):
        """Stop the web server."""
        if self.server:
            self.server.shutdown()
            self.server = None
            xbmc.log("[CloudSync] Web OAuth server stopped", xbmc.LOGINFO)

    def get_server_url(self):
        """Get the server URL."""
        try:
            # Get local IP address
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                ip = s.getsockname()[0]
            return f"http://{ip}:{self.port}"
        except:
            return f"http://localhost:{self.port}"

    def is_setup_complete(self):
        """Check if setup is complete."""
        return self.server and hasattr(self.server, 'setup_complete') and self.server.setup_complete