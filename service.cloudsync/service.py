#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CloudSync V3 - Main Service
MQTT-first real-time sync service for Kodi with Add-only Favorites
"""

import sys
import os
import time
import xml.etree.ElementTree as ET
import xbmc
import xbmcaddon

# Add lib path
sys.path.append(os.path.join(os.path.dirname(__file__), 'resources', 'lib'))

from mqtt_client import CloudSyncMQTT
from kodi_rpc import KodiRPC
from kodi_monitor import CloudSyncMonitor
from favorites_sync import FavoritesSync
from web_config import CloudSyncWebConfig


class CloudSyncServiceV3:
    """CloudSync V3 - Real-time MQTT sync service with add-only favorites"""

    def __init__(self):
        self.addon = xbmcaddon.Addon('service.cloudsync')
        self.mqtt = None
        self.kodi_rpc = KodiRPC()
        self.kodi_monitor = None
        self.running = False

        # Clean favorites sync with file monitoring
        self.favorites_sync = None

        # Web configuration server
        self.web_config = None


    def _log(self, message: str, level: int = xbmc.LOGINFO):
        """Centralized logging"""
        xbmc.log(f"CloudSync V3: {message}", level)

    def start(self):
        """Start the CloudSync V3 service"""
        try:
            # Check if service is enabled
            if not self.addon.getSettingBool('enabled'):
                self._log("CloudSync V3 is disabled in settings")
                return

            # Service instance protection using lock file
            import tempfile
            import os
            import fcntl if os.name != 'nt' else None

            self.lock_file_path = os.path.join(tempfile.gettempdir(), 'cloudsync_v3.lock')

            try:
                self.lock_file = open(self.lock_file_path, 'w')
                if os.name != 'nt':  # Unix systems
                    fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                else:  # Windows - simpler check
                    if os.path.exists(self.lock_file_path):
                        with open(self.lock_file_path, 'r') as f:
                            existing_pid = f.read().strip()
                        try:
                            os.kill(int(existing_pid), 0)  # Check if process exists
                            self._log(f"CloudSync V3 already running (PID: {existing_pid})")
                            return
                        except (OSError, ValueError):
                            pass  # Process doesn't exist, continue

                # Write current PID to lock file
                self.lock_file.write(str(os.getpid()))
                self.lock_file.flush()

            except (IOError, OSError) as e:
                self._log(f"CloudSync V3 already running or cannot create lock file: {e}")
                return

            self._log("CloudSync V3 service starting")
            self.running = True

            # Initialize MQTT client
            self.mqtt = CloudSyncMQTT()

            # Register message handlers
            self._register_message_handlers()

            # Initialize Kodi monitor with MQTT publish callback and settings change callback
            self.kodi_monitor = CloudSyncMonitor(
                mqtt_publish_callback=self._mqtt_publish,
                settings_change_callback=self._on_settings_changed
            )

            # Initialize favorites sync with file monitoring (V3: add-only mode)
            self.favorites_sync = FavoritesSync(mqtt_publish_callback=self._mqtt_publish)
            if self.addon.getSettingBool('sync_favorites'):
                if self.favorites_sync.start_monitoring():
                    self._log("V3: Favorites file monitoring started (add-only mode)")
                else:
                    self._log("Failed to start favorites file monitoring", xbmc.LOGWARNING)

            # Initialize web configuration server
            if self.addon.getSettingBool('enable_web_config'):
                self.web_config = CloudSyncWebConfig()
                web_port = int(self.addon.getSetting('web_config_port') or '8090')
                if self.web_config.start(web_port):
                    self._log(f"Web configuration server started on port {web_port}")
                else:
                    self._log("Failed to start web configuration server", xbmc.LOGWARNING)

            # Start MQTT connection
            if self.mqtt.start():
                self._log("MQTT connection established successfully")
            else:
                self._log("Failed to establish MQTT connection - continuing without sync", xbmc.LOGWARNING)

            # Main service loop
            self._main_loop()

        except Exception as e:
            self._log(f"Error starting CloudSync V3 service: {e}", xbmc.LOGERROR)
        finally:
            self.stop()

    def stop(self):
        """Stop the CloudSync V3 service"""
        self._log("CloudSync V3 service stopping")
        self.running = False

        # Stop favorites sync
        if self.favorites_sync:
            self.favorites_sync.stop_monitoring()

        # Stop web configuration server
        if self.web_config:
            self.web_config.stop()

        # Stop MQTT client
        if self.mqtt:
            self.mqtt.stop()

        # Clean up lock file
        try:
            import os
            if hasattr(self, 'lock_file') and self.lock_file:
                self.lock_file.close()
            if hasattr(self, 'lock_file_path') and os.path.exists(self.lock_file_path):
                os.remove(self.lock_file_path)
        except Exception as e:
            self._log(f"Error cleaning up lock file: {e}", xbmc.LOGWARNING)

        self._log("CloudSync V3 service stopped")

    def _register_message_handlers(self):
        """Register MQTT message handlers for different sync events"""
        if not self.mqtt:
            return

        # Register handlers for different message types
        self.mqtt.register_handler("cloudsync/watched/", self._handle_watched_message)
        self.mqtt.register_handler("cloudsync/resume/", self._handle_resume_message)
        self.mqtt.register_handler("cloudsync/favorites/add", self._handle_favorite_add_message)
        # V3: Remove handler disabled (add-only mode)
        # self.mqtt.register_handler("cloudsync/favorites/remove", self._handle_favorite_remove_message)
        self.mqtt.register_handler("cloudsync/devices/", self._handle_device_message)

        # Manual sync handlers
        self.mqtt.register_handler("cloudsync/favorites/master_publish", self._handle_master_favorites)

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
        self._log(f"Publishing: {topic}", xbmc.LOGDEBUG)

        if not self.mqtt:
            self._log("MQTT client is None", xbmc.LOGERROR)
            return False

        if not self.mqtt.is_connected():
            status = self.mqtt.get_status()
            self._log(f"MQTT not connected - status: {status}", xbmc.LOGWARNING)
            return False

        # Publishing to MQTT (removed verbose log)
        result = self.mqtt.publish(topic, payload)
        if not result:
            self._log(f"MQTT publish failed for: {topic}", xbmc.LOGWARNING)
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

    def _handle_favorite_add_message(self, topic: str, payload: dict):
        """Handle favorite add messages (V3: add-only mode)"""
        try:
            if not self.addon.getSettingBool('sync_favorites'):
                return

            self._log(f"Processing favorite add: {topic}", xbmc.LOGDEBUG)

            # Skip messages from our own device
            device_id = payload.get('device_id')
            if device_id == self._get_device_id():
                self._log("Skipping add message from own device", xbmc.LOGDEBUG)
                return

            content = payload.get('content', {})
            self._handle_favorite_add(content)

        except Exception as e:
            self._log(f"Error handling favorite add message: {e}", xbmc.LOGERROR)

    def _handle_favorite_remove_message(self, topic: str, payload: dict):
        """Handle favorite remove messages"""
        try:
            if not self.addon.getSettingBool('sync_favorites_disabled'):
                return

            self._log(f"Processing favorite remove: {topic}", xbmc.LOGDEBUG)

            # Skip messages from our own device
            device_id = payload.get('device_id')
            if device_id == self._get_device_id():
                self._log("Skipping remove message from own device", xbmc.LOGDEBUG)
                return

            content = payload.get('content', {})
            self._handle_favorite_remove(content)

        except Exception as e:
            self._log(f"Error handling favorite remove message: {e}", xbmc.LOGERROR)


    def _handle_favorite_add(self, content: dict):
        """Handle adding a single favorite from another device (V3: with anti-loop protection)"""
        try:
            title = content.get('title', 'Unknown')
            xml_content = content.get('xml_content', '')
            thumbnail = content.get('thumbnail', '')

            self._log(f"V3: Received favorite add: {title}", xbmc.LOGINFO)

            if not xml_content:
                self._log(f"No XML content for favorite: {title}", xbmc.LOGWARNING)
                return

            # V3: Mark as received to prevent loop broadcasting
            if self.favorites_sync:
                self.favorites_sync.mark_favorite_as_received(title)
                self.favorites_sync.set_api_write_flag(True)

            try:
                # Use Kodi JSON-RPC to add favorite
                result = self.kodi_rpc.add_favorite(title, xml_content, thumbnail)
                if result:
                    self._log(f"V3: Successfully added favorite: {title}", xbmc.LOGINFO)
                else:
                    self._log(f"Failed to add favorite: {title}", xbmc.LOGWARNING)

            finally:
                # Clear API write flag
                if self.favorites_sync:
                    self.favorites_sync.set_api_write_flag(False)

        except Exception as e:
            self._log(f"Error handling favorite add: {e}", xbmc.LOGERROR)

    def _handle_favorite_remove(self, content: dict):
        """Handle removing a favorite from another device"""
        try:
            title = content.get('title', 'Unknown')
            self._log(f"Received favorite remove: {title}", xbmc.LOGINFO)

            # Set API write flag to prevent loop
            if self.favorites_sync:
                self.favorites_sync.set_api_write_flag(True)

            try:
                # Use Kodi JSON-RPC to remove favorite
                result = self.kodi_rpc.remove_favorite(title)
                if result:
                    self._log(f"Successfully removed favorite: {title}", xbmc.LOGINFO)
                else:
                    self._log(f"Failed to remove favorite: {title}", xbmc.LOGWARNING)

            finally:
                # Clear API write flag
                if self.favorites_sync:
                    self.favorites_sync.set_api_write_flag(False)

        except Exception as e:
            self._log(f"Error handling favorite remove: {e}", xbmc.LOGERROR)

    def _get_device_id(self):
        """Get unique device identifier (same as MQTT client)"""
        return self.mqtt.device_id if self.mqtt else "unknown"

    def _on_settings_changed(self):
        """Handle CloudSync settings changes - restart web server if needed"""
        try:
            self._log("Settings changed - checking web configuration", xbmc.LOGINFO)

            # Check if web config setting changed
            web_config_enabled = self.addon.getSettingBool('enable_web_config')
            web_config_port = int(self.addon.getSetting('web_config_port') or '8090')

            if web_config_enabled:
                # Stop existing web server if running
                if self.web_config and self.web_config.is_running():
                    self._log("Stopping existing web server for restart", xbmc.LOGINFO)
                    self.web_config.stop()

                # Start/restart web server
                if not self.web_config:
                    from web_config import CloudSyncWebConfig
                    self.web_config = CloudSyncWebConfig()

                if self.web_config.start(web_config_port):
                    self._log(f"Web configuration server started on port {web_config_port}", xbmc.LOGINFO)
                else:
                    self._log("Failed to start web configuration server", xbmc.LOGWARNING)
            else:
                # Stop web server if it's running but disabled
                if self.web_config and self.web_config.is_running():
                    self._log("Disabling web configuration server", xbmc.LOGINFO)
                    self.web_config.stop()

        except Exception as e:
            self._log(f"Error handling settings change: {e}", xbmc.LOGERROR)

    def _handle_device_message(self, topic: str, payload: dict):
        """Handle device status messages"""
        try:
            device_id = payload.get('device_id')
            status = payload.get('status')

            if device_id and device_id != self.mqtt.device_id:
                self._log(f"Device {device_id} is {status}", xbmc.LOGDEBUG)

        except Exception as e:
            self._log(f"Error handling device message: {e}", xbmc.LOGERROR)

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

                # Periodic status logging (every 5 minutes)
                loop_counter += 1
                if loop_counter >= 300:  # 300 seconds at 1-second intervals
                    loop_counter = 0
                    if self.mqtt:
                        status = self.mqtt.get_status()
                        self._log(f"Status: Connected={status['connected']}, Device={status['device_id'][:12]}...", xbmc.LOGDEBUG)



                # Wait 1 second (responsive for MQTT)
                if self.kodi_monitor.waitForAbort(1):
                    break

            except Exception as e:
                self._log(f"Error in main service loop: {e}", xbmc.LOGERROR)
                time.sleep(1)  # Prevent tight error loop

        self._log("Main service loop ended")


    def _handle_master_favorites(self, topic: str, payload: dict):
        """Handle master favorites publish from another device"""
        try:
            self._log(f"Received master favorites: {topic}", xbmc.LOGINFO)

            # Skip messages from our own device
            device_id = payload.get('device_id')
            if device_id == self._get_device_id():
                self._log("Skipping master favorites from own device", xbmc.LOGDEBUG)
                return

            if not self.addon.getSettingBool('sync_favorites'):
                self._log("Favorites sync disabled, ignoring master publish")
                return

            action = payload.get('action')
            favorites = payload.get('favorites', [])
            master_device = payload.get('master_device')

            if action == "master_publish" and favorites:
                self._log(f"Processing {len(favorites)} favorites from master {master_device}")

                # Clear existing favorites and replace with master list
                # (This is safe since user explicitly chose master)
                if self._replace_all_favorites(favorites):
                    self._log(f"Successfully replaced favorites with {len(favorites)} from {master_device}")
                    xbmc.executebuiltin('Notification(CloudSync V3,Favorites updated from master device,3000)')
                else:
                    self._log("Failed to replace favorites from master", xbmc.LOGERROR)

        except Exception as e:
            self._log(f"Error handling master favorites: {e}", xbmc.LOGERROR)


    def _replace_all_favorites(self, favorites: list) -> bool:
        """Replace all favorites with master list"""
        try:
            if not self.favorites_sync:
                return False

            # Mark as API operation to prevent loop broadcasting
            self.favorites_sync.set_api_write_flag(True)

            try:
                # Use Kodi JSON-RPC to clear and replace favorites
                # This is a simplified implementation
                if self.kodi_rpc:
                    return self.kodi_rpc.replace_all_favorites(favorites)
                return False

            finally:
                # Reset API flag after operation
                self.favorites_sync.set_api_write_flag(False)

        except Exception as e:
            self._log(f"Error replacing favorites: {e}", xbmc.LOGERROR)
            return False


def main():
    """Main entry point"""
    service = CloudSyncServiceV3()
    service.start()


if __name__ == '__main__':
    main()