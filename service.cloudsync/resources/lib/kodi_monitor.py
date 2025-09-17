#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CloudSync V2 - Kodi Event Monitor
Monitor Kodi events and trigger MQTT sync
"""

import json
import xbmc
from typing import Optional, Callable
from kodi_rpc import KodiRPC


class CloudSyncMonitor(xbmc.Monitor):
    """Monitor Kodi events for CloudSync V2"""

    def __init__(self, mqtt_publish_callback: Callable = None):
        super().__init__()
        self.kodi_rpc = KodiRPC()
        self.mqtt_publish = mqtt_publish_callback
        self.last_played_item = None

    def _log(self, message: str, level: int = xbmc.LOGINFO):
        """Centralized logging"""
        xbmc.log(f"CloudSync V2 Monitor: {message}", level)

    def onNotification(self, sender: str, method: str, data: str):
        """Handle Kodi notifications"""
        try:
            self._log(f"Notification received: {sender} - {method}", xbmc.LOGINFO)

            if not self.mqtt_publish:
                self._log("No MQTT publish callback available", xbmc.LOGWARNING)
                return

            # Parse notification data
            try:
                notification_data = json.loads(data) if data else {}
            except:
                notification_data = {}

            # Handle different notification types
            if method == "VideoLibrary.OnUpdate":
                self._log(f"VideoLibrary update notification: {notification_data}", xbmc.LOGINFO)
                self._handle_library_update(notification_data)
            elif method == "Player.OnPlay":
                self._log(f"Player play notification: {notification_data}", xbmc.LOGINFO)
                self._handle_player_play(notification_data)
            elif method == "Player.OnStop":
                self._log(f"Player stop notification: {notification_data}", xbmc.LOGINFO)
                self._handle_player_stop(notification_data)
            else:
                self._log(f"Unhandled notification: {method}", xbmc.LOGINFO)

        except Exception as e:
            self._log(f"Error handling notification {method}: {e}", xbmc.LOGERROR)

    def _handle_library_update(self, data: dict):
        """Handle video library update notification"""
        try:
            item = data.get("item", {})
            item_type = item.get("type")
            item_id = item.get("id")

            if not item_type or not item_id:
                return

            self._log(f"Library update: {item_type} ID {item_id}", xbmc.LOGINFO)

            # Check if this is a watched status change
            if item_type == "movie":
                self._check_movie_watched_change(item_id)
            elif item_type == "episode":
                self._check_episode_watched_change(item_id)

        except Exception as e:
            self._log(f"Error handling library update: {e}", xbmc.LOGERROR)

    def _check_movie_watched_change(self, movie_id: int):
        """Check if movie watched status changed"""
        try:
            self._log(f"Checking movie watched change for ID: {movie_id}", xbmc.LOGINFO)

            movie_details = self.kodi_rpc.get_movie_details(movie_id)
            if not movie_details:
                self._log(f"No movie details found for ID: {movie_id}", xbmc.LOGWARNING)
                return

            self._log(f"Movie details retrieved: {movie_details.get('title', 'Unknown')}", xbmc.LOGINFO)

            # Publish watched status change
            self._publish_movie_watched(movie_details)

        except Exception as e:
            self._log(f"Error checking movie watched change: {e}", xbmc.LOGERROR)

    def _check_episode_watched_change(self, episode_id: int):
        """Check if episode watched status changed"""
        try:
            episode_details = self.kodi_rpc.get_episode_details(episode_id)
            if not episode_details:
                return

            # Get TV show details for show unique ID
            tvshow_id = episode_details.get("tvshowid")
            if tvshow_id:
                show_details = self.kodi_rpc.get_tvshow_details(tvshow_id)
                if show_details:
                    episode_details["show_uniqueid"] = show_details.get("uniqueid", {})

            # Publish watched status change
            self._publish_episode_watched(episode_details)

        except Exception as e:
            self._log(f"Error checking episode watched change: {e}", xbmc.LOGERROR)

    def _publish_movie_watched(self, movie_details: dict):
        """Publish movie watched status to MQTT"""
        try:
            title = movie_details.get("title", "Unknown")
            uniqueid = movie_details.get("uniqueid", {})
            playcount = movie_details.get("playcount", 0)

            self._log(f"Publishing movie watched: {title}, uniqueid: {uniqueid}, playcount: {playcount}", xbmc.LOGINFO)

            if not uniqueid:
                self._log(f"No unique ID for movie: {title}", xbmc.LOGWARNING)
                return

            topic = f"cloudsync/watched/{uniqueid.get('imdb', uniqueid.get('tmdb', 'unknown'))}"

            payload = {
                "content": {
                    "type": "movie",
                    "title": title,
                    "uniqueid": uniqueid,
                    "playcount": playcount,
                    "year": movie_details.get("year")
                }
            }

            self._log(f"MQTT topic: {topic}", xbmc.LOGINFO)

            if self.mqtt_publish:
                result = self.mqtt_publish(topic, payload)
                self._log(f"MQTT publish result: {result}", xbmc.LOGINFO)
            else:
                self._log("No MQTT publish callback!", xbmc.LOGERROR)

            self._log(f"Published movie watched status: {title} (playcount={playcount})", xbmc.LOGINFO)

        except Exception as e:
            self._log(f"Error publishing movie watched status: {e}", xbmc.LOGERROR)

    def _publish_episode_watched(self, episode_details: dict):
        """Publish episode watched status to MQTT"""
        try:
            title = episode_details.get("title", "Unknown")
            show_title = episode_details.get("showtitle", "Unknown")
            season = episode_details.get("season", 0)
            episode = episode_details.get("episode", 0)
            uniqueid = episode_details.get("uniqueid", {})
            show_uniqueid = episode_details.get("show_uniqueid", {})
            playcount = episode_details.get("playcount", 0)

            if not show_uniqueid:
                self._log(f"No show unique ID for episode: {show_title} - {title}", xbmc.LOGWARNING)
                return

            # Use show's main unique ID for topic
            show_id = show_uniqueid.get('imdb', show_uniqueid.get('tvdb', show_uniqueid.get('tmdb', 'unknown')))
            topic = f"cloudsync/watched/{show_id}_S{season:02d}E{episode:02d}"

            payload = {
                "content": {
                    "type": "episode",
                    "title": title,
                    "showtitle": show_title,
                    "season": season,
                    "episode": episode,
                    "uniqueid": uniqueid,
                    "show_uniqueid": show_uniqueid,
                    "playcount": playcount
                }
            }

            self.mqtt_publish(topic, payload)
            self._log(f"Published episode watched status: {show_title} S{season}E{episode} (playcount={playcount})", xbmc.LOGINFO)

        except Exception as e:
            self._log(f"Error publishing episode watched status: {e}", xbmc.LOGERROR)

    def _handle_player_play(self, data: dict):
        """Handle player play notification"""
        try:
            item = data.get("item", {})
            self.last_played_item = item
            self._log(f"Player started: {item.get('type', 'unknown')}", xbmc.LOGINFO)

        except Exception as e:
            self._log(f"Error handling player play: {e}", xbmc.LOGERROR)

    def _handle_player_stop(self, data: dict):
        """Handle player stop notification"""
        try:
            # When player stops, check for resume point changes
            if self.last_played_item:
                item_type = self.last_played_item.get("type")
                item_id = self.last_played_item.get("id")

                if item_type == "movie" and item_id:
                    self._check_movie_resume_change(item_id)
                elif item_type == "episode" and item_id:
                    self._check_episode_resume_change(item_id)

            self.last_played_item = None

        except Exception as e:
            self._log(f"Error handling player stop: {e}", xbmc.LOGERROR)

    def _check_movie_resume_change(self, movie_id: int):
        """Check if movie resume point changed"""
        try:
            movie_details = self.kodi_rpc.get_movie_details(movie_id)
            if not movie_details:
                return

            resume = movie_details.get("resume", {})
            if resume.get("position", 0) > 0:
                self._publish_movie_resume(movie_details)

        except Exception as e:
            self._log(f"Error checking movie resume change: {e}", xbmc.LOGERROR)

    def _check_episode_resume_change(self, episode_id: int):
        """Check if episode resume point changed"""
        try:
            episode_details = self.kodi_rpc.get_episode_details(episode_id)
            if not episode_details:
                return

            # Get show details
            tvshow_id = episode_details.get("tvshowid")
            if tvshow_id:
                show_details = self.kodi_rpc.get_tvshow_details(tvshow_id)
                if show_details:
                    episode_details["show_uniqueid"] = show_details.get("uniqueid", {})

            resume = episode_details.get("resume", {})
            if resume.get("position", 0) > 0:
                self._publish_episode_resume(episode_details)

        except Exception as e:
            self._log(f"Error checking episode resume change: {e}", xbmc.LOGERROR)

    def _publish_movie_resume(self, movie_details: dict):
        """Publish movie resume point to MQTT"""
        try:
            title = movie_details.get("title", "Unknown")
            uniqueid = movie_details.get("uniqueid", {})
            resume = movie_details.get("resume", {})

            if not uniqueid or not resume.get("position"):
                return

            topic = f"cloudsync/resume/{uniqueid.get('imdb', uniqueid.get('tmdb', 'unknown'))}"

            payload = {
                "content": {
                    "type": "movie",
                    "title": title,
                    "uniqueid": uniqueid,
                    "resume": {
                        "position": resume.get("position", 0),
                        "total": resume.get("total", 0)
                    }
                }
            }

            self.mqtt_publish(topic, payload)
            self._log(f"Published movie resume point: {title} ({resume.get('position')}s)", xbmc.LOGINFO)

        except Exception as e:
            self._log(f"Error publishing movie resume point: {e}", xbmc.LOGERROR)

    def _publish_episode_resume(self, episode_details: dict):
        """Publish episode resume point to MQTT"""
        try:
            title = episode_details.get("title", "Unknown")
            show_title = episode_details.get("showtitle", "Unknown")
            season = episode_details.get("season", 0)
            episode = episode_details.get("episode", 0)
            show_uniqueid = episode_details.get("show_uniqueid", {})
            resume = episode_details.get("resume", {})

            if not show_uniqueid or not resume.get("position"):
                return

            show_id = show_uniqueid.get('imdb', show_uniqueid.get('tvdb', show_uniqueid.get('tmdb', 'unknown')))
            topic = f"cloudsync/resume/{show_id}_S{season:02d}E{episode:02d}"

            payload = {
                "content": {
                    "type": "episode",
                    "title": title,
                    "showtitle": show_title,
                    "season": season,
                    "episode": episode,
                    "show_uniqueid": show_uniqueid,
                    "resume": {
                        "position": resume.get("position", 0),
                        "total": resume.get("total", 0)
                    }
                }
            }

            self.mqtt_publish(topic, payload)
            self._log(f"Published episode resume point: {show_title} S{season}E{episode} ({resume.get('position')}s)", xbmc.LOGINFO)

        except Exception as e:
            self._log(f"Error publishing episode resume point: {e}", xbmc.LOGERROR)