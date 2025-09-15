import json
import urllib.request
import urllib.error
import urllib.parse
import xbmc
import xbmcaddon


class DropboxProviderSimple:
    """Simple Dropbox provider using direct API calls without dependencies."""
    
    API_BASE_URL = "https://api.dropboxapi.com/2"
    CONTENT_API_URL = "https://content.dropboxapi.com/2"
    
    def __init__(self):
        self.addon = xbmcaddon.Addon('service.cloudsync')
        self.access_token = self.addon.getSetting('dropbox_access_token')
        self.sync_folder = "/CloudSync"
    
    def is_available(self):
        """Check if Dropbox is configured."""
        return bool(self.access_token)
    
    def test_connection(self):
        """Test Dropbox connection."""
        if not self.access_token:
            xbmc.log("[CloudSync] No Dropbox access token configured", xbmc.LOGWARNING)
            return False
        
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            req = urllib.request.Request(
                f"{self.API_BASE_URL}/users/get_current_account",
                data=b'null',
                headers=headers
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                
                if 'account_id' in result:
                    name = result.get('name', {}).get('display_name', 'Unknown')
                    email = result.get('email', 'Unknown')
                    xbmc.log(f"[CloudSync] Connected to Dropbox as: {name} ({email})", xbmc.LOGINFO)
                    return True
                else:
                    xbmc.log("[CloudSync] Invalid response from Dropbox", xbmc.LOGERROR)
                    return False
                    
        except urllib.error.HTTPError as e:
            if e.code == 401:
                xbmc.log("[CloudSync] Invalid Dropbox access token", xbmc.LOGERROR)
            else:
                xbmc.log(f"[CloudSync] Dropbox HTTP Error {e.code}: {e.reason}", xbmc.LOGERROR)
            return False
        except Exception as e:
            xbmc.log(f"[CloudSync] Dropbox connection error: {e}", xbmc.LOGERROR)
            return False
    
    def ensure_folder_exists(self):
        """Ensure sync folder exists."""
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'path': self.sync_folder,
                'autorename': False
            }
            
            req = urllib.request.Request(
                f"{self.API_BASE_URL}/files/create_folder_v2",
                data=json.dumps(data).encode('utf-8'),
                headers=headers
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                xbmc.log(f"[CloudSync] Created Dropbox folder: {self.sync_folder}", xbmc.LOGDEBUG)
                return True
                
        except urllib.error.HTTPError as e:
            if e.code == 409:
                # Folder already exists
                xbmc.log(f"[CloudSync] Dropbox folder already exists: {self.sync_folder}", xbmc.LOGDEBUG)
                return True
            else:
                xbmc.log(f"[CloudSync] Error creating folder: HTTP {e.code}", xbmc.LOGWARNING)
                return False
        except Exception as e:
            xbmc.log(f"[CloudSync] Error creating folder: {e}", xbmc.LOGERROR)
            return False
    
    def upload_file(self, filename, content, create_backup=True):
        """Upload file to Dropbox."""
        if not self.is_available():
            return False
        
        try:
            # Convert content to bytes if needed
            if isinstance(content, str):
                file_content = content.encode('utf-8')
            else:
                file_content = content
            
            # Create backup only if requested and file exists
            if create_backup:
                try:
                    self._backup_file(filename)
                except Exception:
                    pass  # File might not exist, continue with upload
            
            # Ensure sync folder exists first
            self.ensure_folder_exists()
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/octet-stream',
                'Dropbox-API-Arg': json.dumps({
                    'path': f"{self.sync_folder}/{filename}",
                    'mode': 'overwrite'
                })
            }
            
            req = urllib.request.Request(
                f"{self.CONTENT_API_URL}/files/upload",
                data=file_content,
                headers=headers
            )
            
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))
                xbmc.log(f"[CloudSync] Uploaded {filename} to Dropbox", xbmc.LOGDEBUG)
                return True
                
        except urllib.error.HTTPError as e:
            error_response = ""
            try:
                if e.fp:
                    error_response = e.fp.read().decode('utf-8')
            except:
                pass
            xbmc.log(f"[CloudSync] HTTP error uploading {filename}: {e.code} {e.reason} - {error_response}", xbmc.LOGERROR)
            return False
        except Exception as e:
            xbmc.log(f"[CloudSync] Failed to upload {filename}: {e}", xbmc.LOGERROR)
            return False
    
    def download_file(self, filename):
        """Download file from Dropbox."""
        if not self.is_available():
            return None
        
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Dropbox-API-Arg': json.dumps({
                    'path': f"{self.sync_folder}/{filename}"
                })
            }
            
            req = urllib.request.Request(
                f"{self.CONTENT_API_URL}/files/download",
                headers=headers
            )
            
            with urllib.request.urlopen(req, timeout=30) as response:
                content = response.read()
                
                # Try to decode as text first
                try:
                    return content.decode('utf-8')
                except UnicodeDecodeError:
                    # Return as bytes if can't decode
                    return content
                    
        except urllib.error.HTTPError as e:
            if e.code == 404:
                # Try backup file
                return self._download_backup(filename)
            else:
                xbmc.log(f"[CloudSync] Error downloading {filename}: HTTP {e.code}", xbmc.LOGERROR)
                return None
        except Exception as e:
            xbmc.log(f"[CloudSync] Error downloading {filename}: {e}", xbmc.LOGERROR)
            return None
    
    def _backup_file(self, filename):
        """Create backup of existing file."""
        try:
            backup_name = f"old_{filename}"
            
            # Delete old backup
            self._delete_file_silent(backup_name)
            
            # Move current file to backup
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'from_path': f"{self.sync_folder}/{filename}",
                'to_path': f"{self.sync_folder}/{backup_name}",
                'autorename': False
            }
            
            req = urllib.request.Request(
                f"{self.API_BASE_URL}/files/move_v2",
                data=json.dumps(data).encode('utf-8'),
                headers=headers
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                xbmc.log(f"[CloudSync] Created backup: {backup_name}", xbmc.LOGDEBUG)
                
        except Exception:
            # Ignore backup errors - original file might not exist
            pass
    
    def _download_backup(self, filename):
        """Try to download backup file."""
        try:
            backup_name = f"old_{filename}"
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Dropbox-API-Arg': json.dumps({
                    'path': f"{self.sync_folder}/{backup_name}"
                })
            }
            
            req = urllib.request.Request(
                f"{self.CONTENT_API_URL}/files/download",
                headers=headers
            )
            
            with urllib.request.urlopen(req, timeout=30) as response:
                content = response.read()
                
                # Restore backup to main file
                self.upload_file(filename, content)
                
                try:
                    return content.decode('utf-8')
                except UnicodeDecodeError:
                    return content
                    
        except Exception:
            return None
    
    def _delete_file_silent(self, filename):
        """Delete file without error reporting."""
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'path': f"{self.sync_folder}/{filename}"
            }
            
            req = urllib.request.Request(
                f"{self.API_BASE_URL}/files/delete_v2",
                data=json.dumps(data).encode('utf-8'),
                headers=headers
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                pass
                
        except Exception:
            pass
    
    def list_files(self):
        """List files in sync folder."""
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'path': self.sync_folder,
                'recursive': False
            }
            
            req = urllib.request.Request(
                f"{self.API_BASE_URL}/files/list_folder",
                data=json.dumps(data).encode('utf-8'),
                headers=headers
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                
                files = []
                for entry in result.get('entries', []):
                    if entry.get('.tag') == 'file':
                        files.append({
                            'name': entry.get('name'),
                            'path': entry.get('path_display'),
                            'size': entry.get('size', 0),
                            'modified': entry.get('server_modified')
                        })
                
                return files
                
        except Exception as e:
            xbmc.log(f"[CloudSync] Error listing files: {e}", xbmc.LOGERROR)
            return []