#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CloudSync V2 - Kodi JSON-RPC Wrapper
Clean interface for Kodi library operations
"""

import json
import time
import xbmc
import xbmcvfs
from typing import Dict, Any, List, Optional


class KodiRPC:
    """Kodi JSON-RPC wrapper for CloudSync V2"""

    def __init__(self):
        pass

    def _log(self, message: str, level: int = xbmc.LOGINFO):
        """Centralized logging"""
        xbmc.log(f"CloudSync V2 RPC: {message}", level)

    def _execute_rpc(self, method: str, params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Execute JSON-RPC command"""
        try:
            request = {
                "jsonrpc": "2.0",
                "method": method,
                "id": 1
            }

            if params:
                request["params"] = params

            response = xbmc.executeJSONRPC(json.dumps(request))
            result = json.loads(response)

            if "error" in result:
                self._log(f"RPC error in {method}: {result['error']}", xbmc.LOGERROR)
                return None

            return result.get("result")

        except Exception as e:
            self._log(f"Exception in RPC {method}: {e}", xbmc.LOGERROR)
            return None

    def get_movie_details(self, movie_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed movie information"""
        params = {
            "movieid": movie_id,
            "properties": [
                "title", "year", "imdbnumber", "uniqueid", "playcount",
                "lastplayed", "resume", "file", "dateadded"
            ]
        }

        result = self._execute_rpc("VideoLibrary.GetMovieDetails", params)
        return result.get("moviedetails") if result else None

    def get_episode_details(self, episode_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed episode information"""
        params = {
            "episodeid": episode_id,
            "properties": [
                "title", "season", "episode", "showtitle", "tvshowid",
                "uniqueid", "playcount", "lastplayed", "resume", "file", "dateadded"
            ]
        }

        result = self._execute_rpc("VideoLibrary.GetEpisodeDetails", params)
        return result.get("episodedetails") if result else None

    def get_tvshow_details(self, tvshow_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed TV show information"""
        params = {
            "tvshowid": tvshow_id,
            "properties": [
                "title", "year", "imdbnumber", "uniqueid", "playcount",
                "lastplayed", "dateadded"
            ]
        }

        result = self._execute_rpc("VideoLibrary.GetTVShowDetails", params)
        return result.get("tvshowdetails") if result else None

    def set_movie_playcount(self, movie_id: int, playcount: int) -> bool:
        """Set movie play count"""
        params = {
            "movieid": movie_id,
            "playcount": playcount
        }

        result = self._execute_rpc("VideoLibrary.SetMovieDetails", params)
        return result is not None

    def set_episode_playcount(self, episode_id: int, playcount: int) -> bool:
        """Set episode play count"""
        params = {
            "episodeid": episode_id,
            "playcount": playcount
        }

        result = self._execute_rpc("VideoLibrary.SetEpisodeDetails", params)
        return result is not None

    def set_movie_resume(self, movie_id: int, position: float, total: float) -> bool:
        """Set movie resume point"""
        params = {
            "movieid": movie_id,
            "resume": {
                "position": position,
                "total": total
            }
        }

        result = self._execute_rpc("VideoLibrary.SetMovieDetails", params)
        return result is not None

    def set_episode_resume(self, episode_id: int, position: float, total: float) -> bool:
        """Set episode resume point"""
        params = {
            "episodeid": episode_id,
            "resume": {
                "position": position,
                "total": total
            }
        }

        result = self._execute_rpc("VideoLibrary.SetEpisodeDetails", params)
        return result is not None

    def find_movie_by_uniqueid(self, uniqueid: Dict[str, str]) -> Optional[int]:
        """Find movie by unique ID (IMDB, TMDB, etc.)"""
        try:
            # Get all movies
            params = {
                "properties": ["uniqueid"]
            }

            result = self._execute_rpc("VideoLibrary.GetMovies", params)
            if not result or "movies" not in result:
                return None

            # Search for matching unique ID
            for movie in result["movies"]:
                movie_uniqueid = movie.get("uniqueid", {})

                # Check for any matching unique ID
                for id_type, id_value in uniqueid.items():
                    if movie_uniqueid.get(id_type) == id_value:
                        return movie["movieid"]

            return None

        except Exception as e:
            self._log(f"Error finding movie by uniqueid: {e}", xbmc.LOGERROR)
            return None

    def find_episode_by_show_and_episode(self, show_uniqueid: Dict[str, str],
                                       season: int, episode: int) -> Optional[int]:
        """Find episode by show unique ID and season/episode numbers"""
        try:
            # First find the TV show
            tvshow_id = self.find_tvshow_by_uniqueid(show_uniqueid)
            if not tvshow_id:
                return None

            # Get episodes for this show
            params = {
                "tvshowid": tvshow_id,
                "properties": ["season", "episode"]
            }

            result = self._execute_rpc("VideoLibrary.GetEpisodes", params)
            if not result or "episodes" not in result:
                return None

            # Find matching episode
            for ep in result["episodes"]:
                if ep.get("season") == season and ep.get("episode") == episode:
                    return ep["episodeid"]

            return None

        except Exception as e:
            self._log(f"Error finding episode: {e}", xbmc.LOGERROR)
            return None

    def find_tvshow_by_uniqueid(self, uniqueid: Dict[str, str]) -> Optional[int]:
        """Find TV show by unique ID"""
        try:
            # Get all TV shows
            params = {
                "properties": ["uniqueid"]
            }

            result = self._execute_rpc("VideoLibrary.GetTVShows", params)
            if not result or "tvshows" not in result:
                return None

            # Search for matching unique ID
            for show in result["tvshows"]:
                show_uniqueid = show.get("uniqueid", {})

                # Check for any matching unique ID
                for id_type, id_value in uniqueid.items():
                    if show_uniqueid.get(id_type) == id_value:
                        return show["tvshowid"]

            return None

        except Exception as e:
            self._log(f"Error finding TV show by uniqueid: {e}", xbmc.LOGERROR)
            return None

    def get_favourites(self) -> List[Dict[str, Any]]:
        """Get all favorites"""
        result = self._execute_rpc("Favourites.GetFavourites")
        return result.get("favourites", []) if result else []

    def debug_favourites_api(self):
        """Debug different Favourites API calls to find all available data"""
        self._log("=== FAVOURITES API DEBUG TEST ===", xbmc.LOGINFO)

        # Test 1: Basic call
        self._log("1. Basic GetFavourites:", xbmc.LOGINFO)
        result1 = self._execute_rpc("Favourites.GetFavourites")
        self._log(f"Basic result: {result1}", xbmc.LOGINFO)

        # Test 2: With various properties
        properties_tests = [
            ["title", "path", "thumbnail"],
            ["title", "path", "thumbnail", "window", "windowparameter"],
            ["title", "type", "path", "thumbnail", "window", "windowparameter"],
        ]

        for i, props in enumerate(properties_tests, 2):
            self._log(f"{i}. GetFavourites with properties {props}:", xbmc.LOGINFO)
            params = {"properties": props}
            result = self._execute_rpc("Favourites.GetFavourites", params)
            self._log(f"Properties result: {result}", xbmc.LOGINFO)

        self._log("=== END FAVOURITES API DEBUG ===", xbmc.LOGINFO)

    def debug_single_favorite_structure(self):
        """Debug the exact structure of a single favorite from API"""
        self._log("=== SINGLE FAVORITE DEBUG ===", xbmc.LOGINFO)

        favorites = self.get_favourites()
        if favorites:
            fav = favorites[0]
            self._log(f"First favorite keys: {list(fav.keys())}", xbmc.LOGINFO)
            self._log(f"First favorite data: {fav}", xbmc.LOGINFO)

        self._log("=== END SINGLE FAVORITE DEBUG ===", xbmc.LOGINFO)

    def add_favourite(self, title: str, type_name: str, path: str, thumbnail: str = "",
                     window: str = "", windowparameter: str = "") -> bool:
        """Add item to favorites"""
        params = {
            "title": title,
            "type": type_name
        }

        # Add path OR window/windowparameter based on format
        if path:
            params["path"] = path

        if thumbnail:
            params["thumbnail"] = thumbnail

        # Add window parameters if available
        if window:
            params["window"] = window
        if windowparameter:
            params["windowparameter"] = windowparameter

        result = self._execute_rpc("Favourites.AddFavourite", params)
        return result is not None

    def add_favorite(self, title: str, xml_content: str, thumbnail: str = "") -> bool:
        """Add favorite using XML content (simplified interface)"""
        try:
            self._log(f"Adding favorite: {title} with XML: {xml_content[:100]}...", xbmc.LOGINFO)

            # Parse XML content to determine type and parameters
            if xml_content.startswith('PlayMedia('):
                # Media type - extract path from PlayMedia("path")
                # Handle both quoted and unquoted paths
                if xml_content.startswith('PlayMedia("') and xml_content.endswith('")'):
                    path = xml_content[len('PlayMedia("'):-len('")')]
                elif xml_content.startswith('PlayMedia(') and xml_content.endswith(')'):
                    path = xml_content[len('PlayMedia('):-len(')')]
                    # Remove quotes if present
                    if path.startswith('"') and path.endswith('"'):
                        path = path[1:-1]
                else:
                    path = xml_content

                self._log(f"Media favorite - path: {path}", xbmc.LOGINFO)
                return self.add_favourite(title, "media", path, thumbnail)

            elif xml_content.startswith('ActivateWindow('):
                # Window type - extract window and windowparameter
                # Format: ActivateWindow(windowid,"parameter",return)
                content = xml_content[len('ActivateWindow('):-len(')')]
                parts = [p.strip() for p in content.split(',')]

                if len(parts) >= 1:
                    window = parts[0].strip()
                    windowparameter = ""

                    if len(parts) >= 2:
                        # Remove quotes from parameter
                        windowparameter = parts[1].strip().strip('"')

                    self._log(f"Window favorite - window: {window}, param: {windowparameter}", xbmc.LOGINFO)
                    return self.add_favourite(title, "window", "", thumbnail, window, windowparameter)

            else:
                # Fallback - try as media with full XML content as path
                self._log(f"Unknown XML content format, trying as media: {xml_content[:50]}...", xbmc.LOGWARNING)
                return self.add_favourite(title, "media", xml_content, thumbnail)

        except Exception as e:
            self._log(f"Error adding favorite {title}: {e}", xbmc.LOGERROR)
            return False

    def remove_favorite(self, title: str) -> bool:
        """Remove favorite by title"""
        try:
            self._log(f"Removing favorite: {title}", xbmc.LOGINFO)

            # Get current favorites to verify it exists
            favorites = self.get_favourites()
            found_favorite = None

            for favorite in favorites:
                if favorite.get("title") == title:
                    found_favorite = favorite
                    break

            if not found_favorite:
                self._log(f"Favorite not found for removal: {title}", xbmc.LOGWARNING)
                return False

            # Remove from XML and try to trigger UI refresh with library scans
            self._log(f"Removing favorite from XML with library refresh: {title}", xbmc.LOGINFO)
            if self._remove_favorite_from_xml(title):
                # Try to trigger UI refresh using library scan methods
                self._notify_favorites_changed()
                return True
            else:
                return False

        except Exception as e:
            self._log(f"Error removing favorite {title}: {e}", xbmc.LOGERROR)
            return False

    def _remove_favorite_from_xml_with_api_refresh(self, title: str, favorite_data: dict) -> bool:
        """Remove favorite using XML + API trick to trigger UI refresh"""
        try:
            # Step 1: Remove from XML
            if not self._remove_favorite_from_xml(title):
                return False

            # Step 2: Add a temporary dummy favorite via API (triggers UI refresh)
            dummy_title = f"__temp_refresh_{int(time.time())}"
            self.add_favourite(dummy_title, "media", "plugin://dummy", "")

            # Step 3: Immediately remove the dummy favorite from XML
            # This should leave us with the original favorite removed + UI refreshed
            time.sleep(0.1)  # Brief delay
            self._remove_favorite_from_xml(dummy_title)

            self._log(f"Removed favorite with API refresh trick: {title}", xbmc.LOGINFO)
            return True

        except Exception as e:
            self._log(f"Error in API refresh trick: {e}", xbmc.LOGERROR)
            return False

    def _recreate_favorites_without(self, title_to_remove: str, current_favorites: list) -> bool:
        """Recreate favorites XML by clearing and re-adding all except the one to remove"""
        try:
            # Clear the XML file first
            if not self._clear_favorites_xml():
                return False

            # Re-add all favorites except the one to remove
            added_count = 0
            for favorite in current_favorites:
                fav_title = favorite.get("title", "")
                if fav_title != title_to_remove:
                    # Extract favorite data
                    xml_content = favorite.get("path", "")
                    thumbnail = favorite.get("thumbnail", "")

                    # Use API to add it back
                    if self.add_favorite(fav_title, xml_content, thumbnail):
                        added_count += 1
                    else:
                        self._log(f"Failed to re-add favorite: {fav_title}", xbmc.LOGWARNING)

            self._log(f"Recreated {added_count} favorites (removed: {title_to_remove})", xbmc.LOGINFO)
            return True

        except Exception as e:
            self._log(f"Error recreating favorites: {e}", xbmc.LOGERROR)
            return False

    def _clear_favorites_xml(self) -> bool:
        """Clear all favorites from XML file"""
        try:
            import xml.etree.ElementTree as ET
            import os

            # Get platform-independent favourites.xml path
            try:
                try:
                    userdata_path = xbmcvfs.translatePath('special://userdata/')
                except AttributeError:
                    userdata_path = xbmc.translatePath('special://userdata/')

                favorites_path = os.path.join(userdata_path, 'favourites.xml')
            except Exception as e:
                self._log(f"Error getting favourites path: {e}", xbmc.LOGERROR)
                return False

            # Create empty favorites XML
            root = ET.Element("favourites")
            tree = ET.ElementTree(root)
            tree.write(favorites_path, encoding='utf-8', xml_declaration=True)

            self._log("Cleared favorites XML file", xbmc.LOGINFO)
            return True

        except Exception as e:
            self._log(f"Error clearing favorites XML: {e}", xbmc.LOGERROR)
            return False

    def _remove_favorite_from_xml(self, title: str) -> bool:
        """Remove favorite directly from favourites.xml file"""
        try:
            import xml.etree.ElementTree as ET
            import os

            # Get platform-independent favourites.xml path
            try:
                try:
                    userdata_path = xbmcvfs.translatePath('special://userdata/')
                except AttributeError:
                    userdata_path = xbmc.translatePath('special://userdata/')

                favorites_path = os.path.join(userdata_path, 'favourites.xml')
            except Exception as e:
                self._log(f"Error getting favourites path: {e}", xbmc.LOGERROR)
                return False

            if not os.path.exists(favorites_path):
                self._log(f"Favourites file does not exist: {favorites_path}", xbmc.LOGWARNING)
                return False

            # Parse XML
            tree = ET.parse(favorites_path)
            root = tree.getroot()

            # Find and remove the favorite
            removed = False
            for fav_elem in root.findall('favourite'):
                if fav_elem.get('name') == title:
                    root.remove(fav_elem)
                    removed = True
                    self._log(f"Removed favorite element: {title}", xbmc.LOGINFO)
                    break

            if not removed:
                self._log(f"Favorite element not found in XML: {title}", xbmc.LOGWARNING)
                return False

            # Write back to file
            tree.write(favorites_path, encoding='utf-8', xml_declaration=True)
            self._log(f"Successfully removed favorite from XML: {title}", xbmc.LOGINFO)

            # Try to notify Kodi about the favorites change
            self._notify_favorites_changed()

            return True

        except Exception as e:
            self._log(f"Error removing favorite from XML: {e}", xbmc.LOGERROR)
            return False

    def _notify_favorites_changed(self):
        """Notify Kodi that favorites have changed to trigger UI refresh"""
        try:
            self._log("Triggering favorites UI refresh", xbmc.LOGINFO)

            # For removal operations, we need builtin commands since there's no RemoveFavourite API
            # AddFavourite API automatically refreshes UI, but XML removal doesn't
            try:
                # Try multiple refresh approaches
                xbmc.executebuiltin("Container.Refresh")
                self._log("Executed Container.Refresh", xbmc.LOGDEBUG)
            except Exception as e:
                self._log(f"Container.Refresh failed: {e}", xbmc.LOGDEBUG)

            try:
                xbmc.executebuiltin("Container.Update(favourites://)")
                self._log("Executed Container.Update favourites", xbmc.LOGDEBUG)
            except Exception as e:
                self._log(f"Container.Update failed: {e}", xbmc.LOGDEBUG)

            # Optional: Send user notification
            try:
                params = {
                    "title": "CloudSync",
                    "message": "Favorites synced"
                }
                self._execute_rpc("GUI.ShowNotification", params)
                self._log("Sent favorites sync notification", xbmc.LOGDEBUG)
            except Exception as e:
                self._log(f"GUI.ShowNotification failed: {e}", xbmc.LOGDEBUG)

        except Exception as e:
            self._log(f"Error in favorites notification: {e}", xbmc.LOGERROR)

    def scan_video_library(self) -> bool:
        """Trigger video library scan"""
        result = self._execute_rpc("VideoLibrary.Scan")
        return result is not None

    def clean_video_library(self) -> bool:
        """Clean video library"""
        result = self._execute_rpc("VideoLibrary.Clean")
        return result is not None