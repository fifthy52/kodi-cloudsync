#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CloudSync V3 - Manual Sync Actions
Handles user-initiated sync requests and favorites publishing
"""

import json
import sys
import time
import xbmc
import xbmcaddon
import xbmcgui
from typing import Dict, Any, List

# Import CloudSync components
try:
    from mqtt_client import CloudSyncMQTT
except ImportError:
    import os
    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from mqtt_client import CloudSyncMQTT


class SyncActions:
    """Handles manual sync actions from settings"""

    def __init__(self):
        self.addon = xbmcaddon.Addon('service.cloudsync')
        self.mqtt = None
        self._init_mqtt()

    def _init_mqtt(self):
        """Initialize MQTT client for sync actions"""
        try:
            self.mqtt = CloudSyncMQTT()
            if not self.mqtt.configure():
                xbmc.log("CloudSync V3: MQTT not configured for sync actions", xbmc.LOGWARNING)
                return

            # Don't start full connection, just configure for publishing
            if not self.mqtt.connect():
                xbmc.log("CloudSync V3: Failed to connect MQTT for sync actions", xbmc.LOGERROR)
                self.mqtt = None
        except Exception as e:
            xbmc.log(f"CloudSync V3: Error initializing MQTT for sync: {e}", xbmc.LOGERROR)
            self.mqtt = None

    def _log(self, message: str, level: int = xbmc.LOGINFO):
        """Centralized logging"""
        xbmc.log(f"CloudSync V3 Sync: {message}", level)

    def request_sync_status(self):
        """Request sync status from all online devices"""
        if not self.mqtt or not self.mqtt.is_connected():
            xbmcgui.Dialog().notification(
                "CloudSync V3",
                "MQTT not connected - cannot request sync",
                xbmcgui.NOTIFICATION_ERROR, 3000
            )
            return

        try:
            # Publish sync request to special topic
            sync_request_topic = "cloudsync/sync/request"
            payload = {
                "request_type": "status",
                "requested_data": ["watched", "resume"],
                "requestor_device": self.mqtt.device_id,
                "request_id": f"sync_{int(time.time())}"
            }

            # Use QoS 1 to ensure delivery, no retain (it's a one-time request)
            success = self.mqtt.publish(sync_request_topic, payload, qos=1, retain=False)

            if success:
                self._log("Sync status request published successfully")
                xbmcgui.Dialog().notification(
                    "CloudSync V3",
                    "Sync status requested from online devices",
                    xbmcgui.NOTIFICATION_INFO, 3000
                )
            else:
                self._log("Failed to publish sync status request", xbmc.LOGERROR)
                xbmcgui.Dialog().notification(
                    "CloudSync V3",
                    "Failed to send sync request",
                    xbmcgui.NOTIFICATION_ERROR, 3000
                )

        except Exception as e:
            self._log(f"Error requesting sync status: {e}", xbmc.LOGERROR)
            xbmcgui.Dialog().notification(
                "CloudSync V3",
                f"Sync request error: {str(e)}",
                xbmcgui.NOTIFICATION_ERROR, 3000
            )

    def publish_all_favorites(self):
        """Publish all favorites from this device as master"""
        if not self.mqtt or not self.mqtt.is_connected():
            xbmcgui.Dialog().notification(
                "CloudSync V3",
                "MQTT not connected - cannot publish favorites",
                xbmcgui.NOTIFICATION_ERROR, 3000
            )
            return

        try:
            # Get all current favorites from Kodi
            favorites = self._get_all_favorites()

            if not favorites:
                xbmcgui.Dialog().notification(
                    "CloudSync V3",
                    "No favorites found to publish",
                    xbmcgui.NOTIFICATION_WARNING, 3000
                )
                return

            # Confirm with user before publishing
            confirm = xbmcgui.Dialog().yesno(
                "CloudSync V3 - Publish Favorites",
                f"This will send {len(favorites)} favorites to all devices.",
                "Other devices will receive these favorites.",
                "Continue?"
            )

            if not confirm:
                return

            # Publish complete favorites list to special master topic
            master_topic = "cloudsync/favorites/master_publish"
            payload = {
                "action": "master_publish",
                "favorites": favorites,
                "master_device": self.mqtt.device_id,
                "publish_timestamp": int(time.time()),
                "favorites_count": len(favorites)
            }

            # Use QoS 1 and retain=False (it's a one-time complete sync)
            success = self.mqtt.publish(master_topic, payload, qos=1, retain=False)

            if success:
                self._log(f"Published {len(favorites)} favorites as master")
                xbmcgui.Dialog().notification(
                    "CloudSync V3",
                    f"Published {len(favorites)} favorites to all devices",
                    xbmcgui.NOTIFICATION_INFO, 3000
                )
            else:
                self._log("Failed to publish favorites as master", xbmc.LOGERROR)
                xbmcgui.Dialog().notification(
                    "CloudSync V3",
                    "Failed to publish favorites",
                    xbmcgui.NOTIFICATION_ERROR, 3000
                )

        except Exception as e:
            self._log(f"Error publishing all favorites: {e}", xbmc.LOGERROR)
            xbmcgui.Dialog().notification(
                "CloudSync V3",
                f"Favorites publish error: {str(e)}",
                xbmcgui.NOTIFICATION_ERROR, 3000
            )

    def _get_all_favorites(self) -> List[Dict[str, Any]]:
        """Get all favorites from Kodi database"""
        try:
            # Use JSON-RPC to get favorites
            json_query = {
                "jsonrpc": "2.0",
                "method": "Favourites.GetFavourites",
                "id": "cloudsync_get_favorites"
            }

            json_response = xbmc.executeJSONRPC(json.dumps(json_query))
            response = json.loads(json_response)

            if 'result' in response and 'favourites' in response['result']:
                favorites = response['result']['favourites']
                self._log(f"Retrieved {len(favorites)} favorites from Kodi")
                return favorites
            else:
                self._log("No favorites found in Kodi response")
                return []

        except Exception as e:
            self._log(f"Error getting favorites from Kodi: {e}", xbmc.LOGERROR)
            return []

    def cleanup(self):
        """Clean up resources"""
        if self.mqtt:
            self.mqtt.disconnect()


def main():
    """Main entry point for sync actions"""
    if len(sys.argv) < 2:
        xbmc.log("CloudSync V3: No sync action specified", xbmc.LOGWARNING)
        return

    action = sys.argv[1]
    sync_actions = SyncActions()

    try:
        if action == "request_sync":
            sync_actions.request_sync_status()
        elif action == "publish_favorites":
            sync_actions.publish_all_favorites()
        else:
            xbmc.log(f"CloudSync V3: Unknown sync action: {action}", xbmc.LOGWARNING)
    finally:
        sync_actions.cleanup()


if __name__ == "__main__":
    main()