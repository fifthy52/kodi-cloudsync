# Kodi CloudSync

A comprehensive Kodi addon for synchronizing watched status, resume points, favorites, and configuration files across multiple devices using Dropbox cloud storage.

## Features

### ✅ Currently Working
- **Watched Status Sync** - Movies and TV episodes playcount and last watched dates
- **Resume Points Sync** - Continue watching from where you left off
- **Favorites Sync** - Synchronize favourites.xml across devices with smart conflict resolution
- **UserData Files Sync** - sources.xml, passwords.xml, mediasources.xml, advancedsettings.xml
- **Addon Data Sync** - Selective sync of addon configuration files for popular addons
- **Dropbox Integration** - Simple token-based authentication
- **Conflict Resolution** - Choose between "newer", "local", or "remote" strategies
- **Advanced Conflict Resolution** - Per-file-type resolution strategies

### 🚧 In Development
- **Custom Addon Selection** - User-configurable addon sync lists
- **Backup and Restore** - Full profile backup/restore functionality

## Installation

1. Download the latest `service.cloudsync.zip` from releases
2. Install via Kodi Add-ons → Install from zip file
3. Configure Dropbox access token in addon settings
4. Enable desired sync options

## Configuration

### Dropbox Setup
1. Go to [Dropbox App Console](https://www.dropbox.com/developers/apps)
2. Create new app → Scoped access → App folder
3. Enable permissions: `files.content.write`, `files.content.read`, `files.metadata.read`
4. Generate access token
5. Enter token in addon settings

### Sync Options
- **Sync Watched Status** - Movie/episode watch status
- **Sync Resume Points** - Video playback positions
- **Sync Favorites** - Favorites menu items
- **Sync UserData Files** - Kodi configuration files (sources, passwords, etc.)
- **Sync Addon Data** - Configuration files for popular addons
- **Conflict Resolution** - How to handle conflicts between devices

## Development

### Project Structure
```
service.cloudsync/
├── addon.xml                          # Addon metadata
├── service_v2.py                      # Main service entry point
├── resources/
│   ├── settings.xml                   # Settings UI
│   ├── language/                      # Localization
│   └── lib/                          # Python modules
│       ├── hybrid_sync_manager.py     # Main sync logic
│       ├── dropbox_provider_simple.py # Dropbox API wrapper
│       ├── kodi_utils.py              # Kodi JSON-RPC helpers
│       └── ...
```

### Version History
- **v1.0** - Basic watched status and resume points sync
- **v1.1** - Added favorites sync with XML file approach
- **v1.2** - Smart conflict resolution for favorites
- **v2.0** - UserData and addon_data sync implementation

## Credits

Inspired by the excellent `service.watchedsync` addon and built using patterns from professional Kodi addon development.

## License

MIT License - See LICENSE file for details