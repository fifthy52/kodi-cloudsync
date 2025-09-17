# CloudSync for Kodi

Real-time synchronization of watched status, resume points, and favorites across multiple Kodi devices using MQTT messaging. Instant cross-device sync without databases or file conflicts.

## ✨ Features

- **Real-time Watched Status Sync** - Instant movie/episode playcount updates across devices
- **Resume Points Sync** - Continue watching from exact position on any device
- **Favorites Sync** - Real-time favorites synchronization via Kodi API
- **MQTT Messaging** - Lightweight, instant communication between devices
- **HiveMQ Cloud Integration** - Secure SSL/TLS cloud messaging
- **Zero-Conflict Architecture** - No databases, no file conflicts
- **Event-Driven Design** - React instantly to Kodi library changes

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

### MQTT Setup
1. Go to CloudSync settings in Kodi
2. Configure MQTT broker settings:
   - **Broker Host**: Your MQTT broker (e.g., HiveMQ Cloud)
   - **Port**: 8883 (SSL/TLS) or 1883 (plain)
   - **Username/Password**: Your MQTT credentials
   - **Device Name**: Unique name for this Kodi device
3. Enable CloudSync and restart Kodi

### Sync Features
- **Watched Status** - Real-time movie/episode watch status
- **Resume Points** - Video playback positions
- **Favorites** - Favorites menu items (polled every 30 seconds)

## 🏗️ Architecture

CloudSync V2 uses a pure MQTT-first architecture:

- **Event-Driven**: Responds to Kodi notifications instantly
- **Lightweight**: MQTT messages for minimal network overhead
- **Reliable**: HiveMQ Cloud with SSL/TLS encryption
- **Scalable**: Add unlimited Kodi devices to sync network

## 🔄 Version History

- **v2.0.0** - Complete MQTT-first rebuild, real-time sync, favorites support
- **v1.x.x** - Legacy Dropbox-based sync (deprecated)

## 🛠️ Development

### Project Structure
```
service.cloudsync/
├── addon.xml                    # Addon metadata
├── service.py                   # Main service entry point
├── resources/
│   ├── settings.xml             # Settings UI
│   └── lib/                     # Python modules
│       ├── mqtt_client.py       # MQTT wrapper with Paho
│       ├── kodi_monitor.py      # Kodi event monitoring
│       ├── kodi_rpc.py          # JSON-RPC API wrapper
│       └── paho/               # Embedded Paho MQTT library
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

Built with Eclipse Paho MQTT library and HiveMQ Cloud for reliable real-time messaging.

---

**Need help?** Open an [issue](https://github.com/fifthy52/kodi-cloudsync/issues) or check the [discussions](https://github.com/fifthy52/kodi-cloudsync/discussions) for support.
