"""
MAVLink to MQTT Bridge
======================
Role: Connects ArduPilot/PX4 to the SecuringSkies Bus.
Input: UDP:14550 (Standard MAVLink)
Output: MQTT 'pixhawk/telemetry'
"""

import time
import json
import os
import sys

# flexible dependency import
try:
    from pymavlink import mavutil
    import paho.mqtt.client as mqtt
except ImportError:
    print("❌ MISSING DEPS: pip install pymavlink paho-mqtt")
    sys.exit(1)

# CONFIGURATION
MAV_CONNECTION = os.getenv("MAV_ADDR", "udpin:0.0.0.0:14550")
MQTT_BROKER = os.getenv("MQTT_BROKER", "192.168.1.100")
TOPIC = "pixhawk/telemetry"

def main():
    print(f"🔌 MAVLINK BRIDGE: Listening on {MAV_CONNECTION}...")
    
    # 1. Connect to Drone
    try:
        # source_system=255 means we are a GCS (Ground Control Station)
        vehicle = mavutil.mavlink_connection(MAV_CONNECTION, source_system=255)
        print("   -> Waiting for HEARTBEAT...")
        vehicle.wait_heartbeat()
        print(f"✅ HEARTBEAT RECEIVED from System {vehicle.target_system}")
    except Exception as e:
        print(f"❌ MAVLINK ERROR: {e}")
        return

    # 2. Connect to MQTT
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    try:
        client.connect(MQTT_BROKER, 1883, 60)
        client.loop_start()
        print(f"✅ MQTT CONNECTED to {MQTT_BROKER}")
    except Exception as e:
        print(f"❌ MQTT ERROR: {e}")
        return

    print("🚀 BRIDGE ACTIVE: Forwarding Telemetry...")

    while True:
        try:
            # Fetch message (non-blocking)
            msg = vehicle.recv_match(blocking=True, timeout=1.0)
            if not msg: continue

            # Filter for Position Data
            if msg.get_type() == 'GLOBAL_POSITION_INT':
                # Decode (MAVLink uses integers for lat/lon, e.g. 600000000)
                lat = msg.lat / 1e7
                lon = msg.lon / 1e7
                alt = msg.alt / 1000.0
                heading = msg.hdg / 100.0
                
                # Create Standard JSON Packet
                payload = {
                    "tid": f"PX4-{vehicle.target_system}",
                    "lat": lat,
                    "lon": lon,
                    "alt": alt,
                    "heading": heading,
                    "icon": "helicopter",  # Forces Orange Icon
                    "type": "MAVLINK_DRONE",
                    "batt": -1 # MAVLink battery is in SYS_STATUS, strictly parsing pos for now
                }
                
                client.publish(TOPIC, json.dumps(payload))

        except Exception as e:
            print(f"⚠️ Bridge Error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()
