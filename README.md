# CloudSync for Kodi

A comprehensive Kodi addon for synchronizing watched status, resume points, favorites, and configuration files across multiple devices using Dropbox cloud storage.

## ✨ Features

### Currently Working
- **Watched Status Sync** - Movies and TV episodes playcount and last watched dates
- **Resume Points Sync** - Continue watching from where you left off
- **Favorites Sync** - Synchronize favorites across devices with smart conflict resolution
- **UserData Files Sync** - sources.xml, passwords.xml, and other configuration files
- **GZIP Compression** - Up to 90% data transfer reduction
- **Intelligent Change Detection** - SHA256-based file tracking avoids unnecessary syncs
- **OAuth2 Integration** - Modern secure Dropbox authentication with automatic token refresh
- **Web-based Setup** - Easy setup from any device on your network (no more typing long codes!)

## 🚀 Installation

### Option 1: From GitHub Releases (Recommended)
1. Go to [Releases](https://github.com/fifthy52/kodi-cloudsync/releases)
2. Download the latest `service.cloudsync-x.x.x.zip`
3. In Kodi: Settings → Add-ons → Install from zip file
4. Select the downloaded zip file

### Option 2: From Repository
1. Download [`repository.cloudsync.zip`](https://github.com/fifthy52/kodi-cloudsync/releases/latest/download/repository.cloudsync.zip)
2. Install the repository zip in Kodi
3. Install CloudSync from the repository (automatic updates!)

## ⚙️ Configuration

### Dropbox Setup (Choose one method)

#### 🌟 Simple Web Setup (Recommended)
1. Go to addon settings
2. Click "✨ Simple Web Setup (Best)"
3. Complete setup in your browser (works from phone/tablet!)

#### 📱 Mobile QR Setup
1. Use "📱 Mobile QR Setup" for QR code authentication
2. Scan QR code with your mobile device

#### 📝 Manual Setup
1. Go to [Dropbox App Console](https://www.dropbox.com/developers/apps)
2. Create new app → Scoped access → App folder
3. Enable permissions: `files.content.write`, `files.content.read`, `files.metadata.read`
4. Use "📝 Manual Token Setup" with your credentials

### Sync Options
- **Sync Watched Status** - Movie/episode watch status
- **Sync Resume Points** - Video playback positions
- **Sync Favorites** - Favorites menu items with automatic skin refresh
- **Sync UserData Files** - Kodi configuration files
- **Use GZIP Compression** - Reduce data transfer significantly
- **Conflict Resolution** - Choose how to handle conflicts between devices

## 📱 Web Setup Interface

CloudSync features a revolutionary web-based setup that eliminates the need to type long authorization codes in Kodi:

- **Network Accessible** - Use any device on your network
- **Mobile Friendly** - Perfect for phones and tablets
- **Step-by-Step Guide** - Clear 4-step process
- **Automatic Completion** - No manual code entry required

## 🔄 Version History

- **v4.1.2** - Fixed dialog overlaps, improved web setup UX
- **v4.1.0** - Added Simple Web Setup with paste interface
- **v4.0.0** - Revolutionary web interface for OAuth2 setup
- **v3.0.0** - Automatic OAuth2 authorization code capture
- **v2.7.0** - Real scannable QR codes for mobile setup
- **v2.5.0** - OAuth2 refresh token support for automatic renewal
- **v2.4.0** - Simplified addon, removed addon_data sync, added favorites auto-refresh

## 🛠️ Development

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
│       ├── simple_web_setup.py        # Web setup server
│       ├── oauth_server.py            # OAuth2 automation
│       └── ...
```

### Building from Source
```bash
git clone https://github.com/fifthy52/kodi-cloudsync.git
cd kodi-cloudsync
zip -r service.cloudsync-dev.zip service.cloudsync/
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with Kodi
5. Submit a pull request

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Credits

Inspired by professional Kodi addon development practices and built with modern OAuth2 security standards.

---

**Need help?** Open an [issue](https://github.com/fifthy52/kodi-cloudsync/issues) or check the [wiki](https://github.com/fifthy52/kodi-cloudsync/wiki) for troubleshooting guides.