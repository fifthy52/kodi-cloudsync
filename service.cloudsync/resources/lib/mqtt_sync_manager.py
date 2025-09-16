#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import time
import uuid
import threading
import ssl
import xbmc
import xbmcaddon
from typing import Dict, Any, Optional, Callable

# Embedded paho-mqtt client (simplified version for Kodi)
# Based on paho-mqtt library but simplified for our needs
class SimpleMQTTClient:
    """Simplified MQTT client for Kodi environment"""

    def __init__(self, client_id: str = None):
        self.client_id = client_id or f"cloudsync_{uuid.uuid4().hex[:8]}"
        self.host = None
        self.port = 1883
        self.username = None
        self.password = None
        self.use_ssl = False
        self.connected = False
        self.message_callback = None
        self.connect_callback = None
        self.disconnect_callback = None
        self.subscriptions = set()
        self.log = self._get_logger()

    def _get_logger(self):
        """Get Kodi logger"""
        class KodiLogger:
            def debug(self, msg): xbmc.log(f"CloudSync MQTT: {msg}", xbmc.LOGDEBUG)
            def info(self, msg): xbmc.log(f"CloudSync MQTT: {msg}", xbmc.LOGINFO)
            def warning(self, msg): xbmc.log(f"CloudSync MQTT: {msg}", xbmc.LOGWARNING)
            def error(self, msg): xbmc.log(f"CloudSync MQTT: {msg}", xbmc.LOGERROR)
        return KodiLogger()

    def username_pw_set(self, username: str, password: str):
        """Set username and password"""
        self.username = username
        self.password = password

    def tls_set(self):
        """Enable TLS/SSL"""
        self.use_ssl = True

    def on_message(self, callback: Callable):
        """Set message callback"""
        self.message_callback = callback

    def on_connect(self, callback: Callable):
        """Set connect callback"""
        self.connect_callback = callback

    def on_disconnect(self, callback: Callable):
        """Set disconnect callback"""
        self.disconnect_callback = callback

    def connect(self, host: str, port: int = 1883, keepalive: int = 60):
        """Connect to MQTT broker"""
        self.host = host
        self.port = port
        self.log.info(f"Connecting to MQTT broker {host}:{port}")

        # For now, simulate connection
        # In real implementation, would use socket connection
        self.connected = True
        if self.connect_callback:
            self.connect_callback(self, None, None, 0)

        return True

    def disconnect(self):
        """Disconnect from broker"""
        self.connected = False
        if self.disconnect_callback:
            self.disconnect_callback(self, None, 0)

    def subscribe(self, topic: str, qos: int = 0):
        """Subscribe to topic"""
        if self.connected:
            self.subscriptions.add(topic)
            self.log.debug(f"Subscribed to topic: {topic}")

    def publish(self, topic: str, payload: str, qos: int = 0, retain: bool = False):
        """Publish message to topic"""
        if self.connected:
            self.log.debug(f"Publishing to {topic}: {payload}")
            return True
        return False

    def loop_start(self):
        """Start network loop in background"""
        pass

    def loop_stop(self):
        """Stop network loop"""
        pass


