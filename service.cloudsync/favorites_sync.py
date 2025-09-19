#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CloudSync V3 - Add-only Favorites Sync with Anti-loop Protection
Simple polling approach with anti-loop protection to prevent sync wars
"""

import os
import time
import threading
import xml.etree.ElementTree as ET
from typing import Optional, Dict, List, Callable

import xbmc
import xbmcvfs


class FavoritesSync:
    """CloudSync V3 - Add-only favorites sync with anti-loop protection"""

    def __init__(self, mqtt_publish_callback: Callable = None):
        self.mqtt_publish = mqtt_publish_callback
        self.favorites_path = None
        self.api_write_in_progress = False
        self.monitoring_thread = None
        self.stop_monitoring_flag = False
        self.last_file_mtime = 0
        self.last_file_size = 0
        self.previous_favorites = []

        # V3: Anti-loop protection - track recently received favorites
        self.recently_received_favorites = {}
        self.anti_loop_grace_period = 10  # seconds

        # Get platform-independent favourites.xml path
        self._init_favorites_path()

    def _log(self, message: str, level: int = xbmc.LOGINFO):
        """Centralized logging"""
        xbmc.log(f"CloudSync V3 Favorites: {message}", level)

    def _init_favorites_path(self):
        """Initialize platform-independent favourites.xml path"""
        try:
            # Try newer Kodi versions first
            try:
                userdata_path = xbmcvfs.translatePath('special://userdata/')
            except AttributeError:
                # Fallback for older Kodi versions
                userdata_path = xbmc.translatePath('special://userdata/')

            self.favorites_path = os.path.join(userdata_path, 'favourites.xml')
            self._log(f"Favourites path: {self.favorites_path}", xbmc.LOGINFO)

        except Exception as e:
            self._log(f"Error getting favourites path: {e}", xbmc.LOGERROR)
            self.favorites_path = None

    def start_monitoring(self):
        """Start simple polling monitoring"""
        if not self.favorites_path:
            self._log("Cannot start monitoring - no favourites path", xbmc.LOGERROR)
            return False

        try:
            # Initialize file state
            self._update_file_state()

            # Start monitoring thread
            self.stop_monitoring_flag = False
            self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitoring_thread.start()

            self._log("Started simple polling monitoring (5 second intervals)", xbmc.LOGINFO)
            return True

        except Exception as e:
            self._log(f"Error starting monitoring: {e}", xbmc.LOGERROR)
            return False

    def stop_monitoring(self):
        """Stop monitoring"""
        if self.monitoring_thread:
            self.stop_monitoring_flag = True
            self.monitoring_thread.join(timeout=2)
            self.monitoring_thread = None
            self._log("Stopped favorites monitoring", xbmc.LOGINFO)

    def _update_file_state(self):
        """Update stored file state"""
        try:
            if os.path.exists(self.favorites_path):
                stat = os.stat(self.favorites_path)
                self.last_file_mtime = stat.st_mtime
                self.last_file_size = stat.st_size
            else:
                self.last_file_mtime = 0
                self.last_file_size = 0
        except Exception as e:
            self._log(f"Error updating file state: {e}", xbmc.LOGERROR)

    def _monitoring_loop(self):
        """Simple polling loop"""
        while not self.stop_monitoring_flag:
            try:
                # Check if file has changed
                if self._has_file_changed():
                    self._log("Favourites file changed detected", xbmc.LOGINFO)

                    # Update file state
                    self._update_file_state()

                    # Process the change
                    self._on_favorites_changed()

                # Sleep for 5 seconds
                time.sleep(5)

            except Exception as e:
                self._log(f"Error in monitoring loop: {e}", xbmc.LOGERROR)
                time.sleep(5)

    def _has_file_changed(self):
        """Check if file has changed since last check"""
        try:
            if not os.path.exists(self.favorites_path):
                # File doesn't exist - changed if we had it before
                return self.last_file_mtime > 0 or self.last_file_size > 0

            stat = os.stat(self.favorites_path)
            current_mtime = stat.st_mtime
            current_size = stat.st_size

            # Check if modification time or size changed
            changed = (current_mtime != self.last_file_mtime or
                      current_size != self.last_file_size)

            return changed

        except Exception as e:
            self._log(f"Error checking file changes: {e}", xbmc.LOGERROR)
            return False

    def _on_favorites_changed(self):
        """Handle favourites.xml file change"""
        try:
            # Skip if our own API write is in progress
            if self.api_write_in_progress:
                self._log("Skipping file change - API write in progress", xbmc.LOGDEBUG)
                return

            self._log("Processing favourites file change", xbmc.LOGINFO)

            # Parse current favourites from XML
            current_favorites = self._parse_favorites_xml()

            if current_favorites is None:
                self._log("Failed to parse favourites XML", xbmc.LOGWARNING)
                return

            self._log(f"Found {len(current_favorites)} favourites in XML", xbmc.LOGINFO)

            # Compare with previous state to detect changes
            if self.previous_favorites:
                changes = self._detect_favorites_changes(self.previous_favorites, current_favorites)
                if changes:
                    self._publish_favorites_changes(changes)
                else:
                    self._log("No favorites changes detected", xbmc.LOGDEBUG)
            else:
                # First run - just store current state, don't publish
                self._log("First favorites scan - storing initial state", xbmc.LOGINFO)

            # Store current state for next comparison
            self.previous_favorites = current_favorites.copy()

        except Exception as e:
            self._log(f"Error processing favourites change: {e}", xbmc.LOGERROR)

    def _detect_favorites_changes(self, previous: List[Dict], current: List[Dict]):
        """Detect what favorites were added (V3: add-only mode with anti-loop protection)"""
        try:
            # Create sets of titles for comparison
            prev_titles = set(fav.get('title', '') for fav in previous)
            curr_titles = set(fav.get('title', '') for fav in current)

            # V3: Only detect additions, ignore removals
            added_titles = curr_titles - prev_titles

            # Debug logging
            self._log(f"Previous: {len(prev_titles)} favorites", xbmc.LOGDEBUG)
            self._log(f"Current: {len(curr_titles)} favorites", xbmc.LOGDEBUG)
            if added_titles:
                self._log(f"New favorites: {list(added_titles)}", xbmc.LOGINFO)
            self._log("V3: Removals ignored (add-only mode)", xbmc.LOGINFO)

            changes = []

            # V3: Only process additions with anti-loop protection
            for favorite in current:
                title = favorite.get('title', '')
                if title in added_titles:
                    # Check anti-loop protection
                    if self._is_recently_received(title):
                        self._log(f"Skipping '{title}' - recently received (anti-loop)", xbmc.LOGDEBUG)
                        continue

                    changes.append({
                        'action': 'add',
                        'favorite': favorite
                    })

            # Detected changes (removed verbose log)
            return changes

        except Exception as e:
            self._log(f"Error detecting favorites changes: {e}", xbmc.LOGERROR)
            return []

    def _publish_favorites_changes(self, changes: List[Dict]):
        """Publish individual favorite changes to MQTT (V3: add-only)"""
        try:
            device_id = self._get_device_id()
            timestamp = int(time.time())

            for change in changes:
                action = change.get('action')

                if action == 'add':
                    favorite = change.get('favorite', {})
                    payload = {
                        'device_id': device_id,
                        'timestamp': timestamp,
                        'content': {
                            'action': 'add',
                            'title': favorite.get('title', ''),
                            'xml_content': favorite.get('xml_content', ''),
                            'thumbnail': favorite.get('thumbnail', '')
                        }
                    }
                    topic = "cloudsync/favorites/add"

                    self._log(f"V3: Publishing favorite add: {payload['content'].get('title', 'Unknown')}", xbmc.LOGINFO)

                    if self.mqtt_publish(topic, payload):
                        self._log(f"Favorite add published successfully", xbmc.LOGINFO)
                    else:
                        self._log(f"Failed to publish favorite add", xbmc.LOGWARNING)

                # V3: Remove operations are ignored in add-only mode

        except Exception as e:
            self._log(f"Error publishing favorites changes: {e}", xbmc.LOGERROR)

    def _get_device_id(self):
        """Get unique device identifier (same as MQTT client)"""
        try:
            import xbmcaddon
            addon = xbmcaddon.Addon('service.cloudsync')
            device_id = addon.getSetting('mqtt_device_id')
            return device_id if device_id else "unknown"
        except Exception:
            return "unknown"

    def _parse_favorites_xml(self) -> Optional[List[Dict]]:
        """Parse favourites.xml and return list of favorites"""
        try:
            if not os.path.exists(self.favorites_path):
                self._log("Favourites.xml does not exist", xbmc.LOGDEBUG)
                return []

            # Parse XML
            tree = ET.parse(self.favorites_path)
            root = tree.getroot()

            favorites = []

            for fav_elem in root.findall('favourite'):
                # Extract attributes
                title = fav_elem.get('name', '')
                thumb = fav_elem.get('thumb', '')

                # Extract content (the action)
                content = fav_elem.text or ''
                content = content.strip()

                # Create favorite dict with title-only key strategy
                favorite = {
                    'title': title,
                    'xml_content': content,
                    'thumbnail': thumb,
                    'xml_element': ET.tostring(fav_elem, encoding='unicode').strip()
                }

                favorites.append(favorite)

            return favorites

        except Exception as e:
            self._log(f"Error parsing favourites XML: {e}", xbmc.LOGERROR)
            return None

    def get_favorite_key(self, favorite: Dict) -> str:
        """Generate stable key for favorite - title only approach"""
        return favorite.get('title', '')

    def set_api_write_flag(self, in_progress: bool):
        """Set API write flag to prevent loop detection"""
        self.api_write_in_progress = in_progress
        if in_progress:
            self._log("API write started - ignoring file changes", xbmc.LOGDEBUG)
        else:
            self._log("API write finished - resuming file monitoring", xbmc.LOGDEBUG)

    def mark_favorite_as_received(self, title: str):
        """Mark favorite as recently received to prevent loop broadcasting"""
        current_time = time.time()
        self.recently_received_favorites[title] = current_time
        self._log(f"Marked '{title}' as recently received (anti-loop)", xbmc.LOGDEBUG)

    def _is_recently_received(self, title: str) -> bool:
        """Check if favorite was recently received from MQTT (anti-loop protection)"""
        current_time = time.time()

        # Clean up old entries first
        self._cleanup_old_received_favorites(current_time)

        # Check if this title was recently received
        if title in self.recently_received_favorites:
            received_time = self.recently_received_favorites[title]
            if current_time - received_time < self.anti_loop_grace_period:
                self._log(f"Skipping broadcast for '{title}' - recently received ({current_time - received_time:.1f}s ago)", xbmc.LOGDEBUG)
                return True

        return False

    def _cleanup_old_received_favorites(self, current_time: float):
        """Remove old entries from recently received favorites"""
        expired_titles = []
        for title, received_time in self.recently_received_favorites.items():
            if current_time - received_time >= self.anti_loop_grace_period:
                expired_titles.append(title)

        for title in expired_titles:
            del self.recently_received_favorites[title]