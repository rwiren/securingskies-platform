"""
SecuringSkies Platform - Ghost Commander (The Brain)
====================================================
Version: 0.9.9f (Instrument Flight Rules - IFR)
Status: PRODUCTION - FULL TELEMETRY
"""

import json
import logging
import time
from litellm import completion

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
                 record_enabled: bool = False, hue_enabled: bool = False, metrics_enabled: bool = False):
        self.model = model_name
        self.provider = "openai" if use_cloud else "ollama"
        self.telemetry_buffer = {}
        self._last_shown_persona = None
        self.debug_mode = False
        
        self.recorder = BlackBox(enabled=record_enabled) if record_enabled else None
        self.hue = HueController(enabled=hue_enabled) if hue_enabled else None
        self.auditor = TelemetryAuditor(enabled=metrics_enabled) if metrics_enabled else None
        
        if self.recorder: logger.info("🔴 RECORDER: ACTIVE")
        if self.auditor: logger.info("📊 METRICS: ACTIVE")
        logger.info(f"🦅 GhostCommander Initialized. Intelligence: {self.provider.upper()} ({self.model})")

    def process_traffic(self, topic: str, payload: bytes):
        try:
            if isinstance(payload, bytes):
                data = json.loads(payload.decode("utf-8"))
            else:
                data = payload 

            if "data" in data and isinstance(data["data"], dict): 
                data = data["data"]
            
            # --- NORMALIZATION ---
            
            # Case A: Autel Controller
            if "drone_list" in data:
                for drone in data["drone_list"]:
                    tid = f"AUTEL_UAV"
                    
                    new_lat = drone.get("latitude")
                    new_lon = drone.get("longitude")
                    current_record = self.telemetry_buffer.get(tid, {})
                    final_lat = new_lat if (new_lat and abs(new_lat) > 1) else current_record.get("lat", 0.0)
                    final_lon = new_lon if (new_lon and abs(new_lon) > 1) else current_record.get("lon", 0.0)

                    if tid not in self.telemetry_buffer: self.telemetry_buffer[tid] = {}
                    self.telemetry_buffer[tid].update({
                        "tid": tid,
                        "type": "UAV",
                        "lat": final_lat,
                        "lon": final_lon,
                        "alt": drone.get("height", 0),
                        "batt": drone.get("battery", {}).get("capacity_percent", 0),
                        # NEW: Speed Metrics
                        "speed": drone.get("horizontal_speed", 0),
                        "v_speed": drone.get("vertical_speed", 0),
                        "acc": 0.1 if drone.get("position_state", {}).get("is_fixed") == 2 else 5.0
                    })
                    
                    if self.telemetry_buffer[tid].get("acc") == 0.1:
                         if "CONTACT" not in self.telemetry_buffer[tid].get("visual", ""):
                             self.telemetry_buffer[tid]["visual"] = "RTK LOCKED"

            # Case B: Autel Vision
            elif "obj_cnt" in data and "objs" in data:
                tid = "AUTEL_UAV"
                if tid in self.telemetry_buffer:
                    count = data.get("obj_cnt", 0)
                    if count > 0:
                        self.telemetry_buffer[tid]["visual"] = f"⚠️ CONTACT: {count} OBJECTS"
                        if self.hue: self.hue.set_state("CRITICAL")

            # Case C: OwnTracks
            elif "tid" in data:
                tid = data.get("tid")
            # MAP 'vel' (km/h) to 'speed' (m/s) for the AI
                data["speed"] = data.get("vel", 0) / 3.6
                self.telemetry_buffer[tid] = data
                if self.hue and "owntracks" in str(topic):
                    self.hue.set_state("CONTACT")

            if self.recorder: self.recorder.log(topic, data) 

        except Exception as e:
            if self.debug_mode: logger.error(f"Traffic Parse Error: {e}")

    def generate_sitrep(self, persona: str = "PILOT", show_prompt: bool = False) -> str:
        start_time = time.time()
        system_prompt = self._get_system_prompt(persona)
        user_prompt = self._format_telemetry_buffer()
        
        if show_prompt:
            if self._last_shown_persona != persona:
                logger.info("\n--- SYSTEM PROMPT ---\n" + system_prompt)
                self._last_shown_persona = persona
            logger.info("\n--- USER PROMPT ---\n" + user_prompt)

        try:
            response = completion(
                model=f"{self.provider}/{self.model}", 
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                max_tokens=150, temperature=0.3
            )
            result_text = response.choices[0].message.content.strip()
            if self.auditor: self.auditor.audit(self.model, start_time, user_prompt.split('\n'), result_text)
            return result_text
        except Exception as e:
            return "SITREP: SYSTEM ERROR. AI UNAVAILABLE."

    def _get_system_prompt(self, persona: str) -> str:
        base_rules = (
            "REPORTING RULES:\n"
            "- If Vertical Speed > 0.5: Report 'CLIMBING'. If < -0.5: Report 'DESCENDING'.\n"
            "- If Speed > 1.0: Report 'MOVING'.\n"
            "- Calculate estimated time to home if moving.\n"
            "- Battery < 20%: WARN CRITICAL.\n"
        )
        if persona == "COMMANDER": 
            return f"You are the Flight Commander. Analyze dynamics (Speed/Alt/Batt). Provide Strategic Outlook.\n{base_rules}"
        return f"Tactical Pilot. Concise Metrics.\n{base_rules}"

    def _format_telemetry_buffer(self) -> str:
        if not self.telemetry_buffer: return "DATA: No Active Telemetry."
        lines = []
        for tid, data in self.telemetry_buffer.items():
            acc = data.get('acc', 10)
            lat = data.get('lat')
            lon = data.get('lon')
            dist_home = 0
            if lat and lon and isinstance(lat, (int, float)):
                try: dist_home = int(calculate_distance_3d(lat, lon, data.get('alt', 0), 60.3195, 24.8310, 115))
                except: pass
            
            # THE UPGRADE: Full Instrument Panel
            lines.append(
                f"Asset: {tid} | BATT: {data.get('batt')}% | "
                f"ALT: {data.get('alt', 0):.1f}m | "
                f"H-SPD: {data.get('speed', 0):.1f}m/s | V-SPD: {data.get('v_speed', 0):.1f}m/s | "
                f"Dist: {dist_home}m | {data.get('visual', 'No Visual')}"
            )
        return "\n".join(lines)
