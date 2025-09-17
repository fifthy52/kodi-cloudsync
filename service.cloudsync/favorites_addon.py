#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CloudSync V2 - Favorites Polling Addition
Add this code to main service for favorites monitoring
"""

def _check_favorites_changes(self):
    """Check for favorites changes (polling-based)"""
    try:
        if not self.addon.getSettingBool('sync_favorites'):
            return

        # Get current favorites
        current_favorites = self.kodi_rpc.get_favourites()

        # Initialize if first run
        if self.last_favorites is None:
            self.last_favorites = current_favorites
            self._log(f"Initialized favorites tracking: {len(current_favorites)} items", xbmc.LOGDEBUG)
            return

        # Compare with previous state
        current_set = {self._favorite_key(fav) for fav in current_favorites}
        previous_set = {self._favorite_key(fav) for fav in self.last_favorites}

        # Find added and removed favorites
        added_keys = current_set - previous_set
        removed_keys = previous_set - current_set

        # Find actual favorite objects
        added_favorites = [fav for fav in current_favorites if self._favorite_key(fav) in added_keys]
        removed_favorites = [fav for fav in self.last_favorites if self._favorite_key(fav) in removed_keys]

        # Publish changes
        for favorite in added_favorites:
            self._publish_favorite_change("add", favorite)

        for favorite in removed_favorites:
            self._publish_favorite_change("remove", favorite)

        # Update state
        self.last_favorites = current_favorites

    except Exception as e:
        self._log(f"Error checking favorites changes: {e}", xbmc.LOGERROR)

def _favorite_key(self, favorite):
    """Generate unique key for favorite item"""
    # Use title and path as unique identifier
    title = favorite.get('title', '')
    path = favorite.get('path', '')
    return f"{title}|{path}"

def _publish_favorite_change(self, action, favorite):
    """Publish favorite add/remove to MQTT"""
    try:
        title = favorite.get('title', 'Unknown')
        path = favorite.get('path', '')
        fav_type = favorite.get('type', 'unknown')

        self._log(f"Favorites {action}: {title} ({fav_type})", xbmc.LOGINFO)

        topic = f"cloudsync/favorites/{action}"

        payload = {
            "content": {
                "action": action,
                "title": title,
                "path": path,
                "type": fav_type,
                "thumbnail": favorite.get('thumbnail', '')
            }
        }

        if self.mqtt and self.mqtt.is_connected():
            result = self.mqtt.publish(topic, payload)
            self._log(f"Published favorite {action}: {title} - Result: {result}", xbmc.LOGINFO)
        else:
            self._log(f"Cannot publish favorite {action} - MQTT not connected", xbmc.LOGWARNING)

    except Exception as e:
        self._log(f"Error publishing favorite change: {e}", xbmc.LOGERROR)

# Add to main loop:
# Every 30 seconds check favorites (30 * 1-second intervals)
self.favorites_check_counter += 1
if self.favorites_check_counter >= 30:
    self.favorites_check_counter = 0
    self._check_favorites_changes()