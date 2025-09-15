"""
Web-based Dropbox OAuth2 Setup
Opens web interface for easy credential entry from any device
"""

import xbmc
import xbmcaddon
import xbmcgui

try:
    from web_oauth_server import WebOAuthServer
    WEB_SERVER_AVAILABLE = True
except ImportError:
    WEB_SERVER_AVAILABLE = False
    xbmc.log("[CloudSync] Web OAuth server not available", xbmc.LOGWARNING)


def setup_web_oauth():
    """Setup Dropbox OAuth2 using web interface."""
    addon = xbmcaddon.Addon('service.cloudsync')
    dialog = xbmcgui.Dialog()

    if not WEB_SERVER_AVAILABLE:
        dialog.ok("Error", "Web OAuth server is not available.\nPlease try the legacy setup method.")
        return True

    # Start web server
    web_server = WebOAuthServer()

    try:
        if not web_server.start_server():
            dialog.ok("Server Error", "Failed to start web server.\nPlease try again or use legacy setup.")
            return True

        server_url = web_server.get_server_url()

        # Show server info to user
        setup_choice = dialog.yesno("CloudSync Web Setup",
                                   f"Web setup server started!\n\n"
                                   f"🌐 Open this URL in any browser:\n"
                                   f"{server_url}\n\n"
                                   f"You can use this from:\n"
                                   f"• This device: http://localhost:{web_server.port}\n"
                                   f"• Phone/tablet on same network\n"
                                   f"• Any device on your local network\n\n"
                                   f"Continue with web setup?",
                                   yeslabel="Open Browser", nolabel="Cancel")

        if not setup_choice:
            dialog.ok("Setup Cancelled", "Web setup cancelled.\nServer will be stopped.")
            web_server.stop_server()
            return True

        # Try to open browser automatically
        try:
            import platform
            system = platform.system().lower()
            if system == 'windows':
                xbmc.executebuiltin(f'System.Exec("start {server_url}")')
            elif system == 'darwin':  # macOS
                xbmc.executebuiltin(f'System.Exec("open {server_url}")')
            else:  # Linux, Android
                xbmc.executebuiltin(f'System.Exec("xdg-open {server_url}")')

            xbmc.log(f"[CloudSync] Opened browser to {server_url}", xbmc.LOGINFO)
        except Exception as e:
            xbmc.log(f"[CloudSync] Failed to open browser: {e}", xbmc.LOGWARNING)

        # Wait for setup completion with progress dialog
        progress = xbmcgui.DialogProgress()
        progress.create("CloudSync Web Setup",
                       f"Web server running on {server_url}")
        progress.update(0, f"Please complete setup in your browser...")

        try:
            # Wait for completion (max 5 minutes)
            for i in range(300):  # 300 seconds = 5 minutes
                if progress.iscanceled():
                    dialog.ok("Setup Cancelled", "Setup was cancelled by user.")
                    break

                if web_server.is_setup_complete():
                    progress.update(100, "Setup completed successfully!")
                    xbmc.sleep(2000)
                    dialog.ok("Setup Complete!",
                             "🎉 OAuth2 setup completed successfully!\n\n"
                             "CloudSync is now configured and will start syncing automatically.\n\n"
                             "You can close the browser window.")
                    break

                # Update progress
                minutes_left = (300 - i) // 60
                seconds_left = (300 - i) % 60
                progress.update(int(i * 100 / 300),
                              f"Waiting for browser setup completion...\n"
                              f"Time remaining: {minutes_left}:{seconds_left:02d}\n"
                              f"URL: {server_url}")

                xbmc.sleep(1000)
            else:
                # Timeout
                progress.close()
                timeout_choice = dialog.yesno("Setup Timeout",
                                            "Setup timed out after 5 minutes.\n\n"
                                            "The web server is still running if you want to continue.\n"
                                            "Keep server running?",
                                            yeslabel="Keep Running", nolabel="Stop Server")

                if not timeout_choice:
                    web_server.stop_server()
                    return True
                else:
                    dialog.ok("Server Running",
                             f"Web server will continue running.\n\n"
                             f"Complete setup at: {server_url}\n\n"
                             f"The server will stop when Kodi restarts.")
                    return True

            progress.close()

        except Exception as e:
            progress.close()
            xbmc.log(f"[CloudSync] Web setup error: {e}", xbmc.LOGERROR)
            dialog.ok("Setup Error", f"An error occurred during setup:\n{e}")

    finally:
        # Always stop server when done
        try:
            web_server.stop_server()
        except:
            pass

    return True


if __name__ == "__main__":
    setup_web_oauth()