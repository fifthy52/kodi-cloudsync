# Packaging Instructions for CloudSync Addon

## Manual ZIP Creation

1. **Navigate to the minimal addon directory:**
   ```
   C:\Users\Lenovo\OneDrive\Projects\kodi_sync\service.cloudsync.minimal\
   ```

2. **Select all files in the directory:**
   - addon.xml
   - service.py  
   - resources/ (folder with settings.xml)

3. **Create ZIP archive:**
   - Right-click on selected files
   - Choose "Send to" > "Compressed (zipped) folder"
   - Rename to `service.cloudsync.zip`

## Alternative Method - Command Line

If you have PowerShell, run:
```powershell
cd "C:\Users\Lenovo\OneDrive\Projects\kodi_sync"
Compress-Archive -Path "service.cloudsync.minimal\*" -DestinationPath "service.cloudsync.zip"
```

## File Structure in ZIP

The ZIP should contain:
```
addon.xml
service.py
resources/
  └── settings.xml
```

**IMPORTANT:** 
- Do NOT include the parent folder `service.cloudsync.minimal` in the ZIP
- The files should be at the root level of the ZIP
- This is why manual ZIP creation often fails

## Installation in Kodi

1. Copy the `service.cloudsync.zip` to your Android device
2. In Kodi: Settings > Add-ons > Install from zip file
3. Navigate to the ZIP file location
4. Select and install

## Troubleshooting

If you get "Failed to unpack" errors:
1. Open the ZIP file and verify structure
2. Ensure no parent folders are included  
3. Check that addon.xml is at root level
4. Try recreating the ZIP with different method