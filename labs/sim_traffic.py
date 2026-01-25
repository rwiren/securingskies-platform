"""
SecuringSkies Traffic Simulator
===============================
Generates fake Autel and DroneTag MQTT traffic for testing the Dashboard.
"""
import time
import json
import math
import os
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

load_dotenv()
BROKER = os.getenv("MQTT_BROKER", "192.168.1.100")
CENTER_LAT = 60.3195
CENTER_LON = 24.8310

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.connect(BROKER, 1883, 60)

print(f"🎮 SIMULATOR ACTIVE: Targeting {BROKER}")
print("   - 🔴 DroneTag (Red)")
print("   - 🟠 Autel V3 (Orange)")

angle = 0
try:
    while True:
        # 1. Autel Drone (Orange) - Flies in a circle
        autel_lat = CENTER_LAT + 0.001 * math.cos(angle)
        autel_lon = CENTER_LON + 0.001 * math.sin(angle)
        autel_payload = {
            "lat": autel_lat, "lon": autel_lon, 
            "alt": 120, "batt": 88, "sat": 16
        }
        client.publish("thing/product/1748FEV3HMM825451479/osd", json.dumps(autel_payload))

        # 2. DroneTag (Red) - Flies closer, faster
        dt_lat = CENTER_LAT + 0.0005 * math.sin(angle * 2)
        dt_lon = CENTER_LON + 0.0005 * math.cos(angle * 2)
        dt_payload = {
            "id": "DT-1234", "lat": dt_lat, "lon": dt_lon, "alt": 50
        }
        client.publish("dronetag/telemetry", json.dumps(dt_payload))

        print(f"📡 Sent Packets | Angle: {angle:.2f}", end="\r")
        angle += 0.1
        time.sleep(0.5)

except KeyboardInterrupt:
    print("\n🛑 Simulation Stopped.")
