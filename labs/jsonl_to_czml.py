import json
import datetime
import os
from datetime import timezone

# --- CONFIGURATION ---
# Dynamically find the project root (assuming script is in /labs)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Input: The log file in the /logs folder
INPUT_FILE = os.path.join(BASE_DIR, "logs", "mission_20260203_104902.jsonl")

# Output: Save the CZML in /labs next to this script
OUTPUT_FILE = os.path.join(BASE_DIR, "labs", "mission_replay.czml")

def unix_to_iso(ts):
    """Convert Unix timestamp to ISO 8601 string for Cesium."""
    return datetime.datetime.fromtimestamp(ts, tz=timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

def parse_mission_file(filepath):
    entities = {}
    
    if not os.path.exists(filepath):
        print(f"❌ ERROR: File not found at {filepath}")
        return {}

    print(f"📂 Reading log: {filepath}")
    
    with open(filepath, 'r') as f:
        for line in f:
            try:
                entry = json.loads(line)
                topic = entry.get('topic', '')
                ts = entry.get('ts')
                payload = entry.get('data', {})
                
                tid, lat, lon, alt = None, None, None, 0
                color = [255, 255, 0, 255] 

                # A. OwnTracks (RW / Blue)
                if "owntracks" in topic and payload.get("_type") == "location":
                    tid = payload.get("tid", "Unknown")
                    lat, lon = payload.get("lat"), payload.get("lon")
                    alt = payload.get("alt", 0)
                    color = [0, 150, 255, 255] 

                # B. Dronetag (Red)
                elif "dronetag" in topic:
                    tid = payload.get("id", topic.split('/')[-1])
                    lat = payload.get("lat", payload.get("latitude"))
                    lon = payload.get("lon", payload.get("longitude"))
                    alt = payload.get("alt", payload.get("altitude", 0))
                    color = [255, 0, 0, 255]

                # C. Autel (Orange)
                elif "thing/product" in topic:
                    parts = topic.split('/')
                    if len(parts) > 2: tid = parts[2]
                    lat, lon = payload.get("latitude"), payload.get("longitude")
                    alt = payload.get("height", payload.get("ned_altitude", 0))
                    if lat == 0.0 or lon == 0.0: continue
                    color = [255, 165, 0, 255]

                if tid and lat is not None and lon is not None:
                    if tid not in entities:
                        entities[tid] = {"id": tid, "color": color, "positions": []}
                    
                    entities[tid]["positions"].extend([
                        unix_to_iso(ts), float(lon), float(lat), float(alt)
                    ])

            except Exception:
                continue
                
    return entities

def generate_czml(entities):
    all_times = []
    for data in entities.values():
        all_times.extend(data["positions"][0::4])
        
    if not all_times:
        print("⚠️ No valid GPS data found.")
        return []

    all_times.sort()
    start_iso, end_iso = all_times[0], all_times[-1]

    czml = [{
        "id": "document",
        "name": "Mission Replay",
        "version": "1.0",
        "clock": {
            "interval": f"{buffer_time(start_iso, -60)}/{buffer_time(end_iso, 60)}",
            "currentTime": start_iso,
            "multiplier": 5,
            "range": "CLAMPED",
            "step": "SYSTEM_CLOCK_MULTIPLIER"
        }
    }]

    for tid, data in entities.items():
        if not data["positions"]: continue
        
        packet = {
            "id": tid,
            "name": tid,
            "availability": f"{data['positions'][0]}/{data['positions'][-4]}",
            "billboard": {
                "image": "https://cesium.com/public/images/2015/02/02/Dot.png",
                "scale": 1.5,
                "color": {"rgba": data["color"]}
            },
            "path": {
                "material": {"solidColor": {"color": {"rgba": data["color"]}}},
                "width": 2,
                "leadTime": 0,
                "trailTime": 60 
            },
            "position": {
                "epoch": data["positions"][0],
                "cartographicDegrees": data["positions"]
            }
        }
        czml.append(packet)

    return czml

def buffer_time(iso_str, seconds):
    dt = datetime.datetime.fromisoformat(iso_str.replace('Z', '+00:00'))
    dt += datetime.timedelta(seconds=seconds)
    return dt.strftime('%Y-%m-%dT%H:%M:%SZ')

# --- EXECUTE ---
mission_data = parse_mission_file(INPUT_FILE)
if mission_data:
    print(f"✅ Found Assets: {list(mission_data.keys())}")
    czml_output = generate_czml(mission_data)
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(czml_output, f, indent=2)
    print(f"💾 Saved CZML to: {OUTPUT_FILE}")
