"""
Local HTTP server for OAuth2 authorization code capture
Eliminates need for manual code entry - captures redirect automatically
"""

import socket
import threading
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
import xbmc


class OAuthHandler(BaseHTTPRequestHandler):
    """HTTP request handler for OAuth2 redirect."""

    def do_GET(self):
        """Handle GET request with authorization code."""
        try:
            # Parse query parameters
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)

            # Check for authorization code
            if 'code' in params:
                self.server.authorization_code = params['code'][0]
                xbmc.log(f"[CloudSync] Captured authorization code: {self.server.authorization_code[:10]}...", xbmc.LOGINFO)

                # Send success response
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()

                success_html = """
                <html>
                <head><title>CloudSync Authorization Complete</title></head>
                <body style="font-family: Arial; text-align: center; margin-top: 100px;">
                    <h1>✅ Authorization Successful!</h1>
                    <p>You can now close this browser window and return to Kodi.</p>
                    <p>CloudSync will continue the setup process automatically.</p>
                </body>
                </html>
                """
                self.wfile.write(success_html.encode())

            elif 'error' in params:
                error = params.get('error', ['unknown'])[0]
                self.server.authorization_error = error
                xbmc.log(f"[CloudSync] OAuth error: {error}", xbmc.LOGERROR)

                # Send error response
                self.send_response(400)
                self.send_header('Content-type', 'text/html')
                self.end_headers()

                error_html = f"""
                <html>
                <head><title>CloudSync Authorization Error</title></head>
                <body style="font-family: Arial; text-align: center; margin-top: 100px;">
                    <h1>❌ Authorization Failed</h1>
                    <p>Error: {error}</p>
                    <p>Please close this window and try again in Kodi.</p>
                </body>
                </html>
                """
                self.wfile.write(error_html.encode())
            else:
                # Unknown request
                self.send_response(400)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b"Invalid OAuth request")

        except Exception as e:
            xbmc.log(f"[CloudSync] OAuth handler error: {e}", xbmc.LOGERROR)
            self.send_response(500)
            self.end_headers()

    def log_message(self, format, *args):
        """Override to use Kodi logging."""
        xbmc.log(f"[CloudSync] OAuth Server: {format % args}", xbmc.LOGDEBUG)


class OAuthServer:
    """Local HTTP server for OAuth2 authorization code capture."""

    def __init__(self, port=8080):
        self.port = port
        self.server = None
        self.thread = None
        self.authorization_code = None
        self.authorization_error = None

    def find_free_port(self):
        """Find a free port for the server."""
        for port in range(8080, 8090):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('localhost', port))
                    return port
            except OSError:
                continue
        raise OSError("No free ports available")

    def start_server(self):
        """Start the OAuth server."""
        try:
            self.port = self.find_free_port()
            self.server = HTTPServer(('localhost', self.port), OAuthHandler)
            self.server.authorization_code = None
            self.server.authorization_error = None

            # Start server in background thread
            self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.thread.start()

            xbmc.log(f"[CloudSync] OAuth server started on http://localhost:{self.port}", xbmc.LOGINFO)
            return True

        except Exception as e:
            xbmc.log(f"[CloudSync] Failed to start OAuth server: {e}", xbmc.LOGERROR)
            return False

    def stop_server(self):
        """Stop the OAuth server."""
        if self.server:
            self.server.shutdown()
            self.server = None
            xbmc.log("[CloudSync] OAuth server stopped", xbmc.LOGINFO)

    def get_redirect_uri(self):
        """Get the redirect URI for OAuth."""
        return f"http://localhost:{self.port}"

    def wait_for_code(self, timeout=60):
        """Wait for authorization code with timeout."""
        import time

        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.server and hasattr(self.server, 'authorization_code') and self.server.authorization_code:
                self.authorization_code = self.server.authorization_code
                return self.authorization_code

            if self.server and hasattr(self.server, 'authorization_error') and self.server.authorization_error:
                self.authorization_error = self.server.authorization_error
                return None

            time.sleep(0.5)

        return None  # Timeout