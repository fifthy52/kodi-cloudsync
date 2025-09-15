import os
import time
import threading
import hashlib
from utils import log, get_addon
import xbmc
import xbmcvfs


class FileMonitor:
    """Monitor userdata files for changes."""
    
    def __init__(self, sync_callback=None):
        self.addon = get_addon()
        self.sync_callback = sync_callback
        self.monitoring = False
        self.monitor_thread = None
        
        # Files to monitor
        self.monitored_files = {
            'favourites.xml': 'favorites',
            'sources.xml': 'sources'
        }
        
        # Current state tracking
        self.file_states = {}
        
        # Settings
        self.sync_favorites = True
        self.sync_sources = True
        
        # Userdata path
        self.userdata_path = xbmc.translatePath('special://userdata/')
    
    def start_monitoring(self):
        """Start monitoring file changes."""
        try:
            if self.monitoring:
                return True
            
            self._update_settings()
            
            if not self.sync_favorites and not self.sync_sources:
                log("File monitoring disabled in settings", xbmc.LOGINFO)
                return False
            
            log("Starting file monitoring", xbmc.LOGINFO)
            self.monitoring = True
            
            # Get initial state
            self._update_file_states()
            
            # Start monitoring thread
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            
            return True
            
        except Exception as e:
            log(f"Error starting file monitor: {e}", xbmc.LOGERROR)
            return False
    
    def stop_monitoring(self):
        """Stop monitoring file changes."""
        self.monitoring = False
        
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5.0)
        
        log("File monitoring stopped", xbmc.LOGINFO)
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        check_interval = 10  # Check every 10 seconds
        
        while self.monitoring:
            try:
                time.sleep(check_interval)
                
                if not self.monitoring:
                    break
                
                self._check_for_changes()
                
            except Exception as e:
                log(f"Error in file monitor loop: {e}", xbmc.LOGERROR)
                time.sleep(60)  # Wait longer after error
    
    def _check_for_changes(self):
        """Check for file changes."""
        try:
            changes_detected = False
            sync_data = {
                'timestamp': time.time(),
                'file_changes': {}
            }
            
            for filename, file_type in self.monitored_files.items():
                if not self._should_monitor_file(file_type):
                    continue
                
                file_path = os.path.join(self.userdata_path, filename)
                current_state = self._get_file_state(file_path)
                previous_state = self.file_states.get(filename, {})
                
                if self._has_file_changed(previous_state, current_state):
                    log(f"File change detected: {filename}", xbmc.LOGDEBUG)
                    
                    sync_data['file_changes'][filename] = {
                        'type': file_type,
                        'path': file_path,
                        'old_state': previous_state,
                        'new_state': current_state
                    }
                    
                    changes_detected = True
                    self.file_states[filename] = current_state
            
            if changes_detected:
                log(f"File changes detected", xbmc.LOGDEBUG)
                
                # Trigger sync callback
                if self.sync_callback:
                    self.sync_callback('files', sync_data)
                
        except Exception as e:
            log(f"Error checking file changes: {e}", xbmc.LOGERROR)
    
    def _get_file_state(self, file_path):
        """Get current state of a file."""
        try:
            if not xbmcvfs.exists(file_path):
                return {
                    'exists': False,
                    'modified_time': 0,
                    'size': 0,
                    'hash': ''
                }
            
            stat = xbmcvfs.Stat(file_path)
            
            # Calculate file hash
            file_hash = ''
            try:
                with open(file_path, 'rb') as f:
                    content = f.read()
                    file_hash = hashlib.md5(content).hexdigest()
            except:
                pass
            
            return {
                'exists': True,
                'modified_time': stat.st_mtime(),
                'size': stat.st_size(),
                'hash': file_hash
            }
            
        except Exception as e:
            log(f"Error getting file state for {file_path}: {e}", xbmc.LOGERROR)
            return {
                'exists': False,
                'modified_time': 0,
                'size': 0,
                'hash': ''
            }
    
    def _has_file_changed(self, old_state, new_state):
        """Check if file has changed."""
        if not old_state:
            return new_state.get('exists', False)
        
        # Check existence change
        if old_state.get('exists', False) != new_state.get('exists', False):
            return True
        
        # If file doesn't exist, no change
        if not new_state.get('exists', False):
            return False
        
        # Check hash change (most reliable)
        old_hash = old_state.get('hash', '')
        new_hash = new_state.get('hash', '')
        
        if old_hash and new_hash and old_hash != new_hash:
            return True
        
        # Fallback to modification time and size
        return (old_state.get('modified_time', 0) != new_state.get('modified_time', 0) or
                old_state.get('size', 0) != new_state.get('size', 0))
    
    def _should_monitor_file(self, file_type):
        """Check if we should monitor this file type."""
        if file_type == 'favorites':
            return self.sync_favorites
        elif file_type == 'sources':
            return self.sync_sources
        return True
    
    def _update_file_states(self):
        """Update current state of all monitored files."""
        try:
            for filename, file_type in self.monitored_files.items():
                if self._should_monitor_file(file_type):
                    file_path = os.path.join(self.userdata_path, filename)
                    self.file_states[filename] = self._get_file_state(file_path)
            
            log("Updated file states baseline", xbmc.LOGDEBUG)
            
        except Exception as e:
            log(f"Error updating file states: {e}", xbmc.LOGERROR)
    
    def _update_settings(self):
        """Update settings from addon."""
        try:
            self.sync_favorites = self.addon.getSettingBool('sync_favorites')
            self.sync_sources = self.addon.getSettingBool('sync_sources')
            
        except Exception as e:
            log(f"Error updating file monitor settings: {e}", xbmc.LOGERROR)
    
    def get_current_files(self):
        """Get current content of monitored files."""
        try:
            files_content = {}
            
            for filename, file_type in self.monitored_files.items():
                if not self._should_monitor_file(file_type):
                    continue
                
                file_path = os.path.join(self.userdata_path, filename)
                
                if xbmcvfs.exists(file_path):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            files_content[filename] = {
                                'type': file_type,
                                'content': content,
                                'path': file_path,
                                'state': self._get_file_state(file_path)
                            }
                    except Exception as e:
                        log(f"Error reading {filename}: {e}", xbmc.LOGWARNING)
                        files_content[filename] = {
                            'type': file_type,
                            'content': None,
                            'path': file_path,
                            'error': str(e)
                        }
                else:
                    files_content[filename] = {
                        'type': file_type,
                        'content': None,
                        'path': file_path,
                        'exists': False
                    }
            
            return files_content
            
        except Exception as e:
            log(f"Error getting current files: {e}", xbmc.LOGERROR)
            return {}
    
    def restore_file(self, filename, content):
        """Restore file content from sync."""
        try:
            if filename not in self.monitored_files:
                log(f"Unknown file for restore: {filename}", xbmc.LOGWARNING)
                return False
            
            file_type = self.monitored_files[filename]
            if not self._should_monitor_file(file_type):
                log(f"File type {file_type} not enabled for sync", xbmc.LOGDEBUG)
                return False
            
            file_path = os.path.join(self.userdata_path, filename)
            
            # Create backup first
            if xbmcvfs.exists(file_path):
                backup_path = f"{file_path}.backup.{int(time.time())}"
                try:
                    xbmcvfs.copy(file_path, backup_path)
                    log(f"Created backup: {backup_path}", xbmc.LOGDEBUG)
                except Exception as e:
                    log(f"Warning: Could not create backup for {filename}: {e}", xbmc.LOGWARNING)
            
            # Write new content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Update file state
            self.file_states[filename] = self._get_file_state(file_path)
            
            log(f"Restored file: {filename}", xbmc.LOGINFO)
            return True
            
        except Exception as e:
            log(f"Error restoring file {filename}: {e}", xbmc.LOGERROR)
            return False