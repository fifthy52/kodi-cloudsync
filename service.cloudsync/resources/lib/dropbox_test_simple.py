import sys
import os
import xbmc
import xbmcaddon
import xbmcgui

# Add current directory to path to avoid conflicts
current_dir = os.path.dirname(__file__)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from dropbox_provider_simple import DropboxProviderSimple


def test_dropbox_connection():
    """Test Dropbox connection and show results."""
    try:
        provider = DropboxProviderSimple()
        
        # Check if configured
        if not provider.is_available():
            xbmcgui.Dialog().ok(
                "Dropbox Test", 
                "Dropbox not configured.",
                "Please run 'Setup Dropbox' first."
            )
            return
        
        # Test connection
        if provider.test_connection():
            try:
                # Ensure folder exists
                provider.ensure_folder_exists()
                
                # List files
                files = provider.list_files()
                
                # Test upload/download
                test_content = "CloudSync test file"
                upload_success = provider.upload_file("test.txt", test_content, create_backup=False)
                
                if upload_success:
                    downloaded = provider.download_file("test.txt")
                    if downloaded == test_content:
                        test_result = "✓ Upload/Download test passed"
                        # Cleanup test file
                        provider._delete_file_silent("test.txt")
                    else:
                        test_result = "⚠ Download test failed"
                else:
                    test_result = "⚠ Upload test failed"
                
                # Show success results
                lines = [
                    "✓ Connection successful!",
                    "",
                    f"Sync folder: {provider.sync_folder}",
                    f"Files in sync folder: {len(files)}",
                    "",
                    test_result
                ]
                
                if files:
                    lines.append("")
                    lines.append("Files:")
                    for file_info in files[:5]:  # Show first 5 files
                        size_kb = file_info['size'] / 1024
                        lines.append(f"  • {file_info['name']} ({size_kb:.1f} KB)")
                    if len(files) > 5:
                        lines.append(f"  ... and {len(files) - 5} more files")
                
                xbmcgui.Dialog().textviewer("Dropbox Test Results", "\n".join(lines))
                
            except Exception as e:
                xbmc.log(f"[CloudSync] Error during extended test: {e}", xbmc.LOGERROR)
                xbmcgui.Dialog().ok(
                    "Dropbox Test", 
                    "✓ Connection successful!",
                    f"But extended test failed: {str(e)}"
                )
        else:
            xbmcgui.Dialog().ok(
                "Dropbox Test Failed", 
                "Could not connect to Dropbox.",
                "Please check your access token."
            )
            
    except Exception as e:
        xbmc.log(f"[CloudSync] Dropbox test error: {e}", xbmc.LOGERROR)
        xbmcgui.Dialog().ok(
            "Dropbox Test Error", 
            f"Test failed with error:",
            str(e)
        )


if __name__ == "__main__":
    test_dropbox_connection()