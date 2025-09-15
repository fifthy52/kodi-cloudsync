"""
File change tracking system for CloudSync
Tracks file modifications using hashes and timestamps to avoid unnecessary sync operations
"""

import hashlib
import json
import os
import time
import xbmc
import xbmcaddon


class FileChangeTracker:
    """Tracks file changes using hashes and timestamps to optimize sync operations."""

    def __init__(self):
        self.addon = xbmcaddon.Addon('service.cloudsync')

        # Get userdata path for storing tracking database
        try:
            import xbmcvfs
            self.tracking_db_path = xbmcvfs.translatePath("special://profile/addon_data/service.cloudsync/file_tracking.json")
            self.base_path = xbmcvfs.translatePath("special://profile/addon_data/service.cloudsync/")
        except:
            self.tracking_db_path = xbmc.translatePath("special://profile/addon_data/service.cloudsync/file_tracking.json")
            self.base_path = xbmc.translatePath("special://profile/addon_data/service.cloudsync/")

        self.tracking_data = {}
        self._load_tracking_data()

    def _ensure_directory_exists(self):
        """Ensure the tracking directory exists."""
        try:
            import xbmcvfs
            if not xbmcvfs.exists(self.base_path):
                xbmcvfs.mkdirs(self.base_path)
        except:
            import os
            os.makedirs(self.base_path, exist_ok=True)

    def _load_tracking_data(self):
        """Load file tracking data from JSON file."""
        try:
            if os.path.exists(self.tracking_db_path):
                with open(self.tracking_db_path, 'r', encoding='utf-8') as f:
                    self.tracking_data = json.load(f)
                xbmc.log(f"[CloudSync] Loaded file tracking data for {len(self.tracking_data)} files", xbmc.LOGDEBUG)
            else:
                self.tracking_data = {}
                xbmc.log("[CloudSync] No existing file tracking data found, starting fresh", xbmc.LOGINFO)
        except Exception as e:
            xbmc.log(f"[CloudSync] Error loading tracking data: {e}", xbmc.LOGERROR)
            self.tracking_data = {}

    def _save_tracking_data(self):
        """Save file tracking data to JSON file."""
        try:
            self._ensure_directory_exists()
            with open(self.tracking_db_path, 'w', encoding='utf-8') as f:
                json.dump(self.tracking_data, f, indent=2)
            xbmc.log(f"[CloudSync] Saved file tracking data for {len(self.tracking_data)} files", xbmc.LOGDEBUG)
        except Exception as e:
            xbmc.log(f"[CloudSync] Error saving tracking data: {e}", xbmc.LOGERROR)

    def _calculate_file_hash(self, file_path):
        """Calculate SHA256 hash of file content."""
        try:
            hasher = hashlib.sha256()
            with open(file_path, 'rb') as f:
                # Read file in chunks to handle large files
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            xbmc.log(f"[CloudSync] Error calculating hash for {file_path}: {e}", xbmc.LOGERROR)
            return None

    def _get_file_info(self, file_path):
        """Get file modification time and size."""
        try:
            stat = os.stat(file_path)
            return {
                'mtime': stat.st_mtime,
                'size': stat.st_size
            }
        except Exception as e:
            xbmc.log(f"[CloudSync] Error getting file info for {file_path}: {e}", xbmc.LOGERROR)
            return None

    def has_file_changed(self, file_path, file_type="unknown"):
        """
        Check if file has changed since last sync.

        Args:
            file_path: Path to the file to check
            file_type: Type of file (favorites, userdata, addon_data) for logging

        Returns:
            tuple: (has_changed: bool, reason: str)
        """
        if not os.path.exists(file_path):
            return True, "file_not_exists"

        # Get current file info
        current_info = self._get_file_info(file_path)
        if not current_info:
            return True, "file_info_error"

        # Get stored tracking info
        stored_info = self.tracking_data.get(file_path, {})

        # Check if we have any stored data
        if not stored_info:
            xbmc.log(f"[CloudSync] {file_type} file {file_path} - No tracking data, marking as changed", xbmc.LOGINFO)
            return True, "no_tracking_data"

        # Quick check: modification time and size
        if (stored_info.get('mtime') != current_info['mtime'] or
            stored_info.get('size') != current_info['size']):
            xbmc.log(f"[CloudSync] {file_type} file {file_path} - Modified (mtime/size changed)", xbmc.LOGINFO)
            return True, "mtime_size_changed"

        # If mtime and size are same, calculate hash for definitive check
        current_hash = self._calculate_file_hash(file_path)
        if not current_hash:
            return True, "hash_calculation_error"

        stored_hash = stored_info.get('hash')
        if stored_hash != current_hash:
            xbmc.log(f"[CloudSync] {file_type} file {file_path} - Content changed (hash mismatch)", xbmc.LOGINFO)
            return True, "content_changed"

        # Check if enough time has passed since last sync (force sync every 24 hours)
        last_sync = stored_info.get('last_sync', 0)
        if time.time() - last_sync > 86400:  # 24 hours
            xbmc.log(f"[CloudSync] {file_type} file {file_path} - Forcing sync (24h elapsed)", xbmc.LOGINFO)
            return True, "force_sync_24h"

        xbmc.log(f"[CloudSync] {file_type} file {file_path} - No changes detected", xbmc.LOGDEBUG)
        return False, "no_changes"

    def mark_file_synced(self, file_path, file_type="unknown"):
        """
        Mark file as successfully synced with current state.

        Args:
            file_path: Path to the file that was synced
            file_type: Type of file for logging
        """
        if not os.path.exists(file_path):
            xbmc.log(f"[CloudSync] Cannot mark non-existent file as synced: {file_path}", xbmc.LOGWARNING)
            return

        current_info = self._get_file_info(file_path)
        current_hash = self._calculate_file_hash(file_path)

        if not current_info or not current_hash:
            xbmc.log(f"[CloudSync] Error getting file info/hash for synced file: {file_path}", xbmc.LOGERROR)
            return

        self.tracking_data[file_path] = {
            'mtime': current_info['mtime'],
            'size': current_info['size'],
            'hash': current_hash,
            'last_sync': time.time(),
            'file_type': file_type
        }

        self._save_tracking_data()
        xbmc.log(f"[CloudSync] Marked {file_type} file as synced: {file_path}", xbmc.LOGDEBUG)

    def remove_file_tracking(self, file_path):
        """Remove tracking data for a file that no longer exists."""
        if file_path in self.tracking_data:
            del self.tracking_data[file_path]
            self._save_tracking_data()
            xbmc.log(f"[CloudSync] Removed tracking data for deleted file: {file_path}", xbmc.LOGDEBUG)

    def get_tracking_stats(self):
        """Get statistics about tracked files."""
        total_files = len(self.tracking_data)
        file_types = {}

        for file_path, info in self.tracking_data.items():
            file_type = info.get('file_type', 'unknown')
            file_types[file_type] = file_types.get(file_type, 0) + 1

        return {
            'total_files': total_files,
            'file_types': file_types,
            'tracking_db_path': self.tracking_db_path
        }

    def cleanup_orphaned_tracking_data(self):
        """Remove tracking data for files that no longer exist."""
        orphaned_files = []

        for file_path in list(self.tracking_data.keys()):
            if not os.path.exists(file_path):
                orphaned_files.append(file_path)

        for file_path in orphaned_files:
            del self.tracking_data[file_path]

        if orphaned_files:
            self._save_tracking_data()
            xbmc.log(f"[CloudSync] Cleaned up tracking data for {len(orphaned_files)} orphaned files", xbmc.LOGINFO)

        return len(orphaned_files)