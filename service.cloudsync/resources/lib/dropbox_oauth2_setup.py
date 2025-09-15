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

# Import QR generator with error handling
try:
    from qr_generator import SimpleQRGenerator
    QR_AVAILABLE = True
except ImportError:
    QR_AVAILABLE = False
    xbmc.log("[CloudSync] QR generator not available", xbmc.LOGWARNING)


def setup_oauth2():
    """Setup Dropbox OAuth2 with refresh token."""
    addon = xbmcaddon.Addon('service.cloudsync')

    # Step 1: Get App Key and Secret from user
    dialog = xbmcgui.Dialog()

    app_key = dialog.input("Enter Dropbox App Key:", type=xbmcgui.INPUT_ALPHANUM)
    if not app_key:
        return False

    app_secret = dialog.input("Enter Dropbox App Secret:", type=xbmcgui.INPUT_ALPHANUM)
    if not app_secret:
        return False

    # Step 2: Generate authorization URL
    auth_url = (f"https://www.dropbox.com/oauth2/authorize?"
                f"client_id={app_key}&"
                f"response_type=code&"
                f"token_access_type=offline")

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
                    # Generate and show QR code
                    qr_ascii = SimpleQRGenerator.generate_qr_ascii(auth_url)
                    qr_url = SimpleQRGenerator.generate_qr_url(auth_url)

                    qr_text = f"Scan this QR code with your phone:\n\n{qr_ascii}\n\nOr visit: {qr_url}\n\nOriginal URL: {auth_url}\n\nThen:\n1. Log in to Dropbox\n2. Click 'Allow'\n3. Copy the authorization code"

                    xbmc.log(f"[CloudSync] Showing QR code for: {auth_url}", xbmc.LOGINFO)
                    dialog.textviewer("QR Code - Dropbox OAuth2", qr_text)
                except Exception as e:
                    xbmc.log(f"[CloudSync] QR code generation failed: {e}", xbmc.LOGERROR)
                    dialog.ok("QR Error", f"QR code generation failed.\nURL logged to Kodi log file.\n\nManual URL: {auth_url}")

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

    # Step 4: Get authorization code from user
    auth_code = dialog.input("Enter Authorization Code:", type=xbmcgui.INPUT_ALPHANUM)
    if not auth_code:
        return False

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