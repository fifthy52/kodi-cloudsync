import json
import time
import sqlite3
import threading
from datetime import datetime
import xbmcaddon
from dropbox_provider_simple import DropboxProviderSimple
from file_change_tracker import FileChangeTracker
import xbmc


class HybridSyncManager:
    """Hybrid sync manager combining WatchedList approach with resume points."""

    def get_movieid_from_uniqueid(self, uniqueid_dict):
        """
        Return movieid from searching for matching at least one of the uniqueid keys in the supplied dict
        Based on WatchedSync addon approach

        :param uniqueid_dict: Dictionary with uniqueid mappings (imdb, tmdb, etc.)
        :return: movieid (int) or None
        """
        if not uniqueid_dict:
            return None

        request = {
            "jsonrpc": "2.0",
            "method": "VideoLibrary.GetMovies",
            "params": {
                "properties": ["uniqueid"]
            },
            "id": 1
        }

        response = json.loads(xbmc.executeJSONRPC(json.dumps(request)))

        if 'result' in response and 'movies' in response['result']:
            for movie in response['result']['movies']:
                if 'uniqueid' not in movie:
                    continue

                # Check if any uniqueid matches
                for key, value in uniqueid_dict.items():
                    if value and movie['uniqueid'].get(key) == value:
                        return movie['movieid']

        return None

    def __init__(self):
        self.addon = xbmcaddon.Addon('service.cloudsync')
        self.dropbox = None
        self.sync_lock = threading.Lock()
        self.monitor = xbmc.Monitor()
        self.change_tracker = FileChangeTracker()
        
        # Database paths
        self.local_db_path = None
        self.remote_db_path = None
        self.db_connection = None
        
        # Sync state
        self.last_sync_time = 0
        self.sync_in_progress = False
        
        # Settings
        self.dropbox_enabled = False
        self.sync_watched = True
        self.sync_resume = True
        self.sync_favorites_enabled = True
        self.sync_userdata_enabled = False
        self.use_compression = True
        self.conflict_resolution = 'newer'
    
    def initialize(self):
        """Initialize the hybrid sync manager."""
        try:
            self._update_settings()
            
            # Setup local database
            if not self._setup_local_database():
                return False

            # Cleanup orphaned file tracking data
            orphaned_count = self.change_tracker.cleanup_orphaned_tracking_data()
            if orphaned_count > 0:
                xbmc.log(f"[CloudSync] Cleaned up {orphaned_count} orphaned file tracking entries", xbmc.LOGINFO)
            
            # Initialize Dropbox if enabled
            if self.dropbox_enabled:
                self.dropbox = DropboxProviderSimple()
                
                if not self.dropbox.is_available():
                    xbmc.log("[CloudSync] Dropbox not available - continuing without cloud sync", xbmc.LOGWARNING)
                    return True
                
                if not self.dropbox.test_connection():
                    xbmc.log("[CloudSync] Dropbox connection failed", xbmc.LOGWARNING)
                    return True
                
                # Ensure sync folder exists
                self.dropbox.ensure_folder_exists()
                
                # Download remote database if exists
                self._download_remote_database()
            
            xbmc.log("[CloudSync] Hybrid sync manager initialized successfully", xbmc.LOGINFO)
            return True
            
        except Exception as e:
            xbmc.log(f"[CloudSync] Failed to initialize hybrid sync manager: {e}", xbmc.LOGERROR)
            return False
    
    def _setup_local_database(self):
        """Setup local SQLite database."""
        try:
            # Database in addon data directory
            try:
                # New Kodi versions
                import xbmcvfs
                data_dir = xbmcvfs.translatePath("special://profile/addon_data/service.cloudsync/")
                if not xbmcvfs.exists(data_dir):
                    xbmcvfs.mkdirs(data_dir)
            except:
                # Older Kodi versions - use fallback
                try:
                    data_dir = xbmc.translatePath("special://profile/addon_data/service.cloudsync/")
                    import os
                    os.makedirs(data_dir, exist_ok=True)
                except:
                    # Ultimate fallback
                    data_dir = "special://profile/addon_data/service.cloudsync/"
            
            self.local_db_path = data_dir + "cloudsync.db"
            
            # Connect and create tables - handle corrupted database
            try:
                self.db_connection = sqlite3.connect(self.local_db_path, check_same_thread=False)
                cursor = self.db_connection.cursor()
                # Test database integrity
                result = cursor.execute("PRAGMA integrity_check").fetchone()
                if result and result[0] != 'ok':
                    raise sqlite3.DatabaseError("Database integrity check failed")
            except (sqlite3.DatabaseError, sqlite3.OperationalError) as e:
                xbmc.log(f"[CloudSync] Database corrupted ({e}), recreating", xbmc.LOGWARNING)
                # Remove corrupted database and create new one
                try:
                    import os
                    if os.path.exists(self.local_db_path):
                        os.remove(self.local_db_path)
                except:
                    pass
                self.db_connection = sqlite3.connect(self.local_db_path, check_same_thread=False)
                cursor = self.db_connection.cursor()
            
            # Create tables
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS watched_movies (
                    imdb_id TEXT PRIMARY KEY,
                    title TEXT,
                    playcount INTEGER,
                    lastplayed TEXT,
                    lastchange INTEGER
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS watched_episodes (
                    tvdb_id INTEGER,
                    season INTEGER,
                    episode INTEGER,
                    playcount INTEGER,
                    lastplayed TEXT,
                    lastchange INTEGER,
                    PRIMARY KEY (tvdb_id, season, episode)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS resume_points (
                    file_path TEXT PRIMARY KEY,
                    position REAL,
                    total_time REAL,
                    lastchange INTEGER,
                    imdb_id TEXT,
                    tvdb_id INTEGER,
                    season INTEGER,
                    episode INTEGER
                )
            """)
            
            # Favorites are now synced as XML file, not database table
            
            self.db_connection.commit()
            xbmc.log("[CloudSync] Local database initialized", xbmc.LOGDEBUG)
            return True
            
        except Exception as e:
            xbmc.log(f"[CloudSync] Failed to setup local database: {e}", xbmc.LOGERROR)
            return False
    
    def _download_remote_database(self):
        """Download remote database from Dropbox."""
        if not self.dropbox:
            return
        
        try:
            # Download database file
            content = self.dropbox.download_file("cloudsync.db")
            if content:
                # Save to temporary location
                try:
                    import xbmcvfs
                    temp_path = xbmcvfs.translatePath("special://temp/cloudsync_remote.db")
                except:
                    temp_path = "special://temp/cloudsync_remote.db"
                
                with open(temp_path, 'wb') as f:
                    if isinstance(content, str):
                        f.write(content.encode('utf-8'))
                    else:
                        f.write(content)
                
                self.remote_db_path = temp_path
                xbmc.log("[CloudSync] Downloaded remote database", xbmc.LOGDEBUG)
                
                # Merge with local database would go here
                # For now, we'll just log that we have a remote database
                
            else:
                xbmc.log("[CloudSync] No remote database found", xbmc.LOGDEBUG)
                
        except Exception as e:
            xbmc.log(f"[CloudSync] Failed to download remote database: {e}", xbmc.LOGERROR)
    
    def perform_full_sync(self):
        """Perform complete synchronization."""
        try:
            # Simple sync progress check without nested locks
            if self.sync_in_progress:
                xbmc.log("[CloudSync] Sync already in progress", xbmc.LOGDEBUG)
                return False

            self.sync_in_progress = True
            xbmc.log("[CloudSync] Starting full sync", xbmc.LOGINFO)

            # Track if any changes were made
            changes_made = False
            remote_changes = False

            # Download from Dropbox first (get remote changes)
            if self.dropbox_enabled:
                remote_changes = self._download_and_merge_remote_data()
                if remote_changes:
                    changes_made = True

            # Sync from Kodi to local database - track changes
            xbmc.log("[CloudSync] Starting sync_watched_status", xbmc.LOGINFO)
            if self.sync_watched_status():
                changes_made = True

            xbmc.log("[CloudSync] Starting sync_resume_points", xbmc.LOGINFO)
            if self.sync_resume_points():
                changes_made = True

            xbmc.log("[CloudSync] Starting sync_favorites", xbmc.LOGINFO)
            if self.sync_favorites():
                changes_made = True

            xbmc.log("[CloudSync] Starting sync_userdata", xbmc.LOGINFO)
            if self.sync_userdata():
                changes_made = True

            # Only proceed with restore and upload if changes were made
            if changes_made:
                # Apply local database back to Kodi
                xbmc.log("[CloudSync] Starting restore to Kodi", xbmc.LOGINFO)
                self._restore_to_kodi()

                # Upload updated data to Dropbox
                xbmc.log("[CloudSync] Starting upload to Dropbox", xbmc.LOGINFO)
                if self.dropbox_enabled:
                    self.upload_to_dropbox()

                xbmc.log("[CloudSync] Full sync completed with changes", xbmc.LOGINFO)
            else:
                xbmc.log("[CloudSync] Full sync completed - no changes detected", xbmc.LOGINFO)

            return True

        except Exception as e:
            xbmc.log(f"[CloudSync] Error during full sync: {e}", xbmc.LOGERROR)
            return False
        finally:
            self.sync_in_progress = False
    
    def sync_watched_status(self):
        """Sync watched status from Kodi to local database."""
        if not self.sync_watched:
            return False

        try:
            cursor = self.db_connection.cursor()
            current_time = int(time.time())
            changes_made = False

            # Get watched movies from Kodi
            request = {
                "jsonrpc": "2.0",
                "method": "VideoLibrary.GetMovies",
                "params": {
                    "properties": ["playcount", "lastplayed", "file", "imdbnumber", "title", "year", "uniqueid"],
                    "filter": {"field": "playcount", "operator": "greaterthan", "value": "0"}
                },
                "id": 1
            }

            response = json.loads(xbmc.executeJSONRPC(json.dumps(request)))

            movies_found = 0
            if 'result' in response and 'movies' in response['result']:
                movies_found = len(response['result']['movies'])
                xbmc.log(f"[CloudSync] Found {movies_found} watched movies in Kodi", xbmc.LOGINFO)
                for movie in response['result']['movies']:
                    # Try to get a reliable identifier
                    movie_id = None
                    id_type = None

                    # Priority 1: IMDb ID
                    if movie.get('imdbnumber'):
                        movie_id = movie.get('imdbnumber')
                        id_type = 'imdb'
                    # Priority 2: TMDB from uniqueid
                    elif movie.get('uniqueid') and movie['uniqueid'].get('tmdb'):
                        movie_id = movie['uniqueid']['tmdb']
                        id_type = 'tmdb'
                    # Priority 3: Any other uniqueid
                    elif movie.get('uniqueid') and movie['uniqueid']:
                        # Get the first available ID
                        for uid_type, uid_value in movie['uniqueid'].items():
                            if uid_value:
                                movie_id = uid_value
                                id_type = uid_type
                                break
                    # Priority 4: Fallback to title+year
                    else:
                        title = movie.get('title', '')
                        year = movie.get('year', 0)
                        if title and year:
                            movie_id = f"{title}_{year}"
                            id_type = 'title_year'

                    if movie_id:
                        # Check if this is actually a change
                        cursor.execute("""
                            SELECT playcount, lastplayed FROM watched_movies WHERE imdb_id = ? OR movie_id = ?
                        """, (movie_id, movie_id))
                        existing = cursor.fetchone()

                        new_playcount = movie.get('playcount', 0)
                        new_lastplayed = movie.get('lastplayed', '')

                        # Only update if values actually changed
                        if not existing or existing[0] != new_playcount or existing[1] != new_lastplayed:
                            xbmc.log(f"[CloudSync] Updating watched status for: {movie.get('title', imdb_id)} (playcount: {existing[0] if existing else 'new'} -> {new_playcount})", xbmc.LOGINFO)
                            cursor.execute("""
                                INSERT OR REPLACE INTO watched_movies
                                (imdb_id, title, playcount, lastplayed, lastchange)
                                VALUES (?, ?, ?, ?, ?)
                            """, (
                                imdb_id,
                                movie.get('title', ''),
                                new_playcount,
                                new_lastplayed,
                                current_time
                            ))
                            changes_made = True

            if changes_made:
                self.db_connection.commit()
                xbmc.log(f"[CloudSync] Synchronized watched status to local database - {movies_found} movies checked", xbmc.LOGINFO)
            else:
                xbmc.log(f"[CloudSync] No changes in watched status - {movies_found} movies checked", xbmc.LOGINFO)

            return changes_made

        except Exception as e:
            xbmc.log(f"[CloudSync] Failed to sync watched status: {e}", xbmc.LOGERROR)
            return False
    
    def sync_resume_points(self):
        """Sync resume points from Kodi to local database."""
        if not self.sync_resume:
            return False

        try:
            cursor = self.db_connection.cursor()
            current_time = int(time.time())
            changes_made = False

            # Get movies with resume points
            request = {
                "jsonrpc": "2.0",
                "method": "VideoLibrary.GetMovies",
                "params": {
                    "properties": ["resume", "file", "imdbnumber"],
                    "filter": {"field": "inprogress", "operator": "true", "value": ""}
                },
                "id": 1
            }

            response = json.loads(xbmc.executeJSONRPC(json.dumps(request)))

            if 'result' in response and 'movies' in response['result']:
                for movie in response['result']['movies']:
                    resume = movie.get('resume', {})
                    position = resume.get('position', 0)
                    total = resume.get('total', 0)

                    if position > 0:
                        file_path = movie.get('file', '')

                        # Check if this is actually a change
                        cursor.execute("""
                            SELECT position, total_time FROM resume_points WHERE file_path = ?
                        """, (file_path,))
                        existing = cursor.fetchone()

                        # Only update if values actually changed
                        if not existing or existing[0] != position or existing[1] != total:
                            cursor.execute("""
                                INSERT OR REPLACE INTO resume_points
                                (file_path, position, total_time, lastchange, imdb_id)
                                VALUES (?, ?, ?, ?, ?)
                            """, (
                                file_path,
                                position,
                                total,
                                current_time,
                                movie.get('imdbnumber', '')
                            ))
                            changes_made = True

            if changes_made:
                self.db_connection.commit()
                xbmc.log("[CloudSync] Synchronized resume points to local database", xbmc.LOGDEBUG)
            else:
                xbmc.log("[CloudSync] No changes in resume points", xbmc.LOGDEBUG)

            return changes_made

        except Exception as e:
            xbmc.log(f"[CloudSync] Failed to sync resume points: {e}", xbmc.LOGERROR)
            return False
    
    def upload_to_dropbox(self):
        """Upload local database to Dropbox."""
        if not self.dropbox or not self.dropbox_enabled:
            return False
        
        try:
            xbmc.log("[CloudSync] Uploading database to Dropbox", xbmc.LOGDEBUG)
            
            # Read local database file
            with open(self.local_db_path, 'rb') as f:
                content = f.read()
            
            # Upload to Dropbox
            success = self.dropbox.upload_file("cloudsync.db", content)
            
            if success:
                self.last_sync_time = time.time()
                xbmc.log("[CloudSync] Successfully uploaded database to Dropbox", xbmc.LOGINFO)
                return True
            else:
                xbmc.log("[CloudSync] Failed to upload database to Dropbox", xbmc.LOGERROR)
                return False
                
        except Exception as e:
            xbmc.log(f"[CloudSync] Error uploading to Dropbox: {e}", xbmc.LOGERROR)
            return False
    
    def _update_settings(self):
        """Update settings from addon."""
        try:
            self.dropbox_enabled = self.addon.getSettingBool('dropbox_enabled')
            self.sync_watched = self.addon.getSettingBool('sync_watched')
            self.sync_resume = self.addon.getSettingBool('sync_resume_points')
            self.sync_favorites_enabled = self.addon.getSettingBool('sync_favorites')
            self.sync_userdata_enabled = self.addon.getSettingBool('sync_userdata')
            self.use_compression = self.addon.getSettingBool('use_compression') if self.addon.getSetting('use_compression') else True
            self.conflict_resolution = self.addon.getSetting('conflict_resolution') or 'newer'
            
        except Exception as e:
            xbmc.log(f"[CloudSync] Error updating settings: {e}", xbmc.LOGERROR)
    
    def cleanup(self):
        """Cleanup resources."""
        try:
            if self.db_connection:
                self.db_connection.close()
                
        except Exception as e:
            xbmc.log(f"[CloudSync] Error during cleanup: {e}", xbmc.LOGERROR)
    
    def _download_and_merge_remote_data(self):
        """Download remote database and merge with local data."""
        try:
            xbmc.log("[CloudSync] Downloading and merging remote data", xbmc.LOGDEBUG)

            # Download remote database
            remote_content = self.dropbox.download_file("cloudsync.db")
            if not remote_content:
                xbmc.log("[CloudSync] No remote database found", xbmc.LOGDEBUG)
                return False

            # Save remote database to temp file
            try:
                import xbmcvfs
                temp_path = xbmcvfs.translatePath("special://temp/cloudsync_remote.db")
            except:
                temp_path = xbmc.translatePath("special://temp/cloudsync_remote.db")

            with open(temp_path, 'wb') as f:
                if isinstance(remote_content, str):
                    f.write(remote_content.encode('utf-8'))
                else:
                    f.write(remote_content)

            # Merge remote data with local database
            changes_made = self._merge_remote_database(temp_path)

            # Cleanup temp file
            try:
                import os
                os.remove(temp_path)
            except:
                pass

            return changes_made

        except Exception as e:
            xbmc.log(f"[CloudSync] Error downloading/merging remote data: {e}", xbmc.LOGERROR)
            return False
    
    def _merge_remote_database(self, remote_db_path):
        """Merge remote database into local database."""
        try:
            remote_conn = sqlite3.connect(remote_db_path)
            remote_cursor = remote_conn.cursor()
            local_cursor = self.db_connection.cursor()
            changes_made = False

            # Merge watched movies (prefer newer lastchange timestamps)
            try:
                remote_cursor.execute("SELECT * FROM watched_movies")
                for row in remote_cursor.fetchall():
                    imdb_id, title, playcount, lastplayed, remote_lastchange = row

                    # Check if local version exists and compare timestamps
                    local_cursor.execute(
                        "SELECT lastchange FROM watched_movies WHERE imdb_id = ?",
                        (imdb_id,)
                    )
                    local_row = local_cursor.fetchone()

                    # If remote is newer or doesn't exist locally, update
                    if not local_row or local_row[0] < remote_lastchange:
                        local_cursor.execute("""
                            INSERT OR REPLACE INTO watched_movies
                            (imdb_id, title, playcount, lastplayed, lastchange)
                            VALUES (?, ?, ?, ?, ?)
                        """, (imdb_id, title, playcount, lastplayed, remote_lastchange))
                        xbmc.log(f"[CloudSync] Merged remote movie: {title}", xbmc.LOGDEBUG)
                        changes_made = True
            except sqlite3.OperationalError:
                pass  # Table might not exist in remote DB

            # Merge resume points (prefer higher position = more progress)
            try:
                remote_cursor.execute("SELECT * FROM resume_points")
                for row in remote_cursor.fetchall():
                    file_path, position, total_time, remote_lastchange, imdb_id, tvdb_id, season, episode = row

                    # Check local version
                    local_cursor.execute(
                        "SELECT position, lastchange FROM resume_points WHERE file_path = ?",
                        (file_path,)
                    )
                    local_row = local_cursor.fetchone()

                    # Use remote if: doesn't exist locally, remote is newer, or remote has higher position
                    should_update = False
                    if not local_row:
                        should_update = True
                    elif local_row[1] < remote_lastchange:  # Remote is newer
                        should_update = True
                    elif position > local_row[0]:  # Remote has more progress
                        should_update = True

                    if should_update:
                        local_cursor.execute("""
                            INSERT OR REPLACE INTO resume_points
                            (file_path, position, total_time, lastchange, imdb_id, tvdb_id, season, episode)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (file_path, position, total_time, remote_lastchange, imdb_id, tvdb_id, season, episode))
                        xbmc.log(f"[CloudSync] Merged remote resume point: {file_path} at {position}s", xbmc.LOGDEBUG)
                        changes_made = True
            except sqlite3.OperationalError:
                pass

            # Favorites are now synced as XML file, not through database

            if changes_made:
                self.db_connection.commit()
                xbmc.log("[CloudSync] Successfully merged remote database", xbmc.LOGINFO)
            else:
                xbmc.log("[CloudSync] No changes from remote database merge", xbmc.LOGDEBUG)

            remote_conn.close()
            return changes_made

        except Exception as e:
            xbmc.log(f"[CloudSync] Error merging remote database: {e}", xbmc.LOGERROR)
            return False
    
    def _restore_to_kodi(self):
        """Restore data from local database back to Kodi."""
        try:
            xbmc.log("[CloudSync] Restoring data to Kodi", xbmc.LOGDEBUG)
            
            # Restore watched status
            self._restore_watched_status()
            
            # Restore resume points  
            self._restore_resume_points()
            
            # Restore favorites
            self._restore_favorites()
            
            xbmc.log("[CloudSync] Data restoration to Kodi completed", xbmc.LOGINFO)
            
        except Exception as e:
            xbmc.log(f"[CloudSync] Error restoring to Kodi: {e}", xbmc.LOGERROR)
    
    def _restore_watched_status(self):
        """Restore watched status from local database to Kodi."""
        try:
            cursor = self.db_connection.cursor()
            
            # Get all watched movies from local database
            cursor.execute("SELECT imdb_id, playcount FROM watched_movies WHERE playcount > 0")
            watched_movies = cursor.fetchall()
            
            for imdb_id, playcount in watched_movies:
                # Find movie in Kodi database by IMDB ID and mark as watched
                request = {
                    "jsonrpc": "2.0",
                    "method": "VideoLibrary.SetMovieDetails",
                    "params": {
                        "movieid": None,  # We need to find this first
                        "playcount": playcount
                    },
                    "id": 1
                }
                
                # First, find the movie ID by IMDB number
                find_request = {
                    "jsonrpc": "2.0",
                    "method": "VideoLibrary.GetMovies",
                    "params": {
                        "properties": ["imdbnumber"],
                        "filter": {"field": "imdbnumber", "operator": "is", "value": imdb_id}
                    },
                    "id": 1
                }
                
                response = json.loads(xbmc.executeJSONRPC(json.dumps(find_request)))
                if 'result' in response and 'movies' in response['result']:
                    movies = response['result']['movies']
                    if movies:
                        movie_id = movies[0]['movieid']
                        
                        # Now set the watched status
                        request['params']['movieid'] = movie_id
                        xbmc.executeJSONRPC(json.dumps(request))
                        xbmc.log(f"[CloudSync] Restored watched status for movie IMDB: {imdb_id}", xbmc.LOGDEBUG)
            
        except Exception as e:
            xbmc.log(f"[CloudSync] Error restoring watched status: {e}", xbmc.LOGERROR)
    
    def _restore_resume_points(self):
        """Restore resume points from local database to Kodi."""
        try:
            cursor = self.db_connection.cursor()
            
            # Get all resume points from local database
            cursor.execute("SELECT file_path, position, total_time FROM resume_points WHERE position > 0")
            resume_points = cursor.fetchall()
            
            for file_path, position, total_time in resume_points:
                # Find movie/episode by file path and set resume point
                find_request = {
                    "jsonrpc": "2.0",
                    "method": "VideoLibrary.GetMovies", 
                    "params": {
                        "properties": ["file"],
                        "filter": {"field": "filename", "operator": "is", "value": file_path}
                    },
                    "id": 1
                }
                
                response = json.loads(xbmc.executeJSONRPC(json.dumps(find_request)))
                if 'result' in response and 'movies' in response['result']:
                    movies = response['result']['movies']
                    if movies:
                        movie_id = movies[0]['movieid']
                        
                        # Set resume point
                        request = {
                            "jsonrpc": "2.0",
                            "method": "VideoLibrary.SetMovieDetails",
                            "params": {
                                "movieid": movie_id,
                                "resume": {
                                    "position": position,
                                    "total": total_time
                                }
                            },
                            "id": 1
                        }
                        
                        xbmc.executeJSONRPC(json.dumps(request))
                        xbmc.log(f"[CloudSync] Restored resume point: {file_path} at {position}s", xbmc.LOGDEBUG)
            
        except Exception as e:
            xbmc.log(f"[CloudSync] Error restoring resume points: {e}", xbmc.LOGERROR)
    
    def sync_favorites(self):
        """Sync favorites XML file with conflict resolution."""
        if not self.sync_favorites_enabled:
            return False

        try:
            # Get path to favorites.xml
            try:
                import xbmcvfs
                favorites_path = xbmcvfs.translatePath("special://profile/favourites.xml")
            except:
                favorites_path = xbmc.translatePath("special://profile/favourites.xml")

            # Check if favorites.xml exists locally
            local_exists = False
            try:
                import xbmcvfs
                local_exists = xbmcvfs.exists(favorites_path)
            except:
                import os
                local_exists = os.path.exists(favorites_path)

            if not local_exists:
                xbmc.log("[CloudSync] No local favourites.xml file found", xbmc.LOGINFO)
                return False

            # Check if file has changed since last sync
            has_changed, change_reason = self.change_tracker.has_file_changed(favorites_path, "favorites")
            if not has_changed:
                xbmc.log(f"[CloudSync] Skipping favourites.xml sync - no changes detected ({change_reason})", xbmc.LOGINFO)
                return False

            # Read local favorites.xml file
            with open(favorites_path, 'r', encoding='utf-8') as f:
                local_content = f.read()

            xbmc.log(f"[CloudSync] Read local favourites.xml ({len(local_content)} chars) - change reason: {change_reason}", xbmc.LOGINFO)

            # Check remote version for conflict resolution
            remote_content = None
            if self.dropbox_enabled and self.dropbox:
                if self.use_compression:
                    remote_content = self.dropbox.download_file_compressed("favourites.xml")
                else:
                    remote_content = self.dropbox.download_file("favourites.xml")

            should_upload = True
            if remote_content:
                # Apply conflict resolution to decide whether to upload
                if self.conflict_resolution == "local":
                    should_upload = True
                elif self.conflict_resolution == "remote":
                    should_upload = False
                elif self.conflict_resolution == "newer":
                    # Upload if local is larger (has more favorites)
                    local_size = len(local_content)
                    remote_size = len(remote_content)
                    should_upload = local_size > remote_size
                    xbmc.log(f"[CloudSync] Conflict resolution: local {local_size} chars vs remote {remote_size} chars", xbmc.LOGINFO)

            # Upload to Dropbox if decision is to upload
            if should_upload and self.dropbox_enabled and self.dropbox:
                if self.use_compression:
                    success = self.dropbox.upload_file_compressed("favourites.xml", local_content)
                else:
                    success = self.dropbox.upload_file("favourites.xml", local_content)

                if success:
                    xbmc.log("[CloudSync] Successfully uploaded favourites.xml to Dropbox", xbmc.LOGINFO)
                    # Mark file as synced
                    self.change_tracker.mark_file_synced(favorites_path, "favorites")
                    # Try to refresh favorites display if enabled
                    if self.addon.getSettingBool('favorites_refresh'):
                        self._reload_skin_for_favorites()
                    return True
                else:
                    xbmc.log("[CloudSync] Failed to upload favourites.xml to Dropbox", xbmc.LOGERROR)
                    return False
            elif not should_upload:
                xbmc.log("[CloudSync] Skipped upload due to conflict resolution", xbmc.LOGINFO)
                return False

            return True

        except Exception as e:
            xbmc.log(f"[CloudSync] Error syncing favorites: {e}", xbmc.LOGERROR)
            return False
    
    def _restore_favorites(self):
        """Restore favorites XML file from Dropbox."""
        if not self.sync_favorites_enabled:
            return

        try:
            # Download favorites.xml from Dropbox
            if not (self.dropbox_enabled and self.dropbox):
                return

            if self.use_compression:
                remote_content = self.dropbox.download_file_compressed("favourites.xml")
            else:
                remote_content = self.dropbox.download_file("favourites.xml")
            if not remote_content:
                xbmc.log("[CloudSync] No remote favourites.xml found", xbmc.LOGINFO)
                return

            # Get local favorites.xml path
            try:
                import xbmcvfs
                favorites_path = xbmcvfs.translatePath("special://profile/favourites.xml")
            except:
                favorites_path = xbmc.translatePath("special://profile/favourites.xml")

            # Check if we should overwrite local file
            local_exists = False
            try:
                import xbmcvfs
                local_exists = xbmcvfs.exists(favorites_path)
            except:
                import os
                local_exists = os.path.exists(favorites_path)

            # Smart conflict resolution based on settings
            if local_exists:
                try:
                    with open(favorites_path, 'r', encoding='utf-8') as f:
                        local_content = f.read().strip()

                    # Apply conflict resolution strategy
                    if self.conflict_resolution == "local":
                        xbmc.log("[CloudSync] Conflict resolution: keeping local favourites.xml", xbmc.LOGINFO)
                        return
                    elif self.conflict_resolution == "remote":
                        xbmc.log("[CloudSync] Conflict resolution: using remote favourites.xml", xbmc.LOGINFO)
                        # Continue to overwrite
                    elif self.conflict_resolution == "newer":
                        # Use the one with more content (more favorites)
                        local_size = len(local_content)
                        remote_size = len(remote_content)

                        if local_size >= remote_size:
                            xbmc.log(f"[CloudSync] Keeping larger local favourites.xml ({local_size} chars vs {remote_size} chars)", xbmc.LOGINFO)
                            return
                        else:
                            xbmc.log(f"[CloudSync] Using larger remote favourites.xml ({remote_size} chars vs {local_size} chars)", xbmc.LOGINFO)
                            # Continue to overwrite

                except:
                    pass  # If we can't read it, overwrite it

            # Write remote content to local file
            with open(favorites_path, 'w', encoding='utf-8') as f:
                f.write(remote_content)

            xbmc.log(f"[CloudSync] Successfully restored favourites.xml ({len(remote_content)} chars)", xbmc.LOGINFO)

            # Try to refresh favorites display if enabled
            if self.addon.getSettingBool('favorites_refresh'):
                self._reload_skin_for_favorites()

        except Exception as e:
            xbmc.log(f"[CloudSync] Error restoring favorites: {e}", xbmc.LOGERROR)

    def sync_userdata(self):
        """Sync UserData files (sources.xml, passwords.xml, etc.) with conflict resolution."""
        if not self.sync_userdata_enabled:
            return False

        # UserData files to sync (based on real Userdata structure analysis)
        userdata_files = [
            'sources.xml',          # Media sources and paths
            'passwords.xml',        # Saved passwords
            'mediasources.xml',     # Media sources configuration
            'advancedsettings.xml', # Advanced Kodi settings
            'profiles.xml',         # User profiles configuration
            'RssFeeds.xml',         # RSS feeds configuration
            'upnpserver.xml',       # UPnP server settings
        ]

        changes_made = False
        for filename in userdata_files:
            if self._sync_userdata_file(filename):
                changes_made = True

        if changes_made:
            xbmc.log("[CloudSync] UserData sync completed with changes", xbmc.LOGDEBUG)
        else:
            xbmc.log("[CloudSync] No changes in UserData files", xbmc.LOGDEBUG)

        return changes_made

    def _sync_userdata_file(self, filename):
        """Sync a single UserData file with conflict resolution."""
        try:
            # Get path to the file
            try:
                import xbmcvfs
                file_path = xbmcvfs.translatePath(f"special://profile/{filename}")
            except:
                file_path = xbmc.translatePath(f"special://profile/{filename}")

            # Check if file exists locally
            local_exists = False
            try:
                import xbmcvfs
                local_exists = xbmcvfs.exists(file_path)
            except:
                import os
                local_exists = os.path.exists(file_path)

            local_content = None
            if local_exists:
                # Check if file has changed since last sync
                has_changed, change_reason = self.change_tracker.has_file_changed(file_path, f"userdata/{filename}")
                if not has_changed:
                    xbmc.log(f"[CloudSync] Skipping {filename} sync - no changes detected ({change_reason})", xbmc.LOGINFO)
                    return False

                # Read local file
                with open(file_path, 'r', encoding='utf-8') as f:
                    local_content = f.read()
                xbmc.log(f"[CloudSync] Read local {filename} ({len(local_content)} chars) - change reason: {change_reason}", xbmc.LOGINFO)

            # Check remote version for conflict resolution
            remote_content = None
            if self.dropbox_enabled and self.dropbox:
                if self.use_compression:
                    remote_content = self.dropbox.download_file_compressed(f"userdata/{filename}")
                else:
                    remote_content = self.dropbox.download_file(f"userdata/{filename}")

            # Conflict resolution logic
            should_upload = True
            should_download = False

            if local_content and remote_content:
                # Both exist - apply conflict resolution
                if self.conflict_resolution == "local":
                    should_upload = True
                    should_download = False
                elif self.conflict_resolution == "remote":
                    should_upload = False
                    should_download = True
                elif self.conflict_resolution == "newer":
                    # Use file size as a simple heuristic
                    local_size = len(local_content)
                    remote_size = len(remote_content)
                    if local_size >= remote_size:
                        should_upload = True
                        should_download = False
                    else:
                        should_upload = False
                        should_download = True
                    xbmc.log(f"[CloudSync] {filename} conflict resolution: local {local_size} chars vs remote {remote_size} chars", xbmc.LOGINFO)
            elif local_content and not remote_content:
                # Only local exists - upload
                should_upload = True
                should_download = False
            elif not local_content and remote_content:
                # Only remote exists - download
                should_upload = False
                should_download = True
            else:
                # Neither exists - nothing to do
                xbmc.log(f"[CloudSync] {filename} does not exist locally or remotely", xbmc.LOGINFO)
                return False

            # Upload to Dropbox if needed
            if should_upload and local_content and self.dropbox_enabled and self.dropbox:
                if self.use_compression:
                    success = self.dropbox.upload_file_compressed(f"userdata/{filename}", local_content)
                else:
                    success = self.dropbox.upload_file(f"userdata/{filename}", local_content)

                if success:
                    xbmc.log(f"[CloudSync] Successfully uploaded {filename} to Dropbox", xbmc.LOGINFO)
                    # Mark file as synced
                    self.change_tracker.mark_file_synced(file_path, f"userdata/{filename}")
                    return True
                else:
                    xbmc.log(f"[CloudSync] Failed to upload {filename} to Dropbox", xbmc.LOGERROR)
                    return False

            # Download from Dropbox if needed
            if should_download and remote_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(remote_content)
                xbmc.log(f"[CloudSync] Successfully downloaded {filename} from Dropbox ({len(remote_content)} chars)", xbmc.LOGINFO)
                # Mark file as synced after download
                self.change_tracker.mark_file_synced(file_path, f"userdata/{filename}")
                return True

            return False

        except Exception as e:
            xbmc.log(f"[CloudSync] Error syncing {filename}: {e}", xbmc.LOGERROR)
            return False

    def _reload_skin_for_favorites(self):
        """Attempt to refresh favorites display in skin.

        Note: Kodi has no reliable way to refresh favorites.xml changes.
        According to official docs, only LoadProfile() works but causes UX issues.
        ReloadSkin() may not work for all skins (especially Arctic Zephyr).
        Consider this experimental - may be removed if ineffective.
        """
        try:
            xbmc.log("[CloudSync] Attempting to refresh favorites display", xbmc.LOGINFO)
            # Try ReloadSkin - may not work for all skins
            xbmc.executebuiltin("ReloadSkin()")
            xbmc.log("[CloudSync] Skin reload attempted (effectiveness varies by skin)", xbmc.LOGINFO)
        except Exception as e:
            xbmc.log(f"[CloudSync] Error attempting favorites refresh: {e}", xbmc.LOGERROR)





