import sys
import os
import time
import xbmc
import xbmcaddon

# Add lib path  
sys.path.append(os.path.join(os.path.dirname(__file__), 'resources', 'lib'))

from hybrid_sync_manager import HybridSyncManager
from mqtt_sync_manager import MQTTSyncManager


class CloudSyncServiceV2:
    """Simplified CloudSync service using hybrid sync approach."""
    
    def __init__(self):
        self.addon = xbmcaddon.Addon('service.cloudsync')
        self.monitor = xbmc.Monitor()
        self.sync_manager = None
        self.mqtt_manager = None
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

            # Initialize MQTT sync if enabled
            if self.addon.getSettingBool('mqtt_enabled'):
                xbmc.log("[CloudSync] Initializing MQTT sync", xbmc.LOGINFO)
                self.mqtt_manager = MQTTSyncManager()

                # Set up MQTT event handlers
                self.mqtt_manager.set_watched_handler(self._handle_mqtt_watched_change)
                self.mqtt_manager.set_favorites_handler(self._handle_mqtt_favorites_change)

                # Start MQTT sync
                if self.mqtt_manager.start():
                    xbmc.log("[CloudSync] MQTT sync started successfully", xbmc.LOGINFO)

                    # Connect MQTT to sync manager for publishing events
                    self.sync_manager.set_mqtt_manager(self.mqtt_manager)
                else:
                    xbmc.log("[CloudSync] Failed to start MQTT sync", xbmc.LOGWARNING)
                    self.mqtt_manager = None

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

        if self.mqtt_manager:
            self.mqtt_manager.stop()

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

    def _handle_mqtt_watched_change(self, content):
        """Handle watched status change from MQTT"""
        try:
            xbmc.log("[CloudSync] Processing MQTT watched change", xbmc.LOGDEBUG)

            content_type = content.get('type')
            uniqueid = content.get('uniqueid', {})
            title = content.get('title', 'Unknown')
            playcount = content.get('playcount', 0)
            lastplayed = content.get('lastplayed', '')
            resume = content.get('resume', {})

            # Apply change using sync manager
            if self.sync_manager:
                success = self.sync_manager.apply_remote_watched_change(
                    content_type, uniqueid, playcount, lastplayed, resume
                )

                if success:
                    xbmc.log(f"[CloudSync] Applied MQTT watched change for {content_type}: {title}", xbmc.LOGINFO)
                else:
                    xbmc.log(f"[CloudSync] Failed to apply MQTT watched change for {content_type}: {title}", xbmc.LOGWARNING)

        except Exception as e:
            xbmc.log(f"[CloudSync] Error handling MQTT watched change: {e}", xbmc.LOGERROR)

    def _handle_mqtt_favorites_change(self, content):
        """Handle favorites change from MQTT"""
        try:
            xbmc.log("[CloudSync] Processing MQTT favorites change", xbmc.LOGDEBUG)

            action = content.get('action')
            item_type = content.get('type')
            item_data = content.get('data', {})

            # Apply change using sync manager
            if self.sync_manager:
                success = self.sync_manager.apply_remote_favorites_change(action, item_type, item_data)

                if success:
                    xbmc.log(f"[CloudSync] Applied MQTT favorites {action} for {item_type}", xbmc.LOGINFO)
                else:
                    xbmc.log(f"[CloudSync] Failed to apply MQTT favorites {action} for {item_type}", xbmc.LOGWARNING)

        except Exception as e:
            xbmc.log(f"[CloudSync] Error handling MQTT favorites change: {e}", xbmc.LOGERROR)


def main():
    service = CloudSyncServiceV2()
    service.start()


if __name__ == '__main__':
    main()