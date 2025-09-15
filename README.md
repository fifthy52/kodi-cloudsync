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

### ⭐ Option 1: Repository Install (Recommended - Auto Updates!)
1. Download [`repository.cloudsync.zip`](https://github.com/fifthy52/kodi-cloudsync/releases/latest/download/repository.cloudsync.zip)
2. In Kodi: Settings → Add-ons → Install from zip file → Select repository zip
3. Go to Install from repository → CloudSync Repository → Service add-ons → CloudSync → Install
4. **Automatic updates** - Future versions will update automatically!

### Option 2: Direct Install
1. Go to [Releases](https://github.com/fifthy52/kodi-cloudsync/releases)
2. Download the latest `service.cloudsync-x.x.x.zip`
3. In Kodi: Settings → Add-ons → Install from zip file
4. Select the downloaded zip file
5. ⚠️ No automatic updates - must manually update each version

## ⚙️ Configuration

### 🌟 Simple Web Setup (Only Method)
1. Go to CloudSync settings in Kodi
2. Click "✨ Simple Web Setup"
3. Open the displayed URL in any browser on your network
4. Complete Dropbox authorization in browser
5. Addon automatically configures itself - done!

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

- **v4.2.0** - Simplified settings UI, automated repository system, documented favorites limitations
- **v4.1.2** - Fixed dialog overlaps, improved web setup UX
- **v4.1.0** - Added Simple Web Setup with paste interface
- **v4.0.0** - Revolutionary web interface for OAuth2 setup
- **v2.7.0** - Real scannable QR codes for mobile setup

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
