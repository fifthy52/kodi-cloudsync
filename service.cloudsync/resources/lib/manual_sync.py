import sys
import os
import threading
import xbmc
import xbmcaddon
import xbmcgui

# Add current directory to path to avoid conflicts
current_dir = os.path.dirname(__file__)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from hybrid_sync_manager import HybridSyncManager


def perform_manual_sync():
    """Perform a manual full sync."""
    try:
        addon = xbmcaddon.Addon('service.cloudsync')
        
        # Show progress dialog
        progress = xbmcgui.DialogProgress()
        progress.create("CloudSync", "Initializing sync...")
        
        if progress.iscanceled():
            return
        
        # Initialize hybrid sync manager
        progress.update(10, "Connecting to Dropbox...")
        sync_manager = HybridSyncManager()
        
        if not sync_manager.initialize():
            progress.close()
            xbmcgui.Dialog().ok("CloudSync Error", "Failed to initialize sync manager.", 
                              "Please check your Dropbox settings.")
            return
        
        if progress.iscanceled():
            progress.close()
            return
        
        # Perform sync
        progress.update(50, "Syncing data...")
        
        # Perform sync directly without additional thread
        try:
            xbmc.log("[CloudSync] Manual sync starting", xbmc.LOGINFO)
            success = sync_manager.perform_full_sync()
            
            progress.update(100, "Sync completed")
            xbmc.sleep(1000)
            progress.close()
            
            if success:
                xbmc.executebuiltin('Notification(CloudSync,Manual sync completed successfully,3000)')
                xbmc.log("[CloudSync] Manual sync completed successfully", xbmc.LOGINFO)
            else:
                xbmc.executebuiltin('Notification(CloudSync,Manual sync failed - check logs,5000)')
                xbmc.log("[CloudSync] Manual sync failed", xbmc.LOGERROR)
                
        except Exception as e:
            progress.close()
            xbmc.log(f"[CloudSync] Error in manual sync: {e}", xbmc.LOGERROR)
            error_msg = str(e).replace(',', ' - ')  # Replace commas to avoid notification parsing issues
            xbmc.executebuiltin(f'Notification(CloudSync,Manual sync error: {error_msg},5000)')
        
    except Exception as e:
        xbmc.log(f"[CloudSync] Error in manual sync: {e}", xbmc.LOGERROR)
        try:
            progress.close()
        except:
            pass
        error_msg = str(e)
        xbmcgui.Dialog().ok("CloudSync Error", f"Manual sync failed: {error_msg}")


if __name__ == "__main__":
    perform_manual_sync()