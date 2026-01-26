"""
SecuringSkies Platform - Ghost Commander (The Brain)
====================================================
Version: 1.0.5 (Autel Controller Latency)
Status: PRODUCTION - FULL TELEMETRY
Description: Central Logic Unit handling Data Ingestion, 
             Dynamic Persona Loading (RAG), and Auditing.
             
CHANGELOG v1.0.5:
- Added Latency KPI for Autel Smart Controller (via 'sn' topic).
- Maintained Dronetag Latency logic.
- Preserved 'Constitutional Guardrails'.
"""

import json
import logging
import time
import os
from typing import Optional, Dict
from datetime import datetime
from litellm import completion

# Import Modular Components
try:
    from securingskies.utils.geo import calculate_distance_3d
    from securingskies.outputs.recorder import BlackBox
    from securingskies.outputs.hue import HueController
    from securingskies.outputs.auditor import TelemetryAuditor
except ImportError as e:
    raise ImportError(f"Missing Core Component: {e}")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("core.officer")

class GhostCommander:
    def __init__(self, model_name: str = "llama3.1", use_cloud: bool = False, 
                 record_enabled: bool = False, hue_enabled: bool = False, metrics_enabled: bool = False,
                 persona: str = "pilot"):
        
        self.model = model_name
        self.provider = "openai" if use_cloud else "ollama"
        self.telemetry_buffer: Dict = {}
        self._last_shown_persona = None
        self.debug_mode = False
        
        # Subsystems
        self.recorder = BlackBox(enabled=record_enabled) if record_enabled else None
        self.hue = HueController(enabled=hue_enabled) if hue_enabled else None
        self.auditor = TelemetryAuditor() if metrics_enabled else None
        
        # ACADEMIC: Dynamic Knowledge Loading (Few-Shot Injection)
        self.current_persona_name = persona
        self.system_prompt = self._load_optimized_brain(persona)
        
        if self.recorder: logger.info("🔴 RECORDER: ACTIVE")
        if self.auditor: logger.info("📊 METRICS: ACTIVE")
        logger.info(f"🦅 GhostCommander Initialized. Brain: {persona.upper()} | Model: {self.model}")

    def _load_optimized_brain(self, persona: str) -> str:
        """Loads the 'Textbook' created by the Optimizer."""
        base_prompt = ""
        defaults = {
            "pilot": "You are a Co-Pilot. Concise. Focus on Battery, Signal, and Speed. Max 20 words.",
            "commander": "You are a Tactical Commander. Analyze trends. Focus on Arrival Estimates and Separation.",
            "analyst": "You are a Data Scientist. Explain GPS Accuracy (RTK) and Battery Latency."
        }
        json_path = f"config/optimized_{persona}.json"
        brain_loaded = False
        
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r') as f:
                    data = json.load(f)
                demos = data.get('predict', {}).get('demos', [])
                if demos:
                    logger.info(f"🧠 LOADED OPTIMIZED BRAIN: {len(demos)} Trained Examples.")
                    base_prompt = f"You are the {persona.upper()}. Follow these trained examples:\n\n"
                    for demo in demos:
                        raw = demo.get('raw_telemetry', '')
                        rep = demo.get('report', '')
                        if raw and rep:
                            base_prompt += f"DATA: {raw}\nREPORT: {rep}\n---\n"
                    base_prompt += "\nNow generate the REPORT for the current DATA."
                    brain_loaded = True
            except Exception as e:
                logger.warning(f"⚠️ Failed to load optimized brain: {e}")
        
        if not brain_loaded:
            logger.info(f"ℹ️ Using Default Static Brain for {persona}")
            base_prompt = defaults.get(persona, defaults['pilot'])

        # CONSTITUTIONAL GUARDRAILS
        guardrails = """
\n--- STRICT TERMINOLOGY RULES ---
1. Check the 'type' field in the DATA.
2. If type is 'Ground Station (GCS)', refer to it as 'OPERATOR' or 'GCS'. It is NOT a drone.
3. If type is 'UAV' (Autel or Dronetag), refer to it as 'DRONE' or 'UAV'.
4. Do not hallucinate RTK status. If 'pos_type' is missing, do not mention RTK.
5. If only GCS is present, state "No UAVs active".
"""
        return base_prompt + guardrails

    def process_traffic(self, topic: str, payload: bytes):
        """Standardized Ingestion Pipeline"""
        server_ts = time.time()
        
        try:
            if isinstance(payload, bytes):
                data = json.loads(payload.decode("utf-8"))
            else:
                data = payload 

            if "data" in data and isinstance(data["data"], dict): 
                # Preserve timestamp if it exists in the wrapper for 'sn' topic
                wrapper_ts = data["data"].get("timestamp")
                data = data["data"]
                if wrapper_ts: data["timestamp"] = wrapper_ts
            
            # --- NORMALIZATION LOGIC ---

            # CASE A: Autel Heartbeat / Device List (LATENCY SOURCE)
            if "drone_list" in data or topic.endswith("/sn"):
                # This packet usually comes from the Controller itself
                tid = "AUTEL_CONTROLLER" # Separate entity for stats
                latency_str = "N/A"
                
                if "timestamp" in data:
                    try:
                        # Autel sends ms, Server uses sec
                        device_ts = float(data["timestamp"]) / 1000.0
                        latency = server_ts - device_ts
                        latency_str = f"{latency:.2f}s"
                    except: pass

                # We don't want this to override the UAV data, just store it as a GCS metric
                # Or we can attach it to the UAV buffer if we want
                
                # Let's attach it to the main AUTEL_UAV record if it exists, or create a placeholder
                uav_tid = "AUTEL_UAV"
                if uav_tid not in self.telemetry_buffer: self.telemetry_buffer[uav_tid] = {}
                self.telemetry_buffer[uav_tid]["c2_latency"] = latency_str

                # Also process the drone list for position if present
                if "drone_list" in data:
                    for drone in data["drone_list"]:
                        new_lat = drone.get("latitude")
                        new_lon = drone.get("longitude")
                        current_record = self.telemetry_buffer.get(uav_tid, {})
                        final_lat = new_lat if (new_lat and abs(new_lat) > 1) else current_record.get("lat", 0.0)
                        final_lon = new_lon if (new_lon and abs(new_lon) > 1) else current_record.get("lon", 0.0)
                        
                        self.telemetry_buffer[uav_tid].update({
                            "tid": uav_tid,
                            "type": "UAV (Autel)",
                            "lat": final_lat,
                            "lon": final_lon,
                            "alt": drone.get("height", 0),
                            "batt": drone.get("battery", {}).get("capacity_percent", 0),
                            "speed": drone.get("horizontal_speed", 0),
                            "pos_type": drone.get("pos_type", "0"), 
                            "acc": 0.1 if drone.get("position_state", {}).get("is_fixed") == 2 else 5.0
                        })

            # CASE B: Autel OSD (Direct Raw Telemetry)
            elif "pos_type" in data or "capacity_percent" in data:
                tid = "AUTEL_UAV"
                if tid not in self.telemetry_buffer: self.telemetry_buffer[tid] = {}
                self.telemetry_buffer[tid]["type"] = "UAV (Autel)"
                if "pos_type" in data: self.telemetry_buffer[tid]["pos_type"] = str(data["pos_type"])
                if "capacity_percent" in data: self.telemetry_buffer[tid]["batt"] = data["capacity_percent"]
                if "height" in data: self.telemetry_buffer[tid]["alt"] = data["height"]

            # CASE C: Autel Vision
            elif "obj_cnt" in data and "objs" in data:
                tid = "AUTEL_UAV"
                if tid in self.telemetry_buffer:
                    count = data.get("obj_cnt", 0)
                    if count > 0:
                        sightings = [obj.get('cls_id') for obj in data.get('objs', [])]
                        self.telemetry_buffer[tid]["ai_sightings"] = f"⚠️ CONTACT: {sightings}"
                        if self.hue: self.hue.set_state("CRITICAL")

            # CASE D: OwnTracks (Mobile Phone)
            elif "tid" in data:
                tid = data.get("tid")
                data["speed"] = data.get("vel", 0) / 3.6
                data["type"] = "Ground Station (GCS)"
                if "tst" in data:
                    try:
                        latency = server_ts - float(data["tst"])
                        data["link_latency"] = f"{latency:.2f}s"
                    except: pass
                self.telemetry_buffer[tid] = data

            # CASE E: DRONETAG (Remote ID)
            elif "dronetag" in topic or "sensor_id" in data:
                tid = data.get("sensor_id", "DRONETAG_UNKNOWN")
                loc = data.get("location", {})
                alt = 0
                for a in data.get("altitudes", []):
                    if a.get("type") == "MSL":
                        alt = a.get("value", 0)
                        break
                
                latency_str = "N/A"
                if "timestamp" in data:
                    try:
                        dt_str = data["timestamp"].replace("Z", "+00:00")
                        dt_obj = datetime.fromisoformat(dt_str)
                        device_ts = dt_obj.timestamp()
                        latency = server_ts - device_ts
                        latency_str = f"{latency:.2f}s"
                    except: pass

                self.telemetry_buffer[tid] = {
                    "tid": tid,
                    "type": "UAV (Dronetag)",
                    "lat": loc.get("latitude"),
                    "lon": loc.get("longitude"),
                    "acc": loc.get("accuracy", 10),
                    "alt": alt,
                    "speed": data.get("velocity", {}).get("horizontal_speed", 0),
                    "state": data.get("operational_state", "unknown"),
                    "batt": "N/A",
                    "link_latency": latency_str
                }

            # Black Box Logging
            if self.recorder: self.recorder.log(topic, data) 

        except Exception as e:
            if self.debug_mode: logger.error(f"Traffic Parse Error: {e}")

    def generate_sitrep(self, show_prompt: bool = False) -> str:
        """The Main Intelligence Loop"""
        start_time = time.time()
        user_prompt = self._format_telemetry_buffer()
        
        if show_prompt:
            logger.info("\n--- SYSTEM BRAIN ---\n" + self.system_prompt[:200] + "...")
            logger.info("\n--- LIVE DATA ---\n" + user_prompt)

        try:
            response = completion(
                model=f"{self.provider}/{self.model}", 
                messages=[
                    {"role": "system", "content": self.system_prompt}, 
                    {"role": "user", "content": f"DATA: {user_prompt}\nREPORT:"}
                ],
                max_tokens=150, temperature=0.3
            )
            result_text = response.choices[0].message.content.strip()
            
            if self.auditor: 
                metrics_str = self.auditor.audit(self.model, start_time, user_prompt.split('\n'), result_text)
                print(f"\033[90m{metrics_str}\033[0m")
                
            return result_text
            
        except Exception as e:
            return f"SITREP: SYSTEM ERROR. AI UNAVAILABLE. ({e})"

    def _format_telemetry_buffer(self) -> str:
        """Flattens the dict into the format the Optimizer expects."""
        if not self.telemetry_buffer: return "DATA: No Active Telemetry."
        lines = []
        for tid, data in self.telemetry_buffer.items():
            lines.append(str(data))
        return "\n".join(lines)
