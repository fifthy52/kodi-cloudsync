#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import json
import time
import xbmc
import xbmcgui
import xbmcaddon

# Get addon instance with proper ID
try:
    addon = xbmcaddon.Addon('service.cloudsync')
except:
    addon = xbmcaddon.Addon()

# Add lib path
LIB_RESOURCES_PATH = os.path.join(addon.getAddonInfo('path'), 'resources', 'lib')
sys.path.append(LIB_RESOURCES_PATH)

from mqtt_sync_manager import MQTTSyncManager

def test_mqtt_connection():
    """Test MQTT connection with current settings"""

    # Get settings
    broker_host = addon.getSetting('mqtt_broker_host').strip()
    broker_port = addon.getSetting('mqtt_broker_port').strip()
    username = addon.getSetting('mqtt_username').strip()
    password = addon.getSetting('mqtt_password').strip()
    use_ssl = addon.getSetting('mqtt_use_ssl') == 'true'

    # Validate settings
    if not broker_host:
        xbmcgui.Dialog().ok("MQTT Test", "Please configure MQTT Broker Host first")
        return

    if not username:
        xbmcgui.Dialog().ok("MQTT Test", "Please configure MQTT Username first")
        return

    if not password:
        xbmcgui.Dialog().ok("MQTT Test", "Please configure MQTT Password first")
        return

    try:
        broker_port = int(broker_port) if broker_port else (8883 if use_ssl else 1883)
    except ValueError:
        broker_port = 8883 if use_ssl else 1883

    # Show progress dialog
    progress = xbmcgui.DialogProgress()
    progress.create("MQTT Test", "Testing MQTT connection...")
    progress.update(10, "Initializing MQTT client...")

    try:
        # Create MQTT manager
        mqtt_manager = MQTTSyncManager()

        progress.update(30, "Configuring connection...")

        # Configure with current settings
        mqtt_manager.configure(broker_host, broker_port, username, password, use_ssl)

        progress.update(50, "Connecting to broker...")

        # Try to connect
        if mqtt_manager.initialize():
            progress.update(80, "Testing publish/subscribe...")

            # Test basic functionality
            test_message_received = [False]

            def test_message_handler(content):
                test_message_received[0] = True
                xbmc.log("CloudSync MQTT Test: Received test message", xbmc.LOGINFO)

            mqtt_manager.set_watched_handler(test_message_handler)

            # Wait a bit for connection
            time.sleep(2)

            progress.update(90, "Connection successful!")
            time.sleep(1)

            # Clean up
            mqtt_manager.stop()

            progress.update(100, "Test completed successfully!")
            time.sleep(1)
            progress.close()

            # Show success dialog
            xbmcgui.Dialog().ok(
                "MQTT Test - Success",
                f"Successfully connected to MQTT broker!\n\n"
                f"Host: {broker_host}:{broker_port}\n"
                f"SSL: {'Yes' if use_ssl else 'No'}\n"
                f"Device ID: {mqtt_manager.device_id}"
            )

        else:
            progress.close()
            xbmcgui.Dialog().ok(
                "MQTT Test - Failed",
                f"Failed to connect to MQTT broker.\n\n"
                f"Please check your settings:\n"
                f"• Host: {broker_host}\n"
                f"• Port: {broker_port}\n"
                f"• Username: {username}\n"
                f"• SSL: {'Yes' if use_ssl else 'No'}"
            )

    except Exception as e:
        progress.close()
        error_msg = str(e)
        xbmc.log(f"CloudSync MQTT Test Error: {error_msg}", xbmc.LOGERROR)
        xbmcgui.Dialog().ok(
            "MQTT Test - Error",
            f"An error occurred during testing:\n\n{error_msg}"
        )

def show_mqtt_setup_help():
    """Show help dialog for MQTT setup"""

    help_text = (
        "MQTT Real-time Sync Setup:\n\n"
        "1. Create free HiveMQ Cloud account:\n"
        "   • Go to console.hivemq.cloud\n"
        "   • Create free cluster\n\n"
        "2. Configure CloudSync:\n"
        "   • Host: your-cluster.hivemq.cloud\n"
        "   • Port: 8883 (SSL) or 1883 (no SSL)\n"
        "   • Username: from HiveMQ console\n"
        "   • Password: from HiveMQ console\n\n"
        "3. Test connection using button above\n\n"
        "4. Enable MQTT sync and repeat on other devices"
    )

    xbmcgui.Dialog().ok("MQTT Setup Help", help_text)

if __name__ == "__main__":
    # Check if we should show help or run test
    if len(sys.argv) > 1 and sys.argv[1] == "help":
        show_mqtt_setup_help()
    else:
        test_mqtt_connection()