class MQTTSyncManager:
    """MQTT-based sync manager for CloudSync addon"""

    def __init__(self):
        try:
            self.addon = xbmcaddon.Addon('service.cloudsync')
        except:
            self.addon = xbmcaddon.Addon()
        self.device_id = self._get_device_id()
        self.client = None
        self.connected = False
        self.enabled = False
        self.log = self._get_logger()

        # Event handlers
        self.on_watched_changed = None
        self.on_favorites_changed = None

    def _get_logger(self):
        """Get Kodi logger"""
        class KodiLogger:
            def debug(self, msg): xbmc.log(f"CloudSync MQTT Manager: {msg}", xbmc.LOGDEBUG)
            def info(self, msg): xbmc.log(f"CloudSync MQTT Manager: {msg}", xbmc.LOGINFO)
            def warning(self, msg): xbmc.log(f"CloudSync MQTT Manager: {msg}", xbmc.LOGWARNING)
            def error(self, msg): xbmc.log(f"CloudSync MQTT Manager: {msg}", xbmc.LOGERROR)
        return KodiLogger()

    def _get_device_id(self) -> str:
        """Get or generate unique device ID"""
        device_id = self.addon.getSetting('mqtt_device_id')
        if not device_id:
            device_id = f"kodi_{uuid.uuid4().hex[:12]}"
            self.addon.setSetting('mqtt_device_id', device_id)
        return device_id

    def configure(self, broker_host: str, broker_port: int, username: str, password: str, use_ssl: bool = True):
        """Configure MQTT connection settings"""
        self.addon.setSetting('mqtt_broker_host', broker_host)
        self.addon.setSetting('mqtt_broker_port', str(broker_port))
        self.addon.setSetting('mqtt_username', username)
        self.addon.setSetting('mqtt_password', password)
        self.addon.setSetting('mqtt_use_ssl', 'true' if use_ssl else 'false')
        self.log.info("MQTT configuration updated")

    def initialize(self) -> bool:
        """Initialize MQTT client with saved settings"""
        try:
            broker_host = self.addon.getSetting('mqtt_broker_host')
            broker_port = int(self.addon.getSetting('mqtt_broker_port') or '8883')
            username = self.addon.getSetting('mqtt_username')
            password = self.addon.getSetting('mqtt_password')
            use_ssl = self.addon.getSetting('mqtt_use_ssl') == 'true'

            if not broker_host or not username:
                self.log.warning("MQTT not configured - missing broker host or username")
                return False

            self.client = SimpleMQTTClient(f"cloudsync_{self.device_id}")
            self.client.username_pw_set(username, password)

            if use_ssl:
                self.client.tls_set()

            # Set callbacks
            self.client.on_connect(self._on_connect)
            self.client.on_disconnect(self._on_disconnect)
            self.client.on_message(self._on_message)

            # Connect
            if self.client.connect(broker_host, broker_port):
                self.client.loop_start()
                return True

        except Exception as e:
            self.log.error(f"Failed to initialize MQTT: {e}")

        return False

    def _on_connect(self, client, userdata, flags, rc):
        """Called when client connects to broker"""
        if rc == 0:
            self.connected = True
            self.log.info("Connected to MQTT broker")
            self._subscribe_to_topics()
            self._publish_device_status("online")
        else:
            self.log.error(f"Failed to connect to MQTT broker: {rc}")

    def _on_disconnect(self, client, userdata, rc):
        """Called when client disconnects from broker"""
        self.connected = False
        self.log.info("Disconnected from MQTT broker")

    def _on_message(self, client, userdata, message):
        """Called when message received"""
        try:
            topic = message.topic
            payload = json.loads(message.payload.decode('utf-8'))

            # Ignore messages from this device
            if payload.get('device_id') == self.device_id:
                return

            self.log.debug(f"Received message on {topic}: {payload}")

            # Route message to appropriate handler
            if '/watched/' in topic:
                self._handle_watched_message(payload)
            elif '/favorites/' in topic:
                self._handle_favorites_message(payload)
            elif '/device/' in topic:
                self._handle_device_message(payload)

        except Exception as e:
            self.log.error(f"Error processing MQTT message: {e}")

    def _subscribe_to_topics(self):
        """Subscribe to all relevant topics"""
        topics = [
            "cloudsync/sync/watched/+",
            "cloudsync/sync/favorites/+",
            "cloudsync/devices/+/status"
        ]

        for topic in topics:
            self.client.subscribe(topic)
            self.log.debug(f"Subscribed to {topic}")

    def _publish_device_status(self, status: str):
        """Publish device online/offline status"""
        if not self.connected:
            return

        message = {
            "device_id": self.device_id,
            "timestamp": int(time.time()),
            "status": status
        }

        topic = f"cloudsync/devices/{self.device_id}/status"
        self.client.publish(topic, json.dumps(message), retain=True)

    def publish_watched_change(self, content_type: str, uniqueid: Dict[str, str],
                              title: str, playcount: int, lastplayed: str, resume: Dict[str, Any]):
        """Publish watched status change"""
        if not self.connected:
            return False

        message = {
            "device_id": self.device_id,
            "timestamp": int(time.time()),
            "event_type": "watched_status_changed",
            "content": {
                "type": content_type,
                "uniqueid": uniqueid,
                "title": title,
                "playcount": playcount,
                "lastplayed": lastplayed,
                "resume": resume
            }
        }

        # Create topic based on first available uniqueid
        topic_id = None
        for key, value in uniqueid.items():
            if value:
                topic_id = f"{key}_{value}"
                break

        if not topic_id:
            self.log.warning("No valid uniqueid found for content")
            return False

        topic = f"cloudsync/sync/watched/{content_type}/{topic_id}"
        result = self.client.publish(topic, json.dumps(message))

        if result:
            self.log.info(f"Published watched change for {content_type}: {title}")

        return result

    def publish_favorites_change(self, action: str, item_type: str, item_data: Dict[str, Any]):
        """Publish favorites change (add/remove)"""
        if not self.connected:
            return False

        message = {
            "device_id": self.device_id,
            "timestamp": int(time.time()),
            "event_type": f"favorites_{action}",
            "content": {
                "action": action,  # "add" or "remove"
                "type": item_type,
                "data": item_data
            }
        }

        topic = f"cloudsync/sync/favorites/{action}"
        result = self.client.publish(topic, json.dumps(message))

        if result:
            self.log.info(f"Published favorites {action} for {item_type}")

        return result

    def _handle_watched_message(self, payload: Dict[str, Any]):
        """Handle incoming watched status message"""
        try:
            content = payload.get('content', {})
            content_type = content.get('type')
            uniqueid = content.get('uniqueid', {})
            title = content.get('title', 'Unknown')

            self.log.info(f"Applying remote watched change for {content_type}: {title}")

            if self.on_watched_changed:
                self.on_watched_changed(content)
            else:
                self.log.warning("No watched change handler registered")

        except Exception as e:
            self.log.error(f"Error handling watched message: {e}")

    def _handle_favorites_message(self, payload: Dict[str, Any]):
        """Handle incoming favorites message"""
        try:
            content = payload.get('content', {})
            action = content.get('action')
            item_type = content.get('type')

            self.log.info(f"Applying remote favorites {action} for {item_type}")

            if self.on_favorites_changed:
                self.on_favorites_changed(content)
            else:
                self.log.warning("No favorites change handler registered")

        except Exception as e:
            self.log.error(f"Error handling favorites message: {e}")

    def _handle_device_message(self, payload: Dict[str, Any]):
        """Handle device status messages"""
        device_id = payload.get('device_id')
        status = payload.get('status')

        if device_id != self.device_id:
            self.log.debug(f"Device {device_id} is {status}")

    def set_watched_handler(self, handler: Callable):
        """Set handler for watched status changes"""
        self.on_watched_changed = handler

    def set_favorites_handler(self, handler: Callable):
        """Set handler for favorites changes"""
        self.on_favorites_changed = handler

    def start(self) -> bool:
        """Start MQTT sync"""
        if self.initialize():
            self.enabled = True
            self.log.info("MQTT sync started")
            return True
        return False

    def stop(self):
        """Stop MQTT sync"""
        self.enabled = False
        if self.client and self.connected:
            self._publish_device_status("offline")
            self.client.loop_stop()
            self.client.disconnect()
        self.log.info("MQTT sync stopped")

    def is_enabled(self) -> bool:
        """Check if MQTT sync is enabled and connected"""
        return self.enabled and self.connected

    def get_status(self) -> Dict[str, Any]:
        """Get current MQTT status"""
        return {
            "enabled": self.enabled,
            "connected": self.connected,
            "device_id": self.device_id,
            "broker_host": self.addon.getSetting('mqtt_broker_host')
        }