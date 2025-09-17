#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CloudSync V2 - MQTT Connection Test
Test MQTT connectivity for CloudSync V2 addon
"""

import sys
import os
import time
import json
import xbmc
import xbmcaddon
import xbmcgui

# Add embedded Paho MQTT path
addon_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(addon_dir, 'lib'))

try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False


class CloudSyncMQTTTest:
    """MQTT connection test for CloudSync V2"""

    def __init__(self):
        self.addon = xbmcaddon.Addon('service.cloudsync')
        self.client = None
        self.connected = False
        self.test_results = []

    def log(self, message, level=xbmc.LOGINFO):
        """Log message"""
        xbmc.log(f"CloudSync V2 MQTT Test: {message}", level)
        self.test_results.append(message)

    def test_mqtt_availability(self):
        """Test if MQTT library is available"""
        self.log("Testing MQTT library availability...")

        if MQTT_AVAILABLE:
            self.log("✓ Paho MQTT library is available")
            return True
        else:
            self.log("✗ Paho MQTT library is NOT available", xbmc.LOGERROR)
            return False

    def test_configuration(self):
        """Test MQTT configuration"""
        self.log("Testing MQTT configuration...")

        try:
            broker_host = self.addon.getSetting('mqtt_broker_host').strip()
            broker_port = self.addon.getSetting('mqtt_broker_port').strip()
            username = self.addon.getSetting('mqtt_username').strip()
            password = self.addon.getSetting('mqtt_password').strip()
            use_ssl = self.addon.getSettingBool('mqtt_use_ssl')

            if not broker_host:
                self.log("✗ MQTT broker host not configured")
                return False
            if not username:
                self.log("✗ MQTT username not configured")
                return False
            if not password:
                self.log("✗ MQTT password not configured")
                return False

            self.log(f"✓ Broker: {broker_host}:{broker_port}")
            self.log(f"✓ Username: {username}")
            self.log(f"✓ SSL/TLS: {use_ssl}")

            return True

        except Exception as e:
            self.log(f"✗ Configuration error: {e}", xbmc.LOGERROR)
            return False

    def test_connection(self):
        """Test MQTT connection"""
        if not MQTT_AVAILABLE:
            return False

        self.log("Testing MQTT connection...")

        try:
            # Get settings
            broker_host = self.addon.getSetting('mqtt_broker_host').strip()
            broker_port = int(self.addon.getSetting('mqtt_broker_port') or '8883')
            username = self.addon.getSetting('mqtt_username').strip()
            password = self.addon.getSetting('mqtt_password').strip()
            use_ssl = self.addon.getSettingBool('mqtt_use_ssl')

            # Create client
            device_id = f"cloudsync_test_{int(time.time())}"
            self.client = mqtt.Client(client_id=device_id, protocol=mqtt.MQTTv311)

            # Set credentials and SSL
            self.client.username_pw_set(username, password)
            if use_ssl:
                self.client.tls_set()

            # Set callbacks
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message

            # Connect
            self.log(f"Connecting to {broker_host}:{broker_port}...")
            result = self.client.connect(broker_host, broker_port, 60)

            if result == mqtt.MQTT_ERR_SUCCESS:
                self.log("Connection initiated successfully")

                # Process network events for 10 seconds
                start_time = time.time()
                while time.time() - start_time < 10:
                    self.client.loop(timeout=0.1)
                    time.sleep(0.1)

                # Test publish
                if self.connected:
                    self.test_publish()

                # Disconnect
                self.client.disconnect()
                return self.connected

            else:
                self.log(f"✗ Connection failed with result code: {result}", xbmc.LOGERROR)
                return False

        except Exception as e:
            self.log(f"✗ Connection error: {e}", xbmc.LOGERROR)
            return False

    def _on_connect(self, client, userdata, flags, rc):
        """Connection callback"""
        if rc == 0:
            self.connected = True
            self.log("✓ Successfully connected to MQTT broker")

            # Subscribe to test topic
            client.subscribe("cloudsync/test/+")
            self.log("✓ Subscribed to test topics")

        else:
            self.log(f"✗ Connection failed with return code {rc}", xbmc.LOGERROR)

    def _on_disconnect(self, client, userdata, rc):
        """Disconnection callback"""
        self.connected = False
        if rc == 0:
            self.log("✓ Clean disconnection from MQTT broker")
        else:
            self.log(f"✗ Unexpected disconnection, return code: {rc}", xbmc.LOGWARNING)

    def _on_message(self, client, userdata, message):
        """Message callback"""
        try:
            topic = message.topic
            payload = json.loads(message.payload.decode('utf-8'))
            self.log(f"✓ Received test message on {topic}")
        except Exception as e:
            self.log(f"✗ Error processing message: {e}", xbmc.LOGERROR)

    def test_publish(self):
        """Test message publishing"""
        if not self.connected:
            return False

        self.log("Testing message publishing...")

        try:
            test_message = {
                "device_id": f"test_{int(time.time())}",
                "timestamp": int(time.time()),
                "test_data": "CloudSync V2 MQTT Test"
            }

            result = self.client.publish("cloudsync/test/message", json.dumps(test_message))

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                self.log("✓ Test message published successfully")
                return True
            else:
                self.log(f"✗ Publish failed with result code: {result.rc}", xbmc.LOGERROR)
                return False

        except Exception as e:
            self.log(f"✗ Publish error: {e}", xbmc.LOGERROR)
            return False

    def run_test(self):
        """Run complete MQTT test"""
        self.log("=== CloudSync V2 MQTT Test Started ===")

        # Test sequence
        tests = [
            ("MQTT Library", self.test_mqtt_availability),
            ("Configuration", self.test_configuration),
            ("Connection", self.test_connection)
        ]

        results = {}
        for test_name, test_func in tests:
            try:
                results[test_name] = test_func()
            except Exception as e:
                self.log(f"✗ {test_name} test failed with exception: {e}", xbmc.LOGERROR)
                results[test_name] = False

        # Summary
        self.log("=== Test Results ===")
        all_passed = True
        for test_name, passed in results.items():
            status = "✓ PASSED" if passed else "✗ FAILED"
            self.log(f"{test_name}: {status}")
            if not passed:
                all_passed = False

        if all_passed:
            self.log("=== All Tests PASSED ===")
            message = "CloudSync V2 MQTT Test: All tests PASSED"
        else:
            self.log("=== Some Tests FAILED ===")
            message = "CloudSync V2 MQTT Test: Some tests FAILED - check logs"

        # Show result dialog
        xbmcgui.Dialog().ok("CloudSync V2 MQTT Test", message)

        return all_passed


def main():
    """Main test entry point"""
    test = CloudSyncMQTTTest()
    test.run_test()


if __name__ == '__main__':
    main()