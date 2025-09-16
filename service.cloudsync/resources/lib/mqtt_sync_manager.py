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

# Import paho MQTT client
try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False


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
            if not MQTT_AVAILABLE:
                self.log.error("Paho MQTT library not available")
                return False

            broker_host = self.addon.getSetting('mqtt_broker_host')
            broker_port = int(self.addon.getSetting('mqtt_broker_port') or '8883')
            username = self.addon.getSetting('mqtt_username')
            password = self.addon.getSetting('mqtt_password')
            use_ssl = self.addon.getSetting('mqtt_use_ssl') == 'true'

            if not broker_host or not username:
                self.log.warning("MQTT not configured - missing broker host or username")
                return False

            # Create Paho MQTT client with Kodi-compatible legacy API
            self.client = mqtt.Client(
                client_id=f"cloudsync_{self.device_id}",
                protocol=mqtt.MQTTv311
            )
            self.log.debug("Created MQTT client with legacy API for Kodi compatibility")

            # Set credentials
            self.client.username_pw_set(username, password)

            # Set SSL/TLS
            if use_ssl:
                self.client.tls_set()

            # Set callbacks
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message

            # Connect with Kodi-compatible approach (no background threading)
            self.log.info(f"Connecting to MQTT broker {broker_host}:{broker_port}")

            # Set additional client options for stability
            self.client.max_inflight_messages_set(20)
            self.client.max_queued_messages_set(0)

            result = self.client.connect(broker_host, broker_port, 60)

            if result == mqtt.MQTT_ERR_SUCCESS:
                self.log.info("MQTT client connected successfully (manual loop mode)")
                # NOTE: No loop_start() - we'll use manual loop in service
                return True
            else:
                self.log.error(f"Failed to connect to MQTT broker, result code: {result}")
                return False

        except Exception as e:
            self.log.error(f"Failed to initialize MQTT: {e}")

        return False

    def _on_connect(self, client, userdata, flags, rc):
        """Called when client connects to broker"""
        if rc == mqtt.MQTT_ERR_SUCCESS or rc == 0:  # Both success codes
            self.connected = True
            self.log.info(f"Connected to MQTT broker successfully (rc={rc})")
            try:
                self._subscribe_to_topics()
                self._publish_device_status("online")
            except Exception as e:
                self.log.error(f"Error in post-connection setup: {e}")
        else:
            self.connected = False
            self.log.error(f"Failed to connect to MQTT broker, return code {rc}")

    def _on_disconnect(self, client, userdata, rc):
        """Called when client disconnects from broker"""
        self.connected = False
        if rc != mqtt.MQTT_ERR_SUCCESS:
            self.log.warning(f"Unexpected disconnection from MQTT broker, return code {rc}")
            # Don't try to reconnect automatically for now - let Kodi handle it
        else:
            self.log.info("Disconnected from MQTT broker")

    def _on_message(self, client, userdata, message):
        """Called when message received"""
        try:
            topic = message.topic
            payload_str = message.payload.decode('utf-8')
            payload = json.loads(payload_str)

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

    def process_network(self):
        """Process MQTT network events - call this regularly from main service loop"""
        if not self.client or not self.enabled:
            return

        try:
            # Manual network loop - non-blocking with short timeout
            self.client.loop(timeout=0.1)
        except Exception as e:
            self.log.error(f"Error in MQTT network processing: {e}")

    def stop(self):
        """Stop MQTT sync"""
        self.enabled = False
        if self.client and self.connected:
            self._publish_device_status("offline")
            # No loop_stop() needed - we use manual loop
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