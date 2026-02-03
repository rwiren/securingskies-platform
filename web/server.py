"""
SecuringSkies Unified Bridge v1.3.5
===================================
Fixes: 
1. Reads CESIUM_TOKEN from .env
2. Passes token securely to HTML
3. Uses Gevent for stability
"""
from gevent import monkey
monkey.patch_all()

import os
import json
import logging
import time
from threading import Lock
from flask import Flask, render_template
from flask_socketio import SocketIO
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

# 1. CONFIGURATION
# Force load .env from project root (one level up from 'web/')
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(base_dir, '.env'))

MQTT_BROKER = os.getenv("MQTT_BROKER", "192.168.192.100") 
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_USER = os.getenv("MQTT_USERNAME")
MQTT_PASS = os.getenv("MQTT_PASSWORD")
CESIUM_TOKEN = os.getenv("CESIUM_TOKEN", "") # <--- LOADED HERE

TOPICS = [("owntracks/#", 0), ("dronetag/#", 0), ("thing/product/#", 0), ("pixhawk/#", 0)]

# 2. SERVER
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger("TacticalServer")

fleet_state = {}
thread_lock = Lock()

# 3. PARSING LOGIC
def find_val_recursive(data, targets):
    if isinstance(data, dict):
        for k, v in data.items():
            if k.lower() in targets: return v
            if isinstance(v, (dict, list)):
                found = find_val_recursive(v, targets)
                if found is not None: return found
    elif isinstance(data, list):
        for item in data:
            found = find_val_recursive(item, targets)
            if found is not None: return found
    return None

def get_telemetry(payload):
    lat = find_val_recursive(payload, ["lat", "latitude", "gps_lat"])
    lon = find_val_recursive(payload, ["lon", "longitude", "gps_lon"])
    alt = find_val_recursive(payload, ["height", "alt", "altitude", "ned_altitude", "rel_alt"])
    if alt is None: alt = 0.0
    return lat, lon, alt

# 4. MQTT LOGIC
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        logger.info(f"✅ UPLINK ESTABLISHED: {MQTT_BROKER}")
        client.subscribe("#")
    else:
        logger.error(f"❌ UPLINK FAILED: {rc}")

def on_message(client, userdata, msg):
    global fleet_state
    try:
        topic = msg.topic
        payload = json.loads(msg.payload.decode())
        try: payload = json.loads(msg.payload.decode())
        except: return

        lat, lon, alt = get_telemetry(payload)
        tid = topic.split('/')[-1]
        icon = "question"
        
        if "owntracks" in topic:
            if payload.get("_type") != "location": return
            tid = payload.get("tid", tid)
            icon = "mobile"
        elif "dronetag" in topic:
            tid = payload.get("id", "RID")
            icon = "plane"
        elif "product" in topic:
            parts = topic.split('/')
            if len(parts) >= 3: tid = parts[2]
            if tid.startswith("TH"): icon = "controller"; tid += "-RC"; alt = 0
            else: icon = "helicopter"

        if lat is not None and lon is not None:
            if abs(float(lat)) > 1.0: 
                with thread_lock:
                    fleet_state[tid] = {
                        "tid": tid, "lat": float(lat), "lon": float(lon), 
                        "alt": float(alt), "icon": icon, "ts": time.time()
                    }
                    socketio.emit('update', fleet_state[tid])
    except: pass 

# 5. ROUTE
@app.route('/')
def index():
    # INJECT TOKEN INTO HTML
    return render_template('unified_map.html', cesium_token=CESIUM_TOKEN)

# 6. LAUNCH
def start_mqtt():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message
    if MQTT_USER and MQTT_PASS: client.username_pw_set(MQTT_USER, MQTT_PASS)
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
    except Exception as e:
        logger.critical(f"🔥 MQTT FAIL: {e}")

if __name__ == '__main__':
    start_mqtt()
    logger.info(f"🚀 UNIFIED DASHBOARD: http://localhost:5000")
    socketio.run(app, host='0.0.0.0', port=5000)
