"""
Simple Web Setup for Dropbox OAuth2
Just a web form to paste the authorization code - much simpler!
"""

import socket
import threading
import urllib.parse
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import xbmc
import xbmcaddon


class SimpleSetupHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler for OAuth2 code entry."""

    def do_GET(self):
        """Serve the setup form."""
        if self.path == '/' or self.path == '/setup':
            self.serve_form()
        else:
            self.send_404()

    def do_POST(self):
        """Handle form submission."""
        if self.path == '/complete':
            self.handle_completion()
        else:
            self.send_404()

    def serve_form(self):
        """Serve simple setup form."""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>CloudSync - Simple Setup</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
               max-width: 700px; margin: 30px auto; padding: 20px; background: #f8f9fa; }}
        .container {{ background: white; padding: 40px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #2563eb; text-align: center; margin-bottom: 30px; }}
        .step {{ margin: 25px 0; padding: 20px; background: #f1f5f9; border-radius: 8px; border-left: 4px solid #2563eb; }}
        .step h3 {{ margin-top: 0; color: #1e40af; }}
        .url-box {{ background: #1f2937; color: #10b981; padding: 15px; border-radius: 6px;
                    font-family: monospace; word-break: break-all; font-size: 14px; }}
        input, textarea {{ width: 100%; padding: 12px; margin: 10px 0; border: 2px solid #d1d5db;
                          border-radius: 6px; font-size: 16px; box-sizing: border-box; }}
        input:focus, textarea:focus {{ outline: none; border-color: #2563eb; }}
        button {{ background: #2563eb; color: white; padding: 15px 30px; border: none;
                 border-radius: 6px; font-size: 16px; cursor: pointer; width: 100%; margin-top: 15px; }}
        button:hover {{ background: #1d4ed8; }}
        .info {{ background: #dbeafe; color: #1e40af; padding: 15px; border-radius: 6px; margin: 20px 0; }}
        .warning {{ background: #fef3c7; color: #92400e; padding: 15px; border-radius: 6px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔗 CloudSync Setup</h1>

        <div class="step">
            <h3>Step 1: Get App Credentials</h3>
            <p>Go to <strong>Dropbox App Console</strong> and get your App Key and Secret.</p>
        </div>

        <div class="step">
            <h3>Step 2: Generate Authorization URL</h3>
            <form style="display: inline;">
                <label><strong>App Key:</strong></label>
                <input type="text" id="app_key" placeholder="Enter your Dropbox App Key" required>

                <label><strong>App Secret:</strong></label>
                <input type="text" id="app_secret" placeholder="Enter your Dropbox App Secret" required>

                <button type="button" onclick="generateURL()">Generate Authorization URL</button>
            </form>
        </div>

        <div id="url_step" style="display: none;" class="step">
            <h3>Step 3: Authorize in Browser</h3>
            <p>Click the link below to authorize CloudSync:</p>
            <div class="url-box" id="auth_url_display"></div>
            <button type="button" onclick="openURL()">Open Authorization URL</button>
        </div>

        <div class="step">
            <h3>Step 4: Paste Authorization Code</h3>
            <form method="post" action="/complete">
                <input type="hidden" id="final_app_key" name="app_key">
                <input type="hidden" id="final_app_secret" name="app_secret">

                <label><strong>Authorization Code:</strong></label>
                <textarea name="auth_code" rows="3" placeholder="Paste the long authorization code from Dropbox here..." required></textarea>

                <button type="submit">Complete Setup</button>
            </form>
        </div>

        <div class="info">
            <strong>💡 Pro tip:</strong> You can access this page from any device on your network!<br>
            <strong>URL:</strong> http://{self.get_server_ip()}:{self.server.server_port}
        </div>
    </div>

    <script>
        let authURL = '';

        function generateURL() {{
            const appKey = document.getElementById('app_key').value;
            const appSecret = document.getElementById('app_secret').value;

            if (!appKey || !appSecret) {{
                alert('Please enter both App Key and App Secret');
                return;
            }}

            // Generate OAuth URL without redirect_uri
            authURL = `https://www.dropbox.com/oauth2/authorize?client_id=${{appKey}}&response_type=code&token_access_type=offline`;

            // Show the URL step
            document.getElementById('url_step').style.display = 'block';
            document.getElementById('auth_url_display').textContent = authURL;

            // Store credentials for later use
            document.getElementById('final_app_key').value = appKey;
            document.getElementById('final_app_secret').value = appSecret;
        }}

        function openURL() {{
            if (authURL) {{
                window.open(authURL, '_blank');
            }}
        }}
    </script>
</body>
</html>
        """

        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def handle_completion(self):
        """Handle setup completion."""
        content_length = int(self.headers.get('content-length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8')
        form_data = urllib.parse.parse_qs(post_data)

        app_key = form_data.get('app_key', [''])[0]
        app_secret = form_data.get('app_secret', [''])[0]
        auth_code = form_data.get('auth_code', [''])[0].strip()

        if not (app_key and app_secret and auth_code):
            self.send_error_page("Missing required information")
            return

        try:
            # Exchange code for tokens
            self.exchange_tokens(app_key, app_secret, auth_code)
        except Exception as e:
            self.send_error_page(f"Setup failed: {str(e)}")

    def exchange_tokens(self, app_key, app_secret, auth_code):
        """Exchange authorization code for tokens."""
        import urllib.request

        data = {
            'code': auth_code,
            'grant_type': 'authorization_code',
            'client_id': app_key,
            'client_secret': app_secret
        }

        encoded_data = urllib.parse.urlencode(data).encode('utf-8')

        req = urllib.request.Request(
            "https://api.dropboxapi.com/oauth2/token",
            data=encoded_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )

        with urllib.request.urlopen(req, timeout=15) as response:
            result = json.loads(response.read().decode('utf-8'))

            if 'access_token' in result:
                # Save to Kodi settings
                addon = xbmcaddon.Addon('service.cloudsync')
                addon.setSetting('dropbox_app_key', app_key)
                addon.setSetting('dropbox_app_secret', app_secret)
                addon.setSetting('dropbox_access_token', result['access_token'])

                if 'refresh_token' in result:
                    addon.setSetting('dropbox_refresh_token', result['refresh_token'])

                addon.setSetting('dropbox_enabled', 'true')

                # Mark as complete
                self.server.setup_complete = True

                xbmc.log("[CloudSync] Web setup completed successfully - flag set to True", xbmc.LOGINFO)

                # Send success page
                html = """
<!DOCTYPE html>
<html>
<head>
    <title>Setup Complete</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; text-align: center; margin: 50px; background: #f0f8ff; }
        .success { background: #d4edda; color: #155724; padding: 40px; border-radius: 10px;
                  max-width: 500px; margin: 50px auto; border: 2px solid #c3e6cb; }
        h1 { color: #155724; margin-bottom: 20px; }
        p { font-size: 18px; line-height: 1.5; }
    </style>
</head>
<body>
    <div class="success">
        <h1>🎉 Setup Complete!</h1>
        <p><strong>CloudSync is now configured!</strong></p>
        <p>You can close this browser window and return to Kodi.</p>
        <p>The addon will start syncing automatically.</p>
    </div>
</body>
</html>
                """

                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(html.encode('utf-8'))
            else:
                raise Exception("Invalid response from Dropbox - no access token")

    def send_error_page(self, error_msg):
        """Send error page."""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Setup Error</title>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; text-align: center; margin: 50px; }}
        .error {{ background: #f8d7da; color: #721c24; padding: 30px; border-radius: 10px;
                 max-width: 500px; margin: 50px auto; }}
    </style>
