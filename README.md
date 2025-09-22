# CloudSync V3 for Kodi

Robust synchronization of watched status, resume points, and favorites across multiple Kodi devices using advanced MQTT messaging with full offline support. Features persistent sessions, message retention, and automatic reconnect sync.

## ✨ Features

### 🔄 Core Sync Capabilities
- **Real-time Watched Status Sync** - Instant movie/episode playcount updates across devices
- **Resume Points Sync** - Continue watching from exact position on any device
- **Add-only Favorites Sync** - V3 anti-loop protection prevents sync wars between devices
- **Manual Favorites Master Publishing** - Complete favorites synchronization when needed

### 🌐 Advanced MQTT Architecture
- **Full Offline Support** - MQTT 5.0 with persistent sessions and message retention
- **QoS 1 Delivery Guarantee** - Critical data (watched/resume) with 30-day message expiry
- **Automatic Reconnect Sync** - Get missed updates instantly when devices come back online
- **Smart Message Persistence** - Different expiry times based on data importance
- **HiveMQ Cloud Integration** - Secure SSL/TLS cloud messaging

### 🔧 User Experience
- **Web Configuration Interface** - Easy MQTT setup via browser instead of TV remote
- **Zero-Conflict Architecture** - No databases, no file conflicts
- **Event-Driven Design** - React instantly to Kodi library changes
- **Automatic Settings Reload** - Web server starts/stops instantly when settings change

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

### 🌐 Web Configuration (V3 Feature!)
1. Go to CloudSync settings in Kodi
2. Enable **"Web Configuration"** in MQTT Configuration section
3. Open your browser and go to `http://[kodi-ip]:8090`
4. Configure MQTT settings easily through the web interface:
   - **Broker Host**: Your MQTT broker (e.g., HiveMQ Cloud)
   - **Port**: 8883 (SSL/TLS) or 1883 (plain)
   - **Username/Password**: Your MQTT credentials
   - **SSL/TLS**: Enable for secure connections

### 📱 Traditional Setup (TV Remote)
1. Go to CloudSync settings in Kodi → MQTT Configuration
2. Configure MQTT broker settings directly in Kodi
3. Enable CloudSync and restart Kodi

### 🔄 Sync Features
- **Watched Status** - Real-time movie/episode watch status
- **Resume Points** - Video playback positions
- **Favorites** - Add-only sync with anti-loop protection (V3)

## 🏗️ Architecture

CloudSync V3 uses a pure MQTT-first architecture:

- **Event-Driven**: Responds to Kodi notifications instantly
- **Anti-Loop Protection**: V3 prevents sync wars with 10-second grace period
- **Web Server Integration**: Built-in HTTP server for easy configuration
- **Lightweight**: MQTT messages for minimal network overhead
- **Reliable**: HiveMQ Cloud with SSL/TLS encryption
- **Scalable**: Add unlimited Kodi devices to sync network

## 📡 Offline Support

CloudSync V3.3.0+ includes comprehensive offline support:

### How It Works
- **Persistent Sessions**: Devices maintain connection state even when offline
- **Message Retention**: MQTT broker stores missed messages for offline devices
- **Automatic Recovery**: When devices reconnect, they automatically receive all missed updates
- **Smart Expiry**: Messages persist for different durations based on importance:
  - Watched/Resume data: 30 days
  - Favorites events: 7 days
  - Device status: 1 day

### Manual Sync Options
- **Automatic**: No action needed - reconnect triggers automatic sync
- **Favorites Master**: Use "Publish All My Favorites" to send complete favorites list to all devices

### QoS Levels
- **Watched/Resume**: QoS 1 (at least once delivery) with message retention
- **Favorites**: QoS 1 (delivery guarantee) without retention (event-based)
- **Device Status**: QoS 0 (best effort) with retention for last known state

## 🔄 Version History

- **v3.3.0** - Full offline support with MQTT 5.0, persistent sessions, message retention, simplified sync architecture
- **v3.2.2** - Clean settings interface, removed duplicate fields
- **v3.2.1** - Automatic web server restart on settings change
- **v3.2.0** - Web configuration interface for easy MQTT setup
- **v3.1.0** - Production-ready with optimized logging
- **v3.0.0** - Add-only favorites sync with anti-loop protection
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
│       ├── favorites_sync.py    # V3 add-only favorites sync
│       ├── web_config.py        # V3 web configuration server
│       └── paho/               # Embedded Paho MQTT library
```

### Building from Source
```bash
git clone https://github.com/fifthy52/kodi-cloudsync.git
cd kodi-cloudsync
zip -r service.cloudsync-dev.zip service.cloudsync/
```

### V3 Key Features

#### 🌐 Web Configuration Server
- Built-in HTTP server on port 8090 (configurable)
- Browser-based MQTT configuration interface
- Automatic server start/stop when settings change
- No need to restart addon when enabling web config

#### 🔒 Anti-Loop Protection
- 10-second grace period prevents sync wars
- Add-only favorites sync (no automatic removals)
- Device-specific tracking of recently received favorites
- Eliminates infinite sync loops between devices

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
