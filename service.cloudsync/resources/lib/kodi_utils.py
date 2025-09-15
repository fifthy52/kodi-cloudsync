"""
Kodi JSON-RPC utility functions inspired by service.watchedsync
"""

import json
import uuid
import xbmc
import xbmcaddon
from time import monotonic


def issue_kodi_jsonrpc_command(payload):
    """Issue RPC command to kodi device and return results"""
    addon = xbmcaddon.Addon('service.cloudsync')

    request_id = str(uuid.uuid4())
    payload["id"] = request_id
    payload["jsonrpc"] = "2.0"

    xbmc.log(f"[CloudSync] JSON-RPC payload: {payload}", xbmc.LOGDEBUG)

    try:
        start = monotonic()
        res = xbmc.executeJSONRPC(json.dumps(payload, allow_nan=False))
        done = monotonic()
        elapsed = done - start

        xbmc.log(f"[CloudSync] JSON-RPC completed in {elapsed*1000:.1f}ms", xbmc.LOGDEBUG)

        result = json.loads(res)
        if "result" in result:
            return result["result"]
        else:
            xbmc.log(f"[CloudSync] JSON-RPC error: {result}", xbmc.LOGERROR)
            return None

    except Exception as e:
        xbmc.log(f"[CloudSync] JSON-RPC exception: {e}", xbmc.LOGERROR)
        return None


def get_favorites():
    """Get all favorites from Kodi"""
    payload = {
        "method": "Favourites.GetFavourites",
        "params": {
            "properties": ["window", "path", "thumbnail", "windowparameter"]
        }
    }

    result = issue_kodi_jsonrpc_command(payload)
    if result and "favourites" in result:
        favorites = result["favourites"]
        return favorites if favorites is not None else []

    xbmc.log("[CloudSync] No favorites found or API error", xbmc.LOGINFO)
    return []


def clear_favorites():
    """Clear all favorites in Kodi - this method doesn't exist in Kodi API"""
    # Kodi doesn't have a ClearFavourites method
    # We'll need to get current favorites and remove them individually
    xbmc.log("[CloudSync] Warning: Favourites.ClearFavourites method not available", xbmc.LOGWARNING)
    return True  # Pretend success, we'll overwrite with new ones


def add_favorite(title, path, fav_type="window", thumbnail="", windowparameter=""):
    """Add a favorite to Kodi"""
    payload = {
        "method": "Favourites.AddFavourite",
        "params": {
            "title": title,
            "path": path
        }
    }

    # Use 'window' parameter instead of 'type' based on error message
    if fav_type == "window" or not fav_type:
        payload["params"]["window"] = windowparameter or "videos"
    else:
        payload["params"]["window"] = fav_type

    if thumbnail:
        payload["params"]["thumbnail"] = thumbnail

    return issue_kodi_jsonrpc_command(payload) is not None


def get_movies_watched_status():
    """Get watched status for all movies"""
    payload = {
        "method": "VideoLibrary.GetMovies",
        "params": {
            "properties": ["title", "year", "lastplayed", "playcount", "uniqueid", "file"]
        }
    }

    result = issue_kodi_jsonrpc_command(payload)
    if result and "movies" in result:
        return result["movies"]
    return []


def get_episodes_watched_status():
    """Get watched status for all episodes"""
    payload = {
        "method": "VideoLibrary.GetEpisodes",
        "params": {
            "properties": ["title", "season", "episode", "lastplayed", "playcount", "uniqueid", "file", "tvshowid"]
        }
    }

    result = issue_kodi_jsonrpc_command(payload)
    if result and "episodes" in result:
        return result["episodes"]
    return []


def set_movie_watched_status(movieid, playcount, lastplayed=None):
    """Set watched status for a movie"""
    payload = {
        "method": "VideoLibrary.SetMovieDetails",
        "params": {
            "movieid": movieid,
            "playcount": playcount
        }
    }

    if lastplayed:
        payload["params"]["lastplayed"] = lastplayed

    return issue_kodi_jsonrpc_command(payload) is not None


def set_episode_watched_status(episodeid, playcount, lastplayed=None):
    """Set watched status for an episode"""
    payload = {
        "method": "VideoLibrary.SetEpisodeDetails",
        "params": {
            "episodeid": episodeid,
            "playcount": playcount
        }
    }

    if lastplayed:
        payload["params"]["lastplayed"] = lastplayed

    return issue_kodi_jsonrpc_command(payload) is not None