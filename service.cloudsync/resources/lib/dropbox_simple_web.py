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
        # Show URL info and auto-open browser
        dialog.ok("Simple Web Setup Started",
                 f"✨ Web server is running!\n\n"
                 f"🌐 URL: {server_url}\n\n"
                 f"📱 Access from any device on your network\n"
                 f"💻 Browser will open automatically\n\n"
                 f"Complete the 4-step setup in your browser...")

        # Try to open browser automatically
        try:
            import platform
            system = platform.system().lower()
            if system == 'windows':
                xbmc.executebuiltin(f'System.Exec("start {server_url}")')
            elif system == 'darwin':
                xbmc.executebuiltin(f'System.Exec("open {server_url}")')
            else:
                xbmc.executebuiltin(f'System.Exec("xdg-open {server_url}")')
            xbmc.log(f"[CloudSync] Browser launched for {server_url}", xbmc.LOGINFO)
        except Exception as e:
            xbmc.log(f"[CloudSync] Failed to launch browser: {e}", xbmc.LOGWARNING)

        # Wait for completion with faster polling
        progress = xbmcgui.DialogProgress()
        progress.create("Simple Web Setup", f"Server: {server_url}")

        try:
            # Use faster polling - check every 0.5 seconds for better responsiveness
            total_checks = 600  # 5 minutes = 600 * 0.5 seconds

            for i in range(total_checks):
                if progress.iscanceled():
                    xbmc.log("[CloudSync] Web setup cancelled by user", xbmc.LOGINFO)
                    break

                # Check completion status more frequently
                if web_server.is_complete():
                    xbmc.log("[CloudSync] Web setup detected completion", xbmc.LOGINFO)
                    progress.update(100, "✅ Setup completed!")
                    progress.close()  # Close progress immediately

                    # Show success dialog
                    dialog.ok("Success! 🎉",
                             "CloudSync setup completed successfully!\n\n"
                             "✅ Dropbox is now configured\n"
                             "🔄 Syncing will start automatically\n"
                             "🌐 You can close the browser")
                    return True

                # Update progress every 2 seconds (every 4th check)
                if i % 4 == 0:
                    mins = (total_checks - i) // 120  # 120 checks per minute
                    secs = ((total_checks - i) % 120) // 2
                    progress.update(int(i * 100 / total_checks),
                                  f"Complete setup in your browser\n"
                                  f"Time remaining: {mins}:{secs:02d}\n"
                                  f"URL: {server_url}")

                xbmc.sleep(500)  # Check every 500ms instead of 1000ms
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