</head>
<body>
    <div class="error">
        <h1>❌ Setup Failed</h1>
        <p>{error_msg}</p>
        <p><a href="/">← Try Again</a></p>
    </div>
</body>
</html>
        """

        self.send_response(400)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def send_404(self):
        """Send 404."""
        self.send_response(404)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"<h1>404 Not Found</h1><p><a href='/'>Go to Setup</a></p>")

    def get_server_ip(self):
        """Get server IP."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except:
            return "localhost"

    def log_message(self, format, *args):
        """Use Kodi logging."""
        xbmc.log(f"[CloudSync] Simple Web: {format % args}", xbmc.LOGDEBUG)


class SimpleWebSetup:
    """Simple web server for OAuth2 setup."""

    def __init__(self):
        self.server = None
        self.thread = None
        self.port = None

    def start(self):
        """Start web server."""
        try:
            # Find free port
            for port in range(8765, 8790):
                try:
                    self.server = HTTPServer(('', port), SimpleSetupHandler)
                    self.port = port
                    break
                except OSError:
                    continue

            if not self.server:
                raise OSError("No free ports available")

            self.server.setup_complete = False

            # Start server thread
            self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.thread.start()

            xbmc.log(f"[CloudSync] Simple web setup started on port {self.port}", xbmc.LOGINFO)
            return True

        except Exception as e:
            xbmc.log(f"[CloudSync] Failed to start simple web server: {e}", xbmc.LOGERROR)
            return False

    def stop(self):
        """Stop server."""
        if self.server:
            self.server.shutdown()
            self.server = None

    def get_url(self):
        """Get server URL."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                ip = s.getsockname()[0]
            return f"http://{ip}:{self.port}"
        except:
            return f"http://localhost:{self.port}"

    def is_complete(self):
        """Check if setup is complete."""
        if not self.server:
            return False

        if not hasattr(self.server, 'setup_complete'):
            return False

        is_done = self.server.setup_complete
        if is_done:
            xbmc.log("[CloudSync] is_complete() returning True - setup is done!", xbmc.LOGINFO)

        return is_done