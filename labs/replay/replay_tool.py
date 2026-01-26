"""
SecuringSkies Platform - Forensic Replay Engine (v0.9.9)
========================================================
MODULE: labs.replay.replay_tool
ROLE: The "Time Machine"
DESCRIPTION: 
  Re-injects historical JSONL telemetry logs into the live MQTT bus 
  with precise time-dilation control. Used for:
  1. Regression Testing (Did the new code fix the old bug?)
  2. Post-Mission Analysis (Forensics)
  3. Simulator Training (Feeding real flight data to the AI)

ALGORITHM:
  Linear Time Scaling with Drift Compensation.
  T_wait = (T_log_elapsed - T_wall_elapsed) / Speed_Factor

AUTHOR: SecuringSkies Research Grid
LICENSE: MIT
"""

import json
import time
import sys
import argparse
import logging
from typing import Optional
import paho.mqtt.client as mqtt

# Configure Logging (Standardized Output)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("replay_tool")

def get_start_time(filename: str, jump_to_action: bool) -> Optional[float]:
    """
    Scans the log file to find the 'Zero Hour' (Start of Mission).
    
    Heuristic Logic:
    1. If --jump is active, look for the first Autel UAV packet ('thing/product').
    2. If not found, look for any 'airborne' status.
    3. Buffer: Returns timestamp - 5.0s to provide context before takeoff.
    """
    if not jump_to_action: 
        return None
    
    logger.info(f"🔍 Scanning {filename} for Mission Start (Autel/Airborne)...")
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    record = json.loads(line)
                    topic = record.get('topic', '')
                    
                    # PRIORITY 1: Autel Smart Controller Telemetry
                    # We ignore Dronetag here because it often logs 'ground' state for hours.
                    if topic.startswith('thing/product'):
                        ts = record['ts']
                        logger.info(f"✅ FOUND: Autel UAV Active at T={ts:.2f}")
                        return ts - 5.0 # Pre-roll buffer
                        
                except (json.JSONDecodeError, KeyError):
                    continue
                    
        logger.warning("⚠️ No Autel UAV signature found. Starting from beginning.")
    except FileNotFoundError:
        logger.error(f"❌ File not found: {filename}")
        sys.exit(1)

    return None

def replay(args):
    """
    Main Replay Loop.
    Uses a 'Drift-Correcting' timing loop to ensure long replays stay in sync.
    """
    # 1. Setup MQTT Connection
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    try:
        client.connect(args.ip, 1883, 60)
        logger.info(f"📡 Connected to Simulation Broker: {args.ip}")
    except Exception as e:
        logger.error(f"❌ MQTT Connection Failed: {e}")
        return

    # 2. Determine Start Point
    start_skip_ts = get_start_time(args.file, args.jump)
    
    logger.info(f"📼 REPLAY STARTED: {args.file}")
    logger.info(f"⏩ SPEED FACTOR: {args.speed}x")
    
    first_record_ts = None
    wall_clock_start = time.time()
    packet_count = 0
    
    try:
        with open(args.file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    record = json.loads(line)
                    ts = record.get('ts')
                    
                    # ---------------------------------------------------------
                    # LOGIC: Timeline Skipping
                    # ---------------------------------------------------------
                    if start_skip_ts and ts < start_skip_ts:
                        continue 

                    # Initialize the "Time Anchor" on the first valid packet
                    if first_record_ts is None:
                        first_record_ts = ts
                        wall_clock_start = time.time()
                        logger.info("⏱️ TIMELINE SYNCED. Playing...")

                    # ---------------------------------------------------------
                    # CONTROL THEORY: Latency Compensation
                    # ---------------------------------------------------------
                    # We calculate how much time HAS passed in the log vs real world.
                    # If the log is 'ahead', we sleep. If 'behind', we burst (catch up).
                    
                    time_passed_log = ts - first_record_ts
                    time_passed_real = (time.time() - wall_clock_start) * args.speed
                    
                    wait = (time_passed_log - time_passed_real) / args.speed
                    
                    if wait > 0:
                        time.sleep(wait)

                    # ---------------------------------------------------------
                    # I/O: Publish to Live Bus
                    # ---------------------------------------------------------
                    topic = record.get('topic')
                    payload = record.get('data')
                    
                    # Ensure strict JSON serialization
                    if isinstance(payload, dict): 
                        payload = json.dumps(payload)
                    
                    client.publish(topic, payload)
                    packet_count += 1
                    
                    # Visual Heartbeat (every 50 packets)
                    if packet_count % 50 == 0:
                        sys.stdout.write(f"\r📡 Replayed Frames: {packet_count} | Log Time: +{time_passed_log:.1f}s")
                        sys.stdout.flush()

                except (json.JSONDecodeError, ValueError):
                    continue

    except KeyboardInterrupt:
        logger.info("\n🛑 User Interrupted Replay.")
    except FileNotFoundError:
        logger.error(f"\n❌ Log file not found: {args.file}")
    finally:
        client.disconnect()
        logger.info(f"\n🏁 Session Ended. Total Packets: {packet_count}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="🦅 SecuringSkies Replay Tool (Time Machine)",
        epilog="Example: python3 replay_tool.py mission.jsonl --speed 2.0 --jump"
    )
    parser.add_argument("file", help="Path to JSONL log file")
    parser.add_argument("--ip", default="127.0.0.1", help="Target MQTT Broker IP")
    parser.add_argument("--speed", type=float, default=1.0, help="Playback Speed Multiplier (e.g. 2.0)")
    parser.add_argument("--jump", action="store_true", help="Auto-skip to UAV Takeoff")
    
    args = parser.parse_args()
    replay(args)
