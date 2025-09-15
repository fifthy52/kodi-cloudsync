import json
import time
import threading
from utils import log, get_addon
import xbmc


class DatabaseMonitor:
    """Monitor Kodi database for changes in watched status and resume points."""
    
    def __init__(self, sync_callback=None):
        self.addon = get_addon()
        self.sync_callback = sync_callback
        self.monitoring = False
        self.monitor_thread = None
        
        # Track last known state
        self.last_watched_movies = {}
        self.last_watched_episodes = {}
        self.last_resume_points = {}
        
        # Settings
        self.sync_watched = True
        self.sync_resume = True
    
    def start_monitoring(self):
        """Start monitoring database changes."""
        try:
            if self.monitoring:
                return True
            
            self._update_settings()
            
            if not self.sync_watched and not self.sync_resume:
                log("Database monitoring disabled in settings", xbmc.LOGINFO)
                return False
            
            log("Starting database monitoring", xbmc.LOGINFO)
            self.monitoring = True
            
            # Get initial state
            self._update_baseline_state()
            
            # Start monitoring thread
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            
            return True
            
        except Exception as e:
            log(f"Error starting database monitor: {e}", xbmc.LOGERROR)
            return False
    
    def stop_monitoring(self):
        """Stop monitoring database changes."""
        self.monitoring = False
        
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5.0)
        
        log("Database monitoring stopped", xbmc.LOGINFO)
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        check_interval = 30  # Check every 30 seconds
        
        while self.monitoring:
            try:
                time.sleep(check_interval)
                
                if not self.monitoring:
                    break
                
                self._check_for_changes()
                
            except Exception as e:
                log(f"Error in database monitor loop: {e}", xbmc.LOGERROR)
                time.sleep(60)  # Wait longer after error
    
    def _check_for_changes(self):
        """Check for changes in database."""
        try:
            changes_detected = False
            sync_data = {
                'timestamp': time.time(),
                'watched_changes': {},
                'resume_changes': {}
            }
            
            if self.sync_watched:
                # Check watched status changes
                current_movies = self._get_watched_movies()
                current_episodes = self._get_watched_episodes()
                
                movie_changes = self._find_changes(self.last_watched_movies, current_movies, 'movies')
                episode_changes = self._find_changes(self.last_watched_episodes, current_episodes, 'episodes')
                
                if movie_changes or episode_changes:
                    sync_data['watched_changes'] = {
                        'movies': movie_changes,
                        'episodes': episode_changes
                    }
                    changes_detected = True
                    
                    self.last_watched_movies = current_movies
                    self.last_watched_episodes = current_episodes
            
            if self.sync_resume:
                # Check resume points changes  
                current_resume = self._get_resume_points()
                resume_changes = self._find_changes(self.last_resume_points, current_resume, 'resume')
                
                if resume_changes:
                    sync_data['resume_changes'] = resume_changes
                    changes_detected = True
                    self.last_resume_points = current_resume
            
            if changes_detected:
                log(f"Database changes detected", xbmc.LOGDEBUG)
                
                # Trigger sync callback
                if self.sync_callback:
                    self.sync_callback('database', sync_data)
                
        except Exception as e:
            log(f"Error checking database changes: {e}", xbmc.LOGERROR)
    
    def _get_watched_movies(self):
        """Get watched movies from database."""
        try:
            request = {
                "jsonrpc": "2.0",
                "method": "VideoLibrary.GetMovies",
                "params": {
                    "properties": ["playcount", "lastplayed", "file", "imdbnumber", "title", "year"],
                    "filter": {"field": "playcount", "operator": "greaterthan", "value": "0"}
                },
                "id": 1
            }
            
            response = xbmc.executeJSONRPC(json.dumps(request))
            result = json.loads(response)
            
            movies = {}
            if 'result' in result and 'movies' in result['result']:
                for movie in result['result']['movies']:
                    movie_id = movie.get('movieid')
                    if movie_id:
                        movies[str(movie_id)] = {
                            'title': movie.get('title', ''),
                            'year': movie.get('year', 0),
                            'file': movie.get('file', ''),
                            'playcount': movie.get('playcount', 0),
                            'lastplayed': movie.get('lastplayed', ''),
                            'imdbnumber': movie.get('imdbnumber', '')
                        }
            
            return movies
            
        except Exception as e:
            log(f"Error getting watched movies: {e}", xbmc.LOGERROR)
            return {}
    
    def _get_watched_episodes(self):
        """Get watched episodes from database."""
        try:
            request = {
                "jsonrpc": "2.0", 
                "method": "VideoLibrary.GetEpisodes",
                "params": {
                    "properties": ["playcount", "lastplayed", "file", "tvshowid", "season", "episode", "title"],
                    "filter": {"field": "playcount", "operator": "greaterthan", "value": "0"}
                },
                "id": 2
            }
            
            response = xbmc.executeJSONRPC(json.dumps(request))
            result = json.loads(response)
            
            episodes = {}
            if 'result' in result and 'episodes' in result['result']:
                for episode in result['result']['episodes']:
                    episode_id = episode.get('episodeid')
                    if episode_id:
                        episodes[str(episode_id)] = {
                            'title': episode.get('title', ''),
                            'tvshowid': episode.get('tvshowid', 0),
                            'season': episode.get('season', 0),
                            'episode': episode.get('episode', 0),
                            'file': episode.get('file', ''),
                            'playcount': episode.get('playcount', 0),
                            'lastplayed': episode.get('lastplayed', '')
                        }
            
            return episodes
            
        except Exception as e:
            log(f"Error getting watched episodes: {e}", xbmc.LOGERROR)
            return {}
    
    def _get_resume_points(self):
        """Get resume points from database."""
        try:
            # Get movies with resume points
            movies_request = {
                "jsonrpc": "2.0",
                "method": "VideoLibrary.GetMovies", 
                "params": {
                    "properties": ["resume", "file", "title"]
                },
                "id": 3
            }
            
            response = xbmc.executeJSONRPC(json.dumps(movies_request))
            result = json.loads(response)
            
            resume_points = {}
            
            if 'result' in result and 'movies' in result['result']:
                for movie in result['result']['movies']:
                    resume = movie.get('resume', {})
                    if resume.get('position', 0) > 0:
                        movie_id = movie.get('movieid')
                        if movie_id:
                            resume_points[f"movie_{movie_id}"] = {
                                'type': 'movie',
                                'id': movie_id,
                                'title': movie.get('title', ''),
                                'file': movie.get('file', ''),
                                'position': resume.get('position', 0),
                                'total': resume.get('total', 0)
                            }
            
            # Get episodes with resume points
            episodes_request = {
                "jsonrpc": "2.0",
                "method": "VideoLibrary.GetEpisodes",
                "params": {
                    "properties": ["resume", "file", "title", "tvshowid", "season", "episode"]
                },
                "id": 4
            }
            
            response = xbmc.executeJSONRPC(json.dumps(episodes_request))
            result = json.loads(response)
            
            if 'result' in result and 'episodes' in result['result']:
                for episode in result['result']['episodes']:
                    resume = episode.get('resume', {})
                    if resume.get('position', 0) > 0:
                        episode_id = episode.get('episodeid')
                        if episode_id:
                            resume_points[f"episode_{episode_id}"] = {
                                'type': 'episode',
                                'id': episode_id,
                                'title': episode.get('title', ''),
                                'file': episode.get('file', ''),
                                'position': resume.get('position', 0),
                                'total': resume.get('total', 0),
                                'tvshowid': episode.get('tvshowid'),
                                'season': episode.get('season'),
                                'episode': episode.get('episode')
                            }
            
            return resume_points
            
        except Exception as e:
            log(f"Error getting resume points: {e}", xbmc.LOGERROR)
            return {}
    
    def _find_changes(self, old_data, new_data, data_type):
        """Find changes between old and new data."""
        changes = {}
        
        # Check for new or modified items
        for key, new_item in new_data.items():
            old_item = old_data.get(key, {})
            
            if not old_item or old_item != new_item:
                changes[key] = {
                    'action': 'update',
                    'old': old_item,
                    'new': new_item
                }
        
        # Check for deleted items (watched -> unwatched)
        for key in old_data:
            if key not in new_data:
                changes[key] = {
                    'action': 'delete',
                    'old': old_data[key],
                    'new': None
                }
        
        if changes:
            log(f"Found {len(changes)} changes in {data_type}", xbmc.LOGDEBUG)
        
        return changes
    
    def _update_baseline_state(self):
        """Update baseline state for comparison."""
        try:
            if self.sync_watched:
                self.last_watched_movies = self._get_watched_movies()
                self.last_watched_episodes = self._get_watched_episodes()
            
            if self.sync_resume:
                self.last_resume_points = self._get_resume_points()
            
            log("Updated database baseline state", xbmc.LOGDEBUG)
            
        except Exception as e:
            log(f"Error updating baseline state: {e}", xbmc.LOGERROR)
    
    def _update_settings(self):
        """Update settings from addon."""
        try:
            self.sync_watched = self.addon.getSettingBool('sync_watched')
            self.sync_resume = self.addon.getSettingBool('sync_resume_points')
            
        except Exception as e:
            log(f"Error updating database monitor settings: {e}", xbmc.LOGERROR)
    
    def get_current_state(self):
        """Get current database state for manual sync."""
        try:
            state = {
                'timestamp': time.time(),
                'watched_movies': {},
                'watched_episodes': {}, 
                'resume_points': {}
            }
            
            if self.sync_watched:
                state['watched_movies'] = self._get_watched_movies()
                state['watched_episodes'] = self._get_watched_episodes()
            
            if self.sync_resume:
                state['resume_points'] = self._get_resume_points()
            
            return state
            
        except Exception as e:
            log(f"Error getting current database state: {e}", xbmc.LOGERROR)
            return {}