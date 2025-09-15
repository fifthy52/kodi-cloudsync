import sys
import os
import xbmc
import xbmcaddon
import xbmcgui

# Add lib path
addon_path = os.path.dirname(os.path.dirname(__file__))
lib_path = os.path.join(addon_path, 'lib')
sys.path.append(lib_path)


def setup_dropbox_auth():
    """Simple Dropbox authorization setup."""
    try:
        addon = xbmcaddon.Addon('service.cloudsync')
        
        # Show information dialog
        dialog = xbmcgui.Dialog()
        
        info_lines = [
            "CloudSync Dropbox Setup",
            "",
            "To use Dropbox sync, you need an access token with proper permissions.",
            "",
            "Steps:",
            "1. Go to: https://dropbox.com/developers/apps",
            "2. Create new app (Scoped access, App folder)",
            "3. Go to Permissions tab",
            "4. Enable these permissions:",
            "   - files.content.write",
            "   - files.content.read", 
            "   - files.metadata.read",
            "5. Go to Settings tab",
            "6. Generate access token",
            "7. Copy the token and paste it here",
            "",
            "IMPORTANT: Without proper permissions, upload will fail!",
            "",
            "Click OK to enter your access token."
        ]
        
        dialog.textviewer("Dropbox Setup Instructions", "\n".join(info_lines))
        
        # Get access token from user
        current_token = addon.getSetting('dropbox_access_token') or ""
        
        token = dialog.input(
            "Enter Dropbox Access Token",
            current_token,
            type=xbmcgui.INPUT_ALPHANUM
        )
        
        if token:
            # Save token
            addon.setSetting('dropbox_access_token', token)
            addon.setSettingBool('dropbox_enabled', True)
            
            # Test connection
            try:
                # Import here to avoid circular imports
                import sys
                import os
                current_dir = os.path.dirname(__file__)
                sys.path.insert(0, current_dir)
                
                from dropbox_provider_simple import DropboxProviderSimple
                provider = DropboxProviderSimple()
                
                if provider.test_connection():
                    dialog.ok(
                        "Dropbox Setup Complete", 
                        "✓ Successfully connected to Dropbox!",
                        "You can now use Dropbox sync."
                    )
                else:
                    dialog.ok(
                        "Connection Failed", 
                        "Could not connect to Dropbox.",
                        "Please check your access token."
                    )
            except Exception as e:
                dialog.ok(
                    "Test Error", 
                    f"Could not test connection: {str(e)}"
                )
        else:
            xbmc.log("[CloudSync] User cancelled Dropbox setup", xbmc.LOGINFO)
            
    except Exception as e:
        xbmc.log(f"[CloudSync] Dropbox auth error: {e}", xbmc.LOGERROR)
        xbmcgui.Dialog().ok(
            "Setup Error", 
            f"Setup failed: {str(e)}"
        )


if __name__ == "__main__":
    setup_dropbox_auth()