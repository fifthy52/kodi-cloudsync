#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CloudSync V3 - Manual Sync Actions
Handles user-initiated favorites publishing as master device
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
    """Handles manual favorites publishing from settings"""

    def __init__(self):
        self.addon = xbmcaddon.Addon('service.cloudsync')
        self.mqtt = None
        self._init_mqtt()

    def _init_mqtt(self):
        """Initialize MQTT client for favorites publishing"""
        try:
            self.mqtt = CloudSyncMQTT()
            if not self.mqtt.configure():
                xbmc.log("CloudSync V3: MQTT not configured for favorites publishing", xbmc.LOGWARNING)
                return

            # Don't start full connection, just configure for publishing
            if not self.mqtt.connect():
                xbmc.log("CloudSync V3: Failed to connect MQTT for favorites publishing", xbmc.LOGERROR)
                self.mqtt = None
        except Exception as e:
            xbmc.log(f"CloudSync V3: Error initializing MQTT for favorites publishing: {e}", xbmc.LOGERROR)
            self.mqtt = None

    def _log(self, message: str, level: int = xbmc.LOGINFO):
        """Centralized logging"""
        xbmc.log(f"CloudSync V3 Favorites: {message}", level)


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
    """Main entry point for favorites actions"""
    if len(sys.argv) < 2:
        xbmc.log("CloudSync V3: No action specified", xbmc.LOGWARNING)
        return

    action = sys.argv[1]
    sync_actions = SyncActions()

    try:
        if action == "publish_favorites":
            sync_actions.publish_all_favorites()
        else:
            xbmc.log(f"CloudSync V3: Unknown action: {action}", xbmc.LOGWARNING)
    finally:
        sync_actions.cleanup()


if __name__ == "__main__":
    main()