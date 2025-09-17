#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CloudSync V2 - Main Service
MQTT-first real-time sync service for Kodi with Favorites polling
"""

import sys
import os
import time
import xbmc
import xbmcaddon

# Add lib path
sys.path.append(os.path.join(os.path.dirname(__file__), 'resources', 'lib'))

from mqtt_client import CloudSyncMQTT
from kodi_rpc import KodiRPC
from kodi_monitor import CloudSyncMonitor


class CloudSyncServiceV2:
    """CloudSync V2 - Real-time MQTT sync service"""

    def __init__(self):
        self.addon = xbmcaddon.Addon('service.cloudsync')
        self.mqtt = None
        self.kodi_rpc = KodiRPC()
        self.kodi_monitor = None
        self.running = False

        # Favorites polling state
        self.last_favorites = None
        self.favorites_check_counter = 0

    def _log(self, message: str, level: int = xbmc.LOGINFO):
        """Centralized logging"""
        xbmc.log(f"CloudSync V2: {message}", level)

    def start(self):
        """Start the CloudSync V2 service"""
        try:
            # Check if service is enabled
            if not self.addon.getSettingBool('enabled'):
                self._log("CloudSync V2 is disabled in settings")
                return

            self._log("CloudSync V2 service starting")
            self.running = True

            # Initialize MQTT client
            self.mqtt = CloudSyncMQTT()

            # Register message handlers
            self._register_message_handlers()

            # Initialize Kodi monitor with MQTT publish callback
            self.kodi_monitor = CloudSyncMonitor(mqtt_publish_callback=self._mqtt_publish)

            # Start MQTT connection
            if self.mqtt.start():
                self._log("MQTT connection established successfully")
            else:
                self._log("Failed to establish MQTT connection - continuing without sync", xbmc.LOGWARNING)

            # Main service loop
            self._main_loop()

        except Exception as e:
            self._log(f"Error starting CloudSync V2 service: {e}", xbmc.LOGERROR)
        finally:
            self.stop()

    def stop(self):
        """Stop the CloudSync V2 service"""
        self._log("CloudSync V2 service stopping")
        self.running = False

        # Stop MQTT client
        if self.mqtt:
            self.mqtt.stop()

        self._log("CloudSync V2 service stopped")

    def _register_message_handlers(self):
        """Register MQTT message handlers for different sync events"""
        if not self.mqtt:
            return

        # Register handlers for different message types
        self.mqtt.register_handler("cloudsync/watched/", self._handle_watched_message)
        self.mqtt.register_handler("cloudsync/resume/", self._handle_resume_message)
        self.mqtt.register_handler("cloudsync/favorites/", self._handle_favorites_message)
        self.mqtt.register_handler("cloudsync/devices/", self._handle_device_message)

        self._log("MQTT message handlers registered")

    def _handle_watched_message(self, topic: str, payload: dict):
        """Handle watched status sync messages"""
        try:
            if not self.addon.getSettingBool('sync_watched'):
                return

            self._log(f"Processing watched status sync: {topic}", xbmc.LOGDEBUG)

            content = payload.get('content', {})
            content_type = content.get('type')
            title = content.get('title', 'Unknown')
            playcount = content.get('playcount', 0)
            uniqueid = content.get('uniqueid', {})

            if not uniqueid:
                self._log(f"No unique ID for {content_type}: {title}", xbmc.LOGWARNING)
                return

            if content_type == 'movie':
                self._sync_movie_watched(title, uniqueid, playcount)
            elif content_type == 'episode':
                season = content.get('season')
                episode = content.get('episode')
                show_uniqueid = content.get('show_uniqueid', {})
                self._sync_episode_watched(title, show_uniqueid, season, episode, playcount)

        except Exception as e:
            self._log(f"Error handling watched message: {e}", xbmc.LOGERROR)

    def _sync_movie_watched(self, title: str, uniqueid: dict, playcount: int):
        """Sync movie watched status"""
        try:
            movie_id = self.kodi_rpc.find_movie_by_uniqueid(uniqueid)
            if movie_id:
                if self.kodi_rpc.set_movie_playcount(movie_id, playcount):
                    self._log(f"Updated watched status for movie: {title} (playcount={playcount})")
                else:
                    self._log(f"Failed to update watched status for movie: {title}", xbmc.LOGWARNING)
            else:
                self._log(f"Movie not found in library: {title}", xbmc.LOGDEBUG)

        except Exception as e:
            self._log(f"Error syncing movie watched status: {e}", xbmc.LOGERROR)

    def _sync_episode_watched(self, title: str, show_uniqueid: dict, season: int, episode: int, playcount: int):
        """Sync episode watched status"""
        try:
            episode_id = self.kodi_rpc.find_episode_by_show_and_episode(show_uniqueid, season, episode)
            if episode_id:
                if self.kodi_rpc.set_episode_playcount(episode_id, playcount):
                    self._log(f"Updated watched status for episode: {title} S{season}E{episode} (playcount={playcount})")
                else:
                    self._log(f"Failed to update watched status for episode: {title}", xbmc.LOGWARNING)
            else:
                self._log(f"Episode not found in library: {title} S{season}E{episode}", xbmc.LOGDEBUG)

        except Exception as e:
            self._log(f"Error syncing episode watched status: {e}", xbmc.LOGERROR)

    def _mqtt_publish(self, topic: str, payload: dict) -> bool:
        """Publish message to MQTT with connection check"""
        self._log(f"_mqtt_publish called: topic={topic}", xbmc.LOGINFO)

        if not self.mqtt:
            self._log("MQTT client is None", xbmc.LOGERROR)
            return False

        if not self.mqtt.is_connected():
            status = self.mqtt.get_status()
            self._log(f"MQTT not connected - status: {status}", xbmc.LOGWARNING)
            return False

        self._log("Publishing to MQTT...", xbmc.LOGINFO)
        result = self.mqtt.publish(topic, payload)
        self._log(f"MQTT publish completed with result: {result}", xbmc.LOGINFO)
        return result

    def _handle_resume_message(self, topic: str, payload: dict):
        """Handle resume point sync messages"""
        try:
            if not self.addon.getSettingBool('sync_resume'):
                return

            self._log(f"Processing resume point sync: {topic}", xbmc.LOGDEBUG)

            content = payload.get('content', {})
            content_type = content.get('type')
            title = content.get('title', 'Unknown')
            resume = content.get('resume', {})
            uniqueid = content.get('uniqueid', {})

            if not uniqueid or not resume.get('position'):
                self._log(f"No unique ID or resume position for {content_type}: {title}", xbmc.LOGWARNING)
                return

            if content_type == 'movie':
                self._sync_movie_resume(title, uniqueid, resume)
            elif content_type == 'episode':
                season = content.get('season')
                episode = content.get('episode')
                show_uniqueid = content.get('show_uniqueid', {})
                self._sync_episode_resume(title, show_uniqueid, season, episode, resume)

        except Exception as e:
            self._log(f"Error handling resume message: {e}", xbmc.LOGERROR)

    def _sync_movie_resume(self, title: str, uniqueid: dict, resume: dict):
        """Sync movie resume point"""
        try:
            movie_id = self.kodi_rpc.find_movie_by_uniqueid(uniqueid)
            if movie_id:
                position = resume.get('position', 0)
                total = resume.get('total', 0)

                if self.kodi_rpc.set_movie_resume(movie_id, position, total):
                    self._log(f"Updated resume point for movie: {title} ({position}s)")
                else:
                    self._log(f"Failed to update resume point for movie: {title}", xbmc.LOGWARNING)
            else:
                self._log(f"Movie not found in library: {title}", xbmc.LOGDEBUG)

        except Exception as e:
            self._log(f"Error syncing movie resume point: {e}", xbmc.LOGERROR)

    def _sync_episode_resume(self, title: str, show_uniqueid: dict, season: int, episode: int, resume: dict):
        """Sync episode resume point"""
        try:
            episode_id = self.kodi_rpc.find_episode_by_show_and_episode(show_uniqueid, season, episode)
            if episode_id:
                position = resume.get('position', 0)
                total = resume.get('total', 0)

                if self.kodi_rpc.set_episode_resume(episode_id, position, total):
                    self._log(f"Updated resume point for episode: {title} S{season}E{episode} ({position}s)")
                else:
                    self._log(f"Failed to update resume point for episode: {title}", xbmc.LOGWARNING)
            else:
                self._log(f"Episode not found in library: {title} S{season}E{episode}", xbmc.LOGDEBUG)

        except Exception as e:
            self._log(f"Error syncing episode resume point: {e}", xbmc.LOGERROR)

    def _handle_favorites_message(self, topic: str, payload: dict):
        """Handle favorites sync messages"""
        try:
            if not self.addon.getSettingBool('sync_favorites'):
                return

            self._log(f"Processing favorites sync: {topic}", xbmc.LOGDEBUG)

            content = payload.get('content', {})
            action = content.get('action')
            title = content.get('title', 'Unknown')
            path = content.get('path', '')
            fav_type = content.get('type', 'unknown')

            if action == 'add':
                self._sync_favorite_add(title, path, fav_type, content)
            elif action == 'remove':
                self._log(f"Received favorite remove (not implemented): {title}")

        except Exception as e:
            self._log(f"Error handling favorites message: {e}", xbmc.LOGERROR)

    def _sync_favorite_add(self, title: str, path: str, fav_type: str, content: dict):
        """Add favorite to local Kodi"""
        try:
            # Validate path protocol to avoid "Invalid protocol" errors
            if not path or not self._is_valid_favorite_path(path):
                self._log(f"Skipping favorite with invalid path: {title} - {path}", xbmc.LOGWARNING)
                return

            thumbnail = content.get('thumbnail', '')

            if self.kodi_rpc.add_favourite(title, fav_type, path, thumbnail):
                self._log(f"Added favorite: {title} ({fav_type})")
            else:
                self._log(f"Failed to add favorite: {title}", xbmc.LOGWARNING)

        except Exception as e:
            self._log(f"Error adding favorite: {e}", xbmc.LOGERROR)

    def _is_valid_favorite_path(self, path: str) -> bool:
        """Check if favorite path has valid protocol"""
        if not path:
            return False

        # Common valid protocols for Kodi favorites
        valid_protocols = [
            'plugin://', 'upnp://', 'nfs://', 'smb://', 'ftp://', 'http://', 'https://',
            'addons://', 'videodb://', 'musicdb://', 'special://', 'sources://',
            'library://', 'file://', 'zip://', 'rar://'
        ]

        return any(path.startswith(protocol) for protocol in valid_protocols)

    def _handle_device_message(self, topic: str, payload: dict):
        """Handle device status messages"""
        try:
            device_id = payload.get('device_id')
            status = payload.get('status')

            if device_id and device_id != self.mqtt.device_id:
                self._log(f"Device {device_id} is {status}", xbmc.LOGDEBUG)

        except Exception as e:
            self._log(f"Error handling device message: {e}", xbmc.LOGERROR)

    def _check_favorites_changes(self):
        """Check for favorites changes (polling-based)"""
        try:
            if not self.addon.getSettingBool('sync_favorites'):
                return

            # Get current favorites with error handling
            try:
                current_favorites = self.kodi_rpc.get_favourites()
                if current_favorites is None:
                    current_favorites = []
            except Exception as fav_error:
                self._log(f"Error getting favorites: {fav_error}", xbmc.LOGERROR)
                return

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

    def _main_loop(self):
        """Main service loop with MQTT processing and favorites polling"""
        self._log("Entering main service loop")

        loop_counter = 0

        while self.running and not self.kodi_monitor.abortRequested():
            try:
                # MQTT background loop handles network processing automatically
                # Just check connection status periodically
                if self.mqtt and not self.mqtt.is_connected():
                    self._log("MQTT disconnected - attempting reconnect", xbmc.LOGWARNING)
                    if self.mqtt.start():
                        self._log("MQTT reconnected successfully", xbmc.LOGINFO)
                    else:
                        self._log("MQTT reconnect failed", xbmc.LOGWARNING)

                # Periodic status logging (every 60 seconds)
                loop_counter += 1
                if loop_counter >= 60:  # 60 seconds at 1-second intervals
                    loop_counter = 0
                    if self.mqtt:
                        status = self.mqtt.get_status()
                        self._log(f"Service status: Connected={status['connected']}, Device={status['device_id']}", xbmc.LOGINFO)

                # Favorites polling (every 30 seconds)
                self.favorites_check_counter += 1
                if self.favorites_check_counter >= 30:
                    self.favorites_check_counter = 0
                    self._check_favorites_changes()

                # Wait 1 second (responsive for MQTT)
                if self.kodi_monitor.waitForAbort(1):
                    break

            except Exception as e:
                self._log(f"Error in main service loop: {e}", xbmc.LOGERROR)
                time.sleep(1)  # Prevent tight error loop

        self._log("Main service loop ended")


def main():
    """Main entry point"""
    service = CloudSyncServiceV2()
    service.start()


if __name__ == '__main__':
    main()