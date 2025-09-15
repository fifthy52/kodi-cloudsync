"""
Simple Web Setup for Dropbox OAuth2
No redirect URIs needed - just paste the code!
"""

import xbmc
import xbmcgui

try:
    from simple_web_setup import SimpleWebSetup
    WEB_AVAILABLE = True
except ImportError:
    WEB_AVAILABLE = False


def simple_web_setup():
    """Simple web-based OAuth2 setup."""
    dialog = xbmcgui.Dialog()

    if not WEB_AVAILABLE:
        dialog.ok("Error", "Simple web setup not available.")
        return True

    # Start web server
    web_server = SimpleWebSetup()

    if not web_server.start():
        dialog.ok("Server Error", "Failed to start web server.\nPlease try another setup method.")
        return True

    server_url = web_server.get_url()

    try:
        # Show URL to user
        choice = dialog.yesno("Simple Web Setup",
                             f"✨ Simple web setup started!\n\n"
                             f"🌐 Open this URL in any browser:\n"
                             f"{server_url}\n\n"
                             f"📱 Works from phone, tablet, or any device on network\n"
                             f"💻 Much easier than typing in Kodi!\n\n"
                             f"Open browser now?",
                             yeslabel="Open Browser", nolabel="Show URL Only")

        if choice:
            # Try to open browser
            try:
                import platform
                system = platform.system().lower()
                if system == 'windows':
                    xbmc.executebuiltin(f'System.Exec("start {server_url}")')
                elif system == 'darwin':
                    xbmc.executebuiltin(f'System.Exec("open {server_url}")')
                else:
                    xbmc.executebuiltin(f'System.Exec("xdg-open {server_url}")')
            except:
                pass

        # Wait for completion
        progress = xbmcgui.DialogProgress()
        progress.create("Simple Web Setup", f"Server: {server_url}")

        try:
            for i in range(300):  # 5 minutes max
                if progress.iscanceled():
                    break

                if web_server.is_complete():
                    progress.update(100, "✅ Setup completed!")
                    xbmc.sleep(2000)
                    dialog.ok("Success! 🎉",
                             "CloudSync setup completed successfully!\n\n"
                             "✅ Dropbox is now configured\n"
                             "🔄 Syncing will start automatically\n"
                             "🌐 You can close the browser")
                    break

                mins = (300 - i) // 60
                secs = (300 - i) % 60
                progress.update(int(i * 100 / 300),
                              f"Complete setup in your browser\n"
                              f"Time remaining: {mins}:{secs:02d}\n"
                              f"URL: {server_url}")

                xbmc.sleep(1000)
            else:
                # Timeout
                progress.close()
                keep_running = dialog.yesno("Timeout",
                                          f"Setup timed out after 5 minutes.\n\n"
                                          f"Web server is still running at:\n{server_url}\n\n"
                                          f"Keep server running?",
                                          yeslabel="Keep Running", nolabel="Stop")

                if keep_running:
                    dialog.ok("Server Running",
                             f"Web server continues at:\n{server_url}\n\n"
                             "Complete setup anytime!\n"
                             "Server stops when Kodi restarts.")
                    return True

            progress.close()

        except Exception as e:
            progress.close()
            dialog.ok("Error", f"Setup error: {e}")

    finally:
        web_server.stop()

    return True


if __name__ == "__main__":
    simple_web_setup()