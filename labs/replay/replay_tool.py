import json
import time
import sys
import argparse
import paho.mqtt.client as mqtt

def get_start_time(filename, jump_to_action):
    """Finds the timestamp where the ACTUAL UAV starts."""
    if not jump_to_action: return None
    
    print(f"🔍 Scanning {filename} for AUTEL UAV activity...")
    with open(filename, 'r') as f:
        for line in f:
            try:
                record = json.loads(line)
                topic = record.get('topic', '')
                
                # FIX: Only trigger on Autel data (thing/product), ignore Dronetag "airborne" noise
                if topic.startswith('thing/product'):
                    print(f"✅ Autel UAV found at timestamp: {record['ts']}")
                    return record['ts'] - 5 # Start 5s before the drone wakes up
            except: continue
            
    print("⚠️ No Autel UAV found. Checking for general Airborne status...")
    # Fallback: Check for generic airborne if Autel never shows up
    with open(filename, 'r') as f:
        for line in f:
            try:
                record = json.loads(line)
                if record.get('data', {}).get('operational_state') == 'airborne':
                     return record['ts'] - 5
            except: continue

    return None

def replay(args):
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    try:
        client.connect(args.ip, 1883, 60)
    except:
        print(f"❌ Could not connect to Broker at {args.ip}")
        return

    start_skip_ts = get_start_time(args.file, args.jump)
    
    print(f"📼 REPLAYING: {args.file} (Speed: {args.speed}x)")
    
    first_record_ts = None
    wall_clock_start = time.time()
    
    with open(args.file, 'r') as f:
        for line in f:
            try:
                record = json.loads(line)
                ts = record.get('ts')
                
                # JUMP LOGIC
                if start_skip_ts and ts < start_skip_ts:
                    continue 

                if first_record_ts is None:
                    first_record_ts = ts
                    wall_clock_start = time.time()

                # TIMING LOGIC
                time_passed_log = ts - first_record_ts
                time_passed_real = (time.time() - wall_clock_start) * args.speed
                
                wait = (time_passed_log - time_passed_real) / args.speed
                if wait > 0: time.sleep(wait)

                # PUBLISH
                topic = record.get('topic')
                payload = record.get('data')
                if isinstance(payload, dict): payload = json.dumps(payload)
                
                client.publish(topic, payload)
                print(f"📡 Replayed: {topic}")

            except KeyboardInterrupt:
                print("\n🛑 Replay Stopped.")
                break
            except Exception: continue

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MQTT Time Machine")
    parser.add_argument("file", help="JSONL Log file")
    parser.add_argument("--ip", default="127.0.0.1", help="Broker IP")
    parser.add_argument("--speed", type=float, default=1.0, help="Replay Speed")
    parser.add_argument("--jump", action="store_true", help="Jump to UAV/Airborne start")
    
    args = parser.parse_args()
    replay(args)
