import sys
import os
import time
import xbmc
import xbmcaddon

# Add lib path  
sys.path.append(os.path.join(os.path.dirname(__file__), 'resources', 'lib'))

from hybrid_sync_manager import HybridSyncManager


class CloudSyncServiceV2:
    """Simplified CloudSync service using hybrid sync approach."""
    
    def __init__(self):
        self.addon = xbmcaddon.Addon('service.cloudsync')
        self.monitor = xbmc.Monitor()
        self.sync_manager = None
        self.running = False
    
    def start(self):
        """Start the service."""
        try:
            if not self.addon.getSettingBool('enabled'):
                xbmc.log("[CloudSync] CloudSync is disabled in settings", xbmc.LOGINFO)
                return
            
            xbmc.log("[CloudSync] CloudSync V2 service starting", xbmc.LOGINFO)
            self.running = True
            
            # Initialize hybrid sync manager
            self.sync_manager = HybridSyncManager()
            if not self.sync_manager.initialize():
                xbmc.log("[CloudSync] Failed to initialize hybrid sync manager", xbmc.LOGERROR)
                return
            
            # Perform initial sync
            xbmc.log("[CloudSync] Performing initial sync", xbmc.LOGINFO)
            self.sync_manager.perform_full_sync()
            
            # Main loop with periodic sync
            self._main_loop()
            
        except Exception as e:
            xbmc.log(f"[CloudSync] Error starting CloudSync V2 service: {e}", xbmc.LOGERROR)
        finally:
            self.stop()
    
    def stop(self):
        """Stop the service."""
        xbmc.log("[CloudSync] CloudSync V2 service stopping", xbmc.LOGINFO)
        self.running = False
        
        if self.sync_manager:
            self.sync_manager.cleanup()
        
        xbmc.log("[CloudSync] CloudSync V2 service stopped", xbmc.LOGINFO)
    
    def _main_loop(self):
        """Main service loop with periodic syncing."""
        try:
            sync_interval = int(self.addon.getSetting('sync_interval') or '5') * 60
        except:
            sync_interval = 300  # Default 5 minutes
        last_sync = time.time()
        
        while self.running and not self.monitor.abortRequested():
            try:
                # Wait for abort or sync interval
                if self.monitor.waitForAbort(30):  # Check every 30 seconds
                    break
                
                current_time = time.time()
                
                # Check if it's time for periodic sync
                if (current_time - last_sync) >= sync_interval:
                    xbmc.log("[CloudSync] Performing periodic sync", xbmc.LOGDEBUG)
                    
                    if self.sync_manager.perform_full_sync():
                        last_sync = current_time
                        xbmc.log("[CloudSync] Periodic sync completed", xbmc.LOGDEBUG)
                    else:
                        xbmc.log("[CloudSync] Periodic sync failed", xbmc.LOGWARNING)
                
                # Update settings periodically
                if int(current_time) % 300 == 0:  # Every 5 minutes
                    self.sync_manager._update_settings()
                
            except Exception as e:
                xbmc.log(f"[CloudSync] Error in main loop: {e}", xbmc.LOGERROR)
                xbmc.sleep(30000)  # Wait 30 seconds after error


def main():
    service = CloudSyncServiceV2()
    service.start()


if __name__ == '__main__':
    main()