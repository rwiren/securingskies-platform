"""
SecuringSkies Web Server
========================
Version: 0.9.8 (Nightly)
Role: WebSocket Bridge for Real-Time Tactical Map.
Features:
  - Recursive GPS Extraction (Autel/DroneTag compatibility)
  - Auto-Icon Classification (Blue/Red/Orange/Cyan)
  - Null Island Filtering

Author: Ghost Commander
"""

import eventlet
eventlet.monkey_patch()

import os
import json
import logging
import time
from flask import Flask, render_template
from flask_socketio import SocketIO
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

# 1. CONFIGURATION
# ----------------
load_dotenv()
MQTT_BROKER = os.getenv("MQTT_BROKER", "192.168.1.100") 
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))

# Subscribe to ALL relevant telemetry streams
TOPICS = [
    ("owntracks/#", 0),       # Phones/Team
    ("dronetag/#", 0),        # Remote ID
    ("thing/product/#", 0)    # Autel Enterprise (Control & UAV)
]

# 2. SETUP
# --------
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Reduce noise, keep it professional
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("web.server")

# In-Memory Tactical State
fleet_state = {}

# 3. HELPER FUNCTIONS
# -------------------
def find_val_recursive(data, targets):
    """
    The 'Nuclear Option' for JSON parsing. 
    Recursively hunts for specific keys (lat/lon) anywhere in the data structure.
    Solves the nested 'data.data.gps' issue with Autel.
    """
    if isinstance(data, dict):
        for k, v in data.items():
            if k.lower() in targets:
                return v
            if isinstance(v, (dict, list)):
                found = find_val_recursive(v, targets)
                if found is not None: return found
    elif isinstance(data, list):
        for item in data:
            found = find_val_recursive(item, targets)
            if found is not None: return found
    return None

def get_coords(payload):
    """Extracts standardized Lat/Lon regardless of vendor format."""
    lat = find_val_recursive(payload, ["lat", "latitude", "gps_lat"])
    lon = find_val_recursive(payload, ["lon", "longitude", "gps_lon"])
    return lat, lon

# 4. MQTT HANDLERS
# ----------------
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"✅ DASHBOARD LINKED: {MQTT_BROKER}")
        client.subscribe(TOPICS)
    else:
        logger.error(f"❌ Connection Failed code={rc}")

def on_message(client, userdata, msg):
    global fleet_state
    try:
        topic = msg.topic
        payload = json.loads(msg.payload.decode())
        
        tid = "UNK"
        lat, lon = get_coords(payload)
        icon = "question"
        
        # --- CLASSIFICATION LOGIC ---
        
        # A. OwnTracks (Ground Assets / Phones)
        if "owntracks" in topic:
            tid = payload.get("tid", topic.split("/")[-1])
            icon = "mobile" # Blue
            
        # B. DroneTag (Hostile / Remote ID)
        elif "dronetag" in topic:
            tid = payload.get("id", "RID")
            icon = "plane" # Red

        # C. Autel Enterprise (Mixed Air/Ground)
        elif "thing/product" in topic:
            parts = topic.split('/')
            # Topic format: thing/product/{SN}/{type}
            if len(parts) >= 3:
                tid = parts[2]
            else:
                tid = "AUTEL_UNK"
            
            # Smart Controller vs Drone distinction
            if tid.startswith("TH"): 
                icon = "controller" # Cyan (Ground Pilot)
                tid += " (RC)"
            else:
                icon = "helicopter" # Orange (Air Asset)

        # --- UPDATE STATE ---
        if lat is not None and lon is not None:
            lat = float(lat)
            lon = float(lon)
            
            # Filter "Null Island" (0,0) noise
            if abs(lat) > 1.0: 
                fleet_state[tid] = {
                    "tid": tid, 
                    "lat": lat, 
                    "lon": lon, 
                    "icon": icon, 
                    "last_seen": time.time()
                }
                # Real-time push to Browser
                socketio.emit('update', fleet_state[tid])
            
    except Exception:
        # Silently drop malformed packets to keep server stable
        pass 

# 5. WEB ROUTES
# -------------
@app.route('/')
def index():
    return render_template('index.html')

# 6. MAIN BOOT
# ------------
def start_mqtt():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message
    
    user = os.getenv("MQTT_USERNAME")
    pw = os.getenv("MQTT_PASSWORD")
    if user and pw: client.username_pw_set(user, pw)
    
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
    except Exception as e:
        print(f"🔥 CRITICAL: MQTT Failed: {e}")

if __name__ == '__main__':
    start_mqtt()
    print(f"🚀 TACTICAL DASHBOARD v0.9.8 active at http://localhost:5000")
    socketio.run(app, host='0.0.0.0', port=5000)
