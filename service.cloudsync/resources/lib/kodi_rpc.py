#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CloudSync V2 - Kodi JSON-RPC Wrapper
Clean interface for Kodi library operations
"""

import json
import xbmc
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

    def add_favourite(self, title: str, type_name: str, path: str, thumbnail: str = "") -> bool:
        """Add item to favorites"""
        params = {
            "title": title,
            "type": type_name,
            "path": path
        }

        if thumbnail:
            params["thumbnail"] = thumbnail

        result = self._execute_rpc("Favourites.AddFavourite", params)
        return result is not None

    def scan_video_library(self) -> bool:
        """Trigger video library scan"""
        result = self._execute_rpc("VideoLibrary.Scan")
        return result is not None

    def clean_video_library(self) -> bool:
        """Clean video library"""
        result = self._execute_rpc("VideoLibrary.Clean")
        return result is not None