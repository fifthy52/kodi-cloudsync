# MQTT Real-time Sync Setup Guide

CloudSync v4.4.0+ supports MQTT-based real-time synchronization as an alternative to the traditional Dropbox database sync approach.

## Benefits of MQTT Sync

- **Real-time**: Changes sync instantly (seconds instead of minutes)
- **Lightweight**: Only changed data is transmitted
- **Reliable**: Battle-tested MQTT protocol
- **Cross-device**: Seamless sync between 2-4 Kodi devices

## HiveMQ Cloud Setup (Recommended)

### Step 1: Create HiveMQ Cloud Account

1. Go to [HiveMQ Cloud Console](https://console.hivemq.cloud/)
2. Sign up for a free account (no credit card required)
3. Create a new cluster:
   - Choose **Free tier** (100 connections, 10GB/month)
   - Select region closest to your location
   - Choose a cluster name

### Step 2: Get Connection Details

After cluster creation, note down:
- **Host**: `your-cluster-id.hivemq.cloud`
- **Port**: `8883` (SSL) or `1883` (non-SSL)
- **Username**: Created in cluster management
- **Password**: Generated for username

### Step 3: Configure CloudSync

On **each** Kodi device:

1. Open CloudSync addon settings
2. Go to **MQTT Sync (Beta)** category
3. Configure:
   - ✅ Enable MQTT Real-time Sync: `True`
   - 🌐 MQTT Broker Host: `your-cluster-id.hivemq.cloud`
   - 🔌 MQTT Broker Port: `8883`
   - 👤 MQTT Username: `your-username`
   - 🔑 MQTT Password: `your-password`
   - 🔒 Use SSL/TLS: `True`
4. Click **Test MQTT Connection** to verify
5. Restart CloudSync addon

## Alternative: Self-hosted MQTT

### Synology NAS

```bash
# Docker Compose example
version: '3'
services:
  mosquitto:
    image: eclipse-mosquitto:latest
    container_name: mosquitto
    ports:
      - "1883:1883"
      - "9001:9001"
    volumes:
      - ./mosquitto.conf:/mosquitto/config/mosquitto.conf
      - mosquitto_data:/mosquitto/data
      - mosquitto_logs:/mosquitto/log
volumes:
  mosquitto_data:
  mosquitto_logs:
```

### Raspberry Pi

```bash
# Install Mosquitto
sudo apt update
sudo apt install mosquitto mosquitto-clients

# Start service
sudo systemctl enable mosquitto
sudo systemctl start mosquitto

# Configure authentication (optional)
sudo mosquitto_passwd -c /etc/mosquitto/passwd username
```

## Topic Structure

CloudSync uses the following MQTT topics:

```
cloudsync/
├── devices/{device_id}/status          # Device online/offline
├── sync/watched/movie/{uniqueid}       # Movie watch status changes
├── sync/watched/episode/{uniqueid}     # Episode watch status changes
├── sync/favorites/add                  # Favorites added
└── sync/favorites/remove               # Favorites removed
```

## Message Format

Example watched status change:

```json
{
  "device_id": "kodi_living_room_a1b2c3",
  "timestamp": 1694875200,
  "event_type": "watched_status_changed",
  "content": {
    "type": "movie",
    "uniqueid": {
      "imdb": "tt1234567",
      "tmdb": "12345"
    },
    "title": "Example Movie",
    "playcount": 1,
    "lastplayed": "2024-01-15 20:30:00",
    "resume": {
      "position": 0,
      "total": 7200
    }
  }
}
```

## Troubleshooting

### Connection Issues

1. **Verify broker details**: Double-check host, port, username, password
2. **Check firewall**: Ensure ports 1883/8883 are accessible
3. **SSL problems**: Try disabling SSL temporarily for testing
4. **Network connectivity**: Test from same network first

### Sync Not Working

1. **Check device IDs**: Each device should have unique ID
2. **Monitor logs**: Enable debug logging in CloudSync settings
3. **Verify subscriptions**: Devices should subscribe to sync topics
4. **Test message flow**: Use MQTT client tools to verify message delivery

### Common Errors

- **Authentication failed**: Wrong username/password
- **Connection timeout**: Network/firewall issues
- **SSL handshake failed**: Certificate or SSL configuration problem
- **Topic permission denied**: MQTT broker ACL restrictions

## Performance Notes

- **Free tier limits**: HiveMQ Cloud free tier allows 10GB/month
- **Message size**: CloudSync messages are typically < 1KB each
- **Frequency**: Messages sent only when watched status changes
- **Bandwidth usage**: Very minimal for typical home usage (2-4 devices)

## Hybrid Approach

You can use both MQTT and Dropbox sync simultaneously:

- **MQTT**: Real-time sync for immediate changes
- **Dropbox**: Backup sync and historical data

This provides redundancy and ensures sync even if MQTT is temporarily unavailable.

## Security Considerations

1. **Use SSL/TLS**: Always enable for cloud brokers
2. **Strong passwords**: Use generated passwords from broker
3. **Topic permissions**: Restrict access to CloudSync topics only
4. **Network security**: Use VPN for self-hosted brokers if accessing remotely

## Support

For MQTT-related issues:
- Check CloudSync logs: `/userdata/addon_data/service.cloudsync/`
- Test connection using MQTT client tools
- Verify broker status in HiveMQ Cloud console
- Report issues on [GitHub](https://github.com/fifthy52/kodi-cloudsync/issues)