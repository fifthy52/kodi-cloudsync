import json
import time
from datetime import datetime
import xbmc
import xbmcgui
from utils import log


class ConflictResolver:
    """Advanced conflict resolution with user interaction support."""
    
    def __init__(self, resolution_strategy='newer'):
        self.strategy = resolution_strategy
        self.pending_conflicts = []
    
    def resolve_database_conflict(self, local_item, remote_item, item_type, item_id):
        """Resolve database item conflict."""
        try:
            # If items are identical, no conflict
            if local_item == remote_item:
                return local_item
            
            # If one is None/empty, use the other
            if not local_item and remote_item:
                return remote_item
            if local_item and not remote_item:
                return local_item
            
            conflict_info = {
                'type': 'database',
                'item_type': item_type,
                'item_id': item_id,
                'local': local_item,
                'remote': remote_item,
                'timestamp': time.time()
            }
            
            return self._apply_resolution_strategy(conflict_info)
            
        except Exception as e:
            log(f"Error resolving database conflict for {item_type} {item_id}: {e}", xbmc.LOGERROR)
            return local_item  # Default to local on error
    
    def resolve_file_conflict(self, filename, local_content, remote_content, local_state=None):
        """Resolve file content conflict."""
        try:
            # If contents are identical, no conflict
            if local_content == remote_content:
                return local_content
            
            # If one is None/empty, use the other
            if not local_content and remote_content:
                return remote_content
            if local_content and not remote_content:
                return local_content
            
            conflict_info = {
                'type': 'file',
                'filename': filename,
                'local': local_content,
                'remote': remote_content,
                'local_state': local_state,
                'timestamp': time.time()
            }
            
            return self._apply_resolution_strategy(conflict_info)
            
        except Exception as e:
            log(f"Error resolving file conflict for {filename}: {e}", xbmc.LOGERROR)
            return local_content  # Default to local on error
    
    def _apply_resolution_strategy(self, conflict_info):
        """Apply the configured resolution strategy."""
        try:
            if self.strategy == 'local':
                log(f"Conflict resolved: using local version ({conflict_info['type']})", xbmc.LOGDEBUG)
                return conflict_info['local']
            
            elif self.strategy == 'remote':
                log(f"Conflict resolved: using remote version ({conflict_info['type']})", xbmc.LOGDEBUG)
                return conflict_info['remote']
            
            elif self.strategy == 'newer':
                return self._resolve_by_timestamp(conflict_info)
            
            elif self.strategy == 'ask':
                return self._resolve_by_user_choice(conflict_info)
            
            else:
                # Default to newer
                return self._resolve_by_timestamp(conflict_info)
                
        except Exception as e:
            log(f"Error applying resolution strategy: {e}", xbmc.LOGERROR)
            return conflict_info['local']
    
    def _resolve_by_timestamp(self, conflict_info):
        """Resolve conflict by using the newer version."""
        try:
            local_time = self._extract_timestamp(conflict_info, 'local')
            remote_time = self._extract_timestamp(conflict_info, 'remote')
            
            if local_time > remote_time:
                log(f"Conflict resolved: local version is newer ({conflict_info['type']})", xbmc.LOGDEBUG)
                return conflict_info['local']
            elif remote_time > local_time:
                log(f"Conflict resolved: remote version is newer ({conflict_info['type']})", xbmc.LOGDEBUG)
                return conflict_info['remote']
            else:
                # Same timestamp, prefer local
                log(f"Conflict resolved: same timestamp, using local ({conflict_info['type']})", xbmc.LOGDEBUG)
                return conflict_info['local']
                
        except Exception as e:
            log(f"Error resolving by timestamp: {e}", xbmc.LOGERROR)
            return conflict_info['local']
    
    def _extract_timestamp(self, conflict_info, version):
        """Extract timestamp from conflict data."""
        try:
            data = conflict_info[version]
            
            if conflict_info['type'] == 'database':
                # Try to get lastplayed timestamp
                if isinstance(data, dict):
                    lastplayed = data.get('lastplayed', '')
                    if lastplayed:
                        # Parse Kodi's lastplayed format
                        try:
                            return datetime.strptime(lastplayed, '%Y-%m-%d %H:%M:%S').timestamp()
                        except:
                            pass
                    
                    # Fallback to playcount as rough indicator
                    playcount = data.get('playcount', 0)
                    return playcount
                
                return 0
            
            elif conflict_info['type'] == 'file':
                # Use file state timestamp if available
                if version == 'local' and conflict_info.get('local_state'):
                    return conflict_info['local_state'].get('modified_time', 0)
                
                # For remote files, we don't have timestamp info easily
                # So prefer local in timestamp comparison
                return 0 if version == 'remote' else time.time()
            
            return 0
            
        except Exception as e:
            log(f"Error extracting timestamp: {e}", xbmc.LOGERROR)
            return 0
    
    def _resolve_by_user_choice(self, conflict_info):
        """Resolve conflict by asking the user."""
        try:
            # For now, add to pending conflicts and use default strategy
            # In a future version, this could show a dialog
            self.pending_conflicts.append(conflict_info)
            
            log(f"Conflict added to pending list for user resolution ({conflict_info['type']})", xbmc.LOGDEBUG)
            
            # Fall back to newer strategy for now
            return self._resolve_by_timestamp(conflict_info)
            
        except Exception as e:
            log(f"Error in user choice resolution: {e}", xbmc.LOGERROR)
            return conflict_info['local']
    
    def resolve_complex_database_merge(self, local_db_state, remote_db_state):
        """Perform intelligent merge of complete database states."""
        try:
            if not remote_db_state:
                return local_db_state
            if not local_db_state:
                return remote_db_state
            
            merged_state = local_db_state.copy()
            
            # Merge watched movies
            local_movies = local_db_state.get('watched_movies', {})
            remote_movies = remote_db_state.get('watched_movies', {})
            merged_movies = {}
            
            # Get all movie IDs from both sources
            all_movie_ids = set(local_movies.keys()) | set(remote_movies.keys())
            
            for movie_id in all_movie_ids:
                local_movie = local_movies.get(movie_id, {})
                remote_movie = remote_movies.get(movie_id, {})
                
                merged_movie = self.resolve_database_conflict(
                    local_movie, remote_movie, 'movie', movie_id
                )
                
                if merged_movie:
                    merged_movies[movie_id] = merged_movie
            
            merged_state['watched_movies'] = merged_movies
            
            # Merge watched episodes
            local_episodes = local_db_state.get('watched_episodes', {})
            remote_episodes = remote_db_state.get('watched_episodes', {})
            merged_episodes = {}
            
            all_episode_ids = set(local_episodes.keys()) | set(remote_episodes.keys())
            
            for episode_id in all_episode_ids:
                local_episode = local_episodes.get(episode_id, {})
                remote_episode = remote_episodes.get(episode_id, {})
                
                merged_episode = self.resolve_database_conflict(
                    local_episode, remote_episode, 'episode', episode_id
                )
                
                if merged_episode:
                    merged_episodes[episode_id] = merged_episode
            
            merged_state['watched_episodes'] = merged_episodes
            
            # Merge resume points
            local_resume = local_db_state.get('resume_points', {})
            remote_resume = remote_db_state.get('resume_points', {})
            merged_resume = {}
            
            all_resume_ids = set(local_resume.keys()) | set(remote_resume.keys())
            
            for resume_id in all_resume_ids:
                local_point = local_resume.get(resume_id, {})
                remote_point = remote_resume.get(resume_id, {})
                
                # For resume points, prefer the one with higher position (more progress)
                if local_point and remote_point:
                    local_pos = local_point.get('position', 0)
                    remote_pos = remote_point.get('position', 0)
                    
                    if local_pos > remote_pos:
                        merged_resume[resume_id] = local_point
                    elif remote_pos > local_pos:
                        merged_resume[resume_id] = remote_point
                    else:
                        # Same position, use conflict resolution
                        merged_point = self.resolve_database_conflict(
                            local_point, remote_point, 'resume', resume_id
                        )
                        if merged_point:
                            merged_resume[resume_id] = merged_point
                elif local_point:
                    merged_resume[resume_id] = local_point
                elif remote_point:
                    merged_resume[resume_id] = remote_point
            
            merged_state['resume_points'] = merged_resume
            
            # Use the newer timestamp
            local_time = local_db_state.get('timestamp', 0)
            remote_time = remote_db_state.get('timestamp', 0)
            merged_state['timestamp'] = max(local_time, remote_time)
            
            log(f"Complex database merge completed", xbmc.LOGDEBUG)
            return merged_state
            
        except Exception as e:
            log(f"Error in complex database merge: {e}", xbmc.LOGERROR)
            return local_db_state
    
    def get_pending_conflicts(self):
        """Get list of conflicts that need user resolution."""
        return self.pending_conflicts.copy()
    
    def clear_pending_conflicts(self):
        """Clear pending conflicts list."""
        self.pending_conflicts.clear()
    
    def set_strategy(self, strategy):
        """Update resolution strategy."""
        if strategy in ['newer', 'local', 'remote', 'ask']:
            self.strategy = strategy
            log(f"Conflict resolution strategy set to: {strategy}", xbmc.LOGDEBUG)
        else:
            log(f"Invalid resolution strategy: {strategy}", xbmc.LOGWARNING)
    
    def create_conflict_summary(self):
        """Create a summary of recent conflicts for logging."""
        try:
            if not self.pending_conflicts:
                return "No conflicts detected"
            
            summary = []
            for conflict in self.pending_conflicts[-10:]:  # Last 10 conflicts
                conflict_type = conflict['type']
                if conflict_type == 'database':
                    item_type = conflict['item_type']
                    item_id = conflict['item_id']
                    summary.append(f"{item_type} {item_id}")
                elif conflict_type == 'file':
                    filename = conflict['filename']
                    summary.append(f"file {filename}")
            
            return f"Recent conflicts: {', '.join(summary)}"
            
        except Exception as e:
            log(f"Error creating conflict summary: {e}", xbmc.LOGERROR)
            return "Error creating summary"