#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CloudSync V3 - MQTT Client Wrapper
Clean, simple MQTT client designed specifically for Kodi real-time sync
"""

import json
import time
import uuid
import xbmc
import xbmcaddon
from typing import Dict, Any, Optional, Callable

# Import embedded Paho MQTT
try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    xbmc.log("CloudSync V3: Paho MQTT not available", xbmc.LOGERROR)


class CloudSyncMQTT:
    """Clean MQTT client wrapper for CloudSync V3"""

    def __init__(self):
        self.addon = self._get_addon()
        self.device_id = self._get_device_id()
        self.client = None
        self.connected = False
        self.enabled = False
        self.message_handlers = {}

        # Connection settings
        self.broker_host = ""
        self.broker_port = 8883
        self.username = ""
        self.password = ""
        self.use_ssl = True

    def _get_addon(self):
        """Get addon instance with error handling"""
        try:
            return xbmcaddon.Addon('service.cloudsync')
        except:
            return xbmcaddon.Addon()

    def _get_device_id(self) -> str:
        """Get or generate unique device ID"""
        device_id = self.addon.getSetting('mqtt_device_id')
        if not device_id:
            # Generate unique device ID
            device_name = self.addon.getSetting('device_name').strip()
            if device_name:
                device_id = f"cloudsync_{device_name.lower().replace(' ', '_')}"
            else:
                device_id = f"cloudsync_{uuid.uuid4().hex[:8]}"

            self.addon.setSetting('mqtt_device_id', device_id)
            xbmc.log(f"CloudSync V3: Generated device ID: {device_id}", xbmc.LOGINFO)

        return device_id

    def _log(self, message: str, level: int = xbmc.LOGINFO):
        """Centralized logging"""
        xbmc.log(f"CloudSync V3 MQTT: {message}", level)

    def configure(self) -> bool:
        """Load MQTT configuration from addon settings"""
        try:
            self.broker_host = self.addon.getSetting('mqtt_broker_host').strip()
            self.broker_port = int(self.addon.getSetting('mqtt_broker_port') or '8883')
            self.username = self.addon.getSetting('mqtt_username').strip()
            self.password = self.addon.getSetting('mqtt_password').strip()
            self.use_ssl = self.addon.getSettingBool('mqtt_use_ssl')

            if not self.broker_host or not self.username or not self.password:
                self._log("MQTT not configured - missing broker host, username, or password", xbmc.LOGWARNING)
                return False

            self._log("MQTT configuration loaded successfully", xbmc.LOGDEBUG)
            return True

        except Exception as e:
            self._log(f"Error loading MQTT configuration: {e}", xbmc.LOGERROR)
            return False

    def connect(self) -> bool:
        """Connect to MQTT broker"""
        if not MQTT_AVAILABLE:
            self._log("Paho MQTT library not available", xbmc.LOGERROR)
            return False

        if not self.configure():
            return False

        try:
            # Create MQTT client with MQTT 5.0 for offline support
            # Use clean sessions to avoid "session taken over" conflicts
            # The broker's retained messages will handle offline sync automatically
            import os
            import time
            unique_client_id = f"{self.device_id}_t{int(time.time())}_pid{os.getpid()}"

            # DEBUG: Log the client ID being used
            self._log(f"Using MQTT client ID: {unique_client_id}", xbmc.LOGINFO)

            self.client = mqtt.Client(
                mqtt.CallbackAPIVersion.VERSION1,
                client_id=unique_client_id,
                protocol=mqtt.MQTTv5       # MQTT 5.0 for message expiry support
            )

            # Use clean sessions to prevent session conflicts
            # MQTT retained messages will handle offline sync
            self.client.clean_start = True

            # No session expiry needed with clean sessions
            # Offline sync is handled by MQTT retained messages

            # Set credentials
            self.client.username_pw_set(self.username, self.password)

            # Set SSL/TLS
            if self.use_ssl:
                self.client.tls_set()

            # Set callbacks
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message

            # Connection options for stability
            self.client.max_inflight_messages_set(20)
            self.client.max_queued_messages_set(0)

            # Connect to broker with proper keepalive
            self._log(f"Connecting to MQTT broker {self.broker_host}:{self.broker_port}")
            result = self.client.connect(self.broker_host, self.broker_port, keepalive=60)

            if result == mqtt.MQTT_ERR_SUCCESS:
                self._log("MQTT client connected successfully")
                # Start background network loop (best practice)
                self.client.loop_start()
                self._log("MQTT background loop started")
                return True
            else:
                self._log(f"Failed to connect to MQTT broker, result code: {result}", xbmc.LOGERROR)
                return False

        except Exception as e:
            self._log(f"Error connecting to MQTT broker: {e}", xbmc.LOGERROR)
            return False

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        """Called when client connects to broker (MQTT 5.0 compatible)"""
        if rc == 0:
            self.connected = True
            self._log(f"Connected to MQTT broker successfully (rc={rc})")

            # Subscribe to all CloudSync topics first
            self._subscribe_to_topics()

            # Log session information for debugging
            if hasattr(flags, 'session_present'):
                self._log(f"Session present: {flags.session_present}", xbmc.LOGDEBUG)

            # Publish device online status after subscription (with small delay)
            # Note: Moving this to _on_subscribe callback would be better
            import threading
            def delayed_status_publish():
                import time
                time.sleep(0.5)  # Small delay to ensure subscription is processed
                if self.connected:
                    self.publish_device_status("online")

            threading.Thread(target=delayed_status_publish, daemon=True).start()

        else:
            self.connected = False
            self._log(f"Failed to connect to MQTT broker, return code {rc}", xbmc.LOGERROR)

    def _on_disconnect(self, client, userdata, rc, properties=None):
        """Called when client disconnects from broker (MQTT 5.0 compatible)"""
        self.connected = False
        if rc != 0:
            self._log(f"Unexpected disconnection from MQTT broker, return code {rc}", xbmc.LOGWARNING)
        else:
            self._log("Disconnected from MQTT broker")

    def _on_message(self, client, userdata, message):
        """Called when message received"""
        try:
            topic = message.topic
            payload_str = message.payload.decode('utf-8')
            payload = json.loads(payload_str)

            # Ignore messages from this device
            if payload.get('device_id') == self.device_id:
                return

            self._log(f"Received message on {topic}", xbmc.LOGDEBUG)

            # Route message to appropriate handler
            for topic_pattern, handler in self.message_handlers.items():
                if topic_pattern in topic:
                    try:
                        handler(topic, payload)
                    except Exception as e:
                        self._log(f"Error in message handler for {topic}: {e}", xbmc.LOGERROR)
                    break

        except Exception as e:
            self._log(f"Error processing MQTT message: {e}", xbmc.LOGERROR)

    def _subscribe_to_topics(self):
        """Subscribe to all CloudSync topics"""
        topics = [
            "cloudsync/watched/+",
            "cloudsync/resume/+",
            "cloudsync/favorites/+",
            "cloudsync/devices/+/status"
        ]

        for topic in topics:
            try:
                self.client.subscribe(topic)
                self._log(f"Subscribed to topic: {topic}", xbmc.LOGDEBUG)
            except Exception as e:
                self._log(f"Error subscribing to {topic}: {e}", xbmc.LOGERROR)

    def get_message_params(self, topic: str) -> tuple:
        """Return (qos, retain, expiry) based on topic type for offline support"""
        if "watched" in topic or "resume" in topic:
            # Critical data: QoS 1, retain for offline devices, 30 days expiry
            return (1, True, 2592000)
        elif "favorites" in topic:
            # Event data: QoS 1 for delivery guarantee, no retain, 7 days expiry
            return (1, False, 604800)
        elif "status" in topic:
            # Status data: QoS 0 (real-time), retain for last known state, 1 day expiry
            return (0, True, 86400)
        else:
            # Default: best effort, no persistence
            return (0, False, None)

    def register_handler(self, topic_pattern: str, handler: Callable):
        """Register message handler for topic pattern"""
        self.message_handlers[topic_pattern] = handler
        self._log(f"Registered handler for topic pattern: {topic_pattern}", xbmc.LOGDEBUG)

    def publish(self, topic: str, payload: Dict[str, Any],
                qos: Optional[int] = None, retain: Optional[bool] = None,
                message_expiry: Optional[int] = None) -> bool:
        """Publish message to MQTT topic with offline support"""
        # Enhanced connection state checking
        if not self.connected or not self.client or not self.client.is_connected():
            self._log("Cannot publish - not connected to MQTT broker", xbmc.LOGWARNING)
            return False

        try:
            # Get message parameters based on topic type if not explicitly provided
            if qos is None or retain is None or message_expiry is None:
                auto_qos, auto_retain, auto_expiry = self.get_message_params(topic)
                qos = qos if qos is not None else auto_qos
                retain = retain if retain is not None else auto_retain
                message_expiry = message_expiry if message_expiry is not None else auto_expiry

            # Add device ID and timestamp
            message = {
                "device_id": self.device_id,
                "timestamp": int(time.time()),
                **payload
            }

            # Create MQTT 5.0 properties for message expiry
            properties = None
            if message_expiry and hasattr(mqtt, 'Properties'):
                try:
                    properties = mqtt.Properties(mqtt.PacketTypes.PUBLISH)
                    properties.MessageExpiryInterval = message_expiry
                except:
                    # Fallback if MQTT 5.0 properties not available
                    self._log(f"MQTT 5.0 properties not available, publishing without expiry", xbmc.LOGDEBUG)

            # Publish message with offline support parameters
            result = self.client.publish(
                topic=topic,
                payload=json.dumps(message),
                qos=qos,
                retain=retain,
                properties=properties
            )

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                self._log(f"Published to {topic} (QoS={qos}, retain={retain}, expiry={message_expiry})", xbmc.LOGDEBUG)
                return True
            else:
                self._log(f"Failed to publish to {topic}, result code: {result.rc}", xbmc.LOGERROR)
                return False

        except Exception as e:
            self._log(f"Error publishing to {topic}: {e}", xbmc.LOGERROR)
            return False

    def publish_device_status(self, status: str):
        """Publish device online/offline status with offline support"""
        topic = f"cloudsync/devices/{self.device_id}/status"
        payload = {"status": status}

        # Use the new publish method with automatic parameter detection
        self.publish(topic, payload)

    def process_network(self):
        """Process MQTT network events - NOT NEEDED with loop_start()"""
        # Background loop handles network processing automatically
        pass

    def disconnect(self):
        """Disconnect from MQTT broker"""
        if self.client and self.connected:
            try:
                # Publish offline status
                self.publish_device_status("offline")

                # Stop background loop first
                self.client.loop_stop()
                self._log("MQTT background loop stopped")

                # Disconnect
                self.client.disconnect()
                self._log("Disconnected from MQTT broker")

            except Exception as e:
                self._log(f"Error during disconnect: {e}", xbmc.LOGERROR)

        self.connected = False
        self.enabled = False

    def start(self) -> bool:
        """Start MQTT client"""
        if self.connect():
            self.enabled = True
            self._log("MQTT client started successfully")
            return True
        return False

    def stop(self):
        """Stop MQTT client"""
        self.enabled = False
        self.disconnect()
        self._log("MQTT client stopped")

    def is_connected(self) -> bool:
        """Check if connected to MQTT broker"""
        result = self.connected and self.enabled
        self._log(f"is_connected check: connected={self.connected}, enabled={self.enabled}, result={result}", xbmc.LOGDEBUG)
        return result

    def get_status(self) -> Dict[str, Any]:
        """Get current MQTT status"""
        return {
            "enabled": self.enabled,
            "connected": self.connected,
            "device_id": self.device_id,
            "broker_host": self.broker_host,
            "broker_port": self.broker_port
        }