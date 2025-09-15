"""
Dropbox OAuth2 Setup with Refresh Token
Generates refresh token for long-term access to Dropbox API
"""

import json
import urllib.request
import urllib.error
import urllib.parse
import xbmc
import xbmcaddon
import xbmcgui

# Import QR generator and OAuth server with error handling
try:
    from qr_generator import SimpleQRGenerator
    QR_AVAILABLE = True
except ImportError:
    QR_AVAILABLE = False
    xbmc.log("[CloudSync] QR generator not available", xbmc.LOGWARNING)

try:
    from oauth_server import OAuthServer
    OAUTH_SERVER_AVAILABLE = True
except ImportError:
    OAUTH_SERVER_AVAILABLE = False
    xbmc.log("[CloudSync] OAuth server not available", xbmc.LOGWARNING)


def setup_oauth2():
    """Setup Dropbox OAuth2 with refresh token."""
    addon = xbmcaddon.Addon('service.cloudsync')

    # Step 1: Show setup instructions
    dialog = xbmcgui.Dialog()

    # Show setup instructions with continue/cancel option
    setup_choice = dialog.yesno("Dropbox OAuth2 Setup",
                               "This will setup automatic OAuth2 authentication.\n\n"
                               "FIRST: Go to Dropbox App Console and add these redirect URIs:\n"
                               "• http://localhost:8765\n"
                               "• http://localhost:8766\n"
                               "• http://localhost:8080\n"
                               "• http://localhost:8081\n\n"
                               "Continue with setup?",
                               yeslabel="Continue", nolabel="Cancel")

    if not setup_choice:
        dialog.ok("Setup Cancelled", "OAuth2 setup was cancelled.\nYou can try again anytime.")
        return True  # Return True to avoid restart loop

    # Get App Key and Secret from user
    app_key = dialog.input("Enter Dropbox App Key:", type=xbmcgui.INPUT_ALPHANUM)
    if not app_key:
        dialog.ok("Setup Cancelled", "Setup cancelled - no App Key provided.")
        return True  # Return True to avoid restart loop

    app_secret = dialog.input("Enter Dropbox App Secret:", type=xbmcgui.INPUT_ALPHANUM)
    if not app_secret:
        dialog.ok("Setup Cancelled", "Setup cancelled - no App Secret provided.")
        return True  # Return True to avoid restart loop

    # Step 2: Setup OAuth server for automatic code capture
    oauth_server = None
    redirect_uri = None

    if OAUTH_SERVER_AVAILABLE:
        try:
            oauth_server = OAuthServer()
            if oauth_server.start_server():
                redirect_uri = oauth_server.get_redirect_uri()
                xbmc.log(f"[CloudSync] OAuth server running on {redirect_uri}", xbmc.LOGINFO)
                dialog.notification("CloudSync", f"Server ready on port {oauth_server.port}", xbmcgui.NOTIFICATION_INFO, 2000)
            else:
                oauth_server = None
        except OSError as e:
            if "No free ports available" in str(e):
                xbmc.log("[CloudSync] All localhost ports are busy", xbmc.LOGWARNING)
                dialog.ok("Port Conflict",
                         "All localhost ports (8080-8100) are busy.\n"
                         "Falling back to manual authorization.\n\n"
                         "Consider closing other apps using localhost ports.")
            oauth_server = None
        except Exception as e:
            xbmc.log(f"[CloudSync] OAuth server failed: {e}", xbmc.LOGWARNING)
            oauth_server = None

    # Step 3: Generate authorization URL with redirect_uri
    if redirect_uri:
        auth_url = (f"https://www.dropbox.com/oauth2/authorize?"
                    f"client_id={app_key}&"
                    f"response_type=code&"
                    f"token_access_type=offline&"
                    f"redirect_uri={redirect_uri}")
        xbmc.log("[CloudSync] Using automatic code capture", xbmc.LOGINFO)
    else:
        auth_url = (f"https://www.dropbox.com/oauth2/authorize?"
                    f"client_id={app_key}&"
                    f"response_type=code&"
                    f"token_access_type=offline")
        xbmc.log("[CloudSync] Using manual code entry", xbmc.LOGINFO)

    # Step 3: Open browser automatically and show instructions
    try:
        # Try to open browser automatically - multi-platform support
        import sys
        import platform

        # Log URL first for fallback
        xbmc.log(f"[CloudSync] OAuth2 URL: {auth_url}", xbmc.LOGNOTICE)

        # Platform-specific browser opening
        system = platform.system().lower()
        if system == 'windows':
            xbmc.executebuiltin(f'System.Exec("start {auth_url}")')
        elif system == 'darwin':  # macOS
            xbmc.executebuiltin(f'System.Exec("open {auth_url}")')
        else:  # Linux, Android
            xbmc.executebuiltin(f'System.Exec("xdg-open {auth_url}")')

        xbmc.log(f"[CloudSync] Opened browser with OAuth URL on {system}", xbmc.LOGINFO)

        # Show QR code option only if available
        if QR_AVAILABLE:
            qr_choice = dialog.yesno("Dropbox OAuth2 Setup",
                                   "Browser should open automatically.\n\n"
                                   "Would you like to see a QR code for mobile scanning?",
                                   yeslabel="Show QR Code", nolabel="Continue")

            if qr_choice:
                try:
                    # Try to show real QR code image first
                    try:
                        import xbmcvfs
                        temp_dir = xbmcvfs.translatePath("special://temp/")
                        if not xbmcvfs.exists(temp_dir):
                            xbmcvfs.mkdirs(temp_dir)
                        qr_image_path = temp_dir + "oauth_qr.png"
                    except:
                        import tempfile
                        qr_image_path = tempfile.gettempdir() + "/oauth_qr.png"

                    # Download QR image
                    if SimpleQRGenerator.download_qr_image(auth_url, qr_image_path):
                        # Show image in Kodi image viewer
                        xbmc.executebuiltin(f'ShowPicture({qr_image_path})')

                        dialog.ok("QR Code Displayed",
                                "QR code image should be displayed.\n\n"
                                "1. Scan with your mobile device\n"
                                "2. Log in to Dropbox\n"
                                "3. Click 'Allow'\n"
                                "4. Copy the authorization code")
                    else:
                        # Fallback to URL display
                        qr_url = SimpleQRGenerator.generate_qr_url(auth_url)
                        qr_text = f"QR Code Generation:\n\nOnline QR Code: {qr_url}\n\nOriginal URL: {auth_url}\n\nInstructions:\n1. Open the QR URL in browser\n2. Scan the QR code with phone\n3. Log in to Dropbox\n4. Click 'Allow'\n5. Copy authorization code"

                        dialog.textviewer("QR Code URL", qr_text)

                except Exception as e:
                    xbmc.log(f"[CloudSync] QR code display failed: {e}", xbmc.LOGERROR)
                    dialog.ok("QR Error", f"QR code display failed.\nURL logged to Kodi log file.\n\nManual URL: {auth_url}")

        dialog.ok("Next Steps",
                  "1. Log in to Dropbox if needed\n"
                  "2. Click 'Allow' to authorize the app\n"
                  "3. Copy the authorization code from the page\n\n"
                  "If browser didn't open, check Kodi log for the URL.")
    except Exception as browser_error:
        # Fallback - show URL and QR code if automatic opening fails
        xbmc.log(f"[CloudSync] Browser auto-open failed: {browser_error}", xbmc.LOGWARNING)

        if QR_AVAILABLE:
            try:
                # Show QR code in fallback mode
                qr_ascii = SimpleQRGenerator.generate_qr_ascii(auth_url)
                qr_url = SimpleQRGenerator.generate_qr_url(auth_url)

                qr_text = f"Browser didn't open automatically. Use QR code:\n\n{qr_ascii}\n\nOr visit: {qr_url}\n\nManual URL: {auth_url}\n\nThen:\n1. Log in to Dropbox\n2. Click 'Allow'\n3. Copy the authorization code"
                dialog.textviewer("QR Code - Manual Setup", qr_text)
            except Exception as qr_error:
                xbmc.log(f"[CloudSync] QR fallback failed: {qr_error}", xbmc.LOGERROR)
                dialog.ok("Manual Setup", f"Please open this URL manually:\n\n{auth_url}\n\n1. Log in to Dropbox\n2. Click 'Allow'\n3. Copy authorization code")
        else:
            dialog.ok("Manual Setup", f"Please open this URL manually:\n\n{auth_url}\n\n1. Log in to Dropbox\n2. Click 'Allow'\n3. Copy authorization code")

    # Step 4: Get authorization code - automatic or manual
    auth_code = None

    if oauth_server:
        # Automatic code capture
        progress = xbmcgui.DialogProgress()
        progress.create("CloudSync OAuth2", "Waiting for authorization...")
        progress.update(0, "Please authorize in your browser...")

        try:
            # Wait for code with progress dialog
            for i in range(60):  # 60 seconds timeout
                if progress.iscanceled():
                    break

                auth_code = oauth_server.wait_for_code(1)  # Check every second
                if auth_code:
                    progress.update(100, "Authorization successful!")
                    xbmc.sleep(1000)
                    break

                if oauth_server.authorization_error:
                    progress.close()
                    dialog.ok("OAuth Error", f"Authorization failed: {oauth_server.authorization_error}")
                    return False

                progress.update(int((i + 1) * 100 / 60), f"Waiting... {60 - i}s remaining")
                xbmc.sleep(1000)

            progress.close()

            if not auth_code:
                # Timeout - fallback to manual entry
                dialog.ok("Timeout", "Automatic authorization timed out.\nFalling back to manual entry.")
                oauth_server.stop_server()
                oauth_server = None
        finally:
            if oauth_server:
                oauth_server.stop_server()

    if not auth_code:
        # Manual entry fallback
        auth_code = dialog.input("Enter Authorization Code:", type=xbmcgui.INPUT_ALPHANUM)
        if not auth_code:
            dialog.ok("Setup Cancelled", "Setup cancelled - no authorization code provided.")
            return True  # Return True to avoid restart loop

    # Step 5: Exchange code for tokens
    try:
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

        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))

            if 'access_token' in result and 'refresh_token' in result:
                # Save all credentials
                addon.setSetting('dropbox_app_key', app_key)
                addon.setSetting('dropbox_app_secret', app_secret)
                addon.setSetting('dropbox_access_token', result['access_token'])
                addon.setSetting('dropbox_refresh_token', result['refresh_token'])
                addon.setSetting('dropbox_enabled', 'true')

                xbmc.log("[CloudSync] OAuth2 setup completed successfully", xbmc.LOGINFO)
                dialog.ok("Success", "Dropbox OAuth2 setup completed!\nRefresh token saved for automatic renewal.")
                return True
            else:
                xbmc.log("[CloudSync] Invalid OAuth2 response", xbmc.LOGERROR)
                dialog.ok("Error", "Invalid response from Dropbox OAuth2")
                return False

    except urllib.error.HTTPError as e:
        error_msg = f"HTTP Error {e.code}: {e.reason}"
        xbmc.log(f"[CloudSync] OAuth2 HTTP Error: {error_msg}", xbmc.LOGERROR)
        dialog.ok("Error", f"OAuth2 failed:\n{error_msg}")
        return False
    except Exception as e:
        xbmc.log(f"[CloudSync] OAuth2 setup error: {e}", xbmc.LOGERROR)
        dialog.ok("Error", f"OAuth2 setup failed:\n{str(e)}")
        return False


if __name__ == "__main__":
    setup_oauth2()