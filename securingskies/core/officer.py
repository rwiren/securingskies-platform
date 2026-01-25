"""
SecuringSkies Platform - Ghost Commander (The Brain)
====================================================
Version: 0.9.9
Date: 2026-01-25
Author: Ghost Commander

Role:
  Core Intelligence Module.
  - Ingests normalized JSON telemetry from the MQTT Bus.
  - Maintains state of all tracked assets.
  - Consults the AI Model (Ollama/OpenAI) for tactical analysis.
  - Generates "SITREP" (Situation Report).

Status: PRODUCTION (Synced with Outputs)
"""

import json
import logging
import time
from typing import Dict, List, Optional
from litellm import completion

# Internal Imports
try:
    from securingskies.utils.geo import calculate_distance_3d
    # Importing output drivers exactly as they appear in your project
    from securingskies.outputs.recorder import BlackBox      # <--- Verified Class Name
    from securingskies.outputs.hue import HueController      # <--- Verified Class Name
    from securingskies.outputs.auditor import TelemetryAuditor # <--- Verified Class Name
except ImportError as e:
    # Fail loudly if core components are missing
    raise ImportError(f"Missing Core Component: {e}")

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("core.officer")

class GhostCommander:
    def __init__(self, model_name: str = "llama3.1", use_cloud: bool = False, 
                 record_enabled: bool = False, hue_enabled: bool = False, metrics_enabled: bool = False):
        """
        Initialize the AI Tactical Officer.
        """
        self.model = model_name
        self.provider = "openai" if use_cloud else "ollama"
        self.telemetry_buffer = {}  # The "Memory" of the track table
        self.track_traffic = False
        self.debug_mode = False
        
        # Initialize Outputs (Using your existing drivers)
        self.recorder = BlackBox(enabled=record_enabled) if record_enabled else None
        self.hue = HueController(enabled=hue_enabled) if hue_enabled else None
        self.auditor = TelemetryAuditor(enabled=metrics_enabled) if metrics_enabled else None
        
        # Confirm subsystem activation
        if self.recorder: logger.info("🔴 RECORDER: ACTIVE")
        if self.auditor: logger.info("📊 METRICS: ACTIVE")
            
        logger.info(f"🦅 GhostCommander Initialized. Intelligence: {self.provider.upper()} ({self.model})")

    def process_traffic(self, topic: str, payload: bytes):
        """
        Ingest MQTT messages, parse JSON, and update the Tactical Map.
        This is the method main.py calls.
        """
        try:
            # 1. Parse Data safely
            if isinstance(payload, bytes):
                payload_str = payload.decode("utf-8")
                data = json.loads(payload_str)
            else:
                data = payload 

            # Handle nested data structures common in telemetry
            if "data" in data: data = data["data"]
            
            # 2. Extract Key Fields
            tid = data.get("tid", "UNK")
            
            # 3. Update Memory
            self.telemetry_buffer[tid] = data
            
            # 4. Trigger Hardware Outputs
            if self.hue:
                # Map topics to Hue States (using set_state("WARNING") etc.)
                if "px4" in str(topic) or "dronetag" in str(topic): 
                    self.hue.set_state("WARNING") # Orange
                elif "owntracks" in str(topic): 
                    self.hue.set_state("CONTACT") # Blue
            
            # 5. Record to Disk
            if self.recorder: 
                self.recorder.log(topic, data) # <--- Calls 'log' (Your API)

            if self.debug_mode: 
                print(f"DEBUG: Updated {tid}")

        except Exception as e:
            if self.debug_mode: logger.error(f"Traffic Parse Error: {e}")

    def generate_sitrep(self, persona: str = "PILOT", show_prompt: bool = False) -> str:
        """
        Generates the text report by sending current memory to the AI.
        Called by main.py loop.
        """
        start_time = time.time()
        
        # 1. Construct the Tactical Context
        system_prompt = self._get_system_prompt(persona)
        user_prompt = self._format_telemetry_buffer()
        
        if show_prompt:
            logger.info("\n--- SYSTEM PROMPT ---\n" + system_prompt)
            logger.info("\n--- USER PROMPT ---\n" + user_prompt)

        # 2. Execute Inference
        try:
            response = completion(
                model=f"{self.provider}/{self.model}", 
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=150,  # Keep it concise
                temperature=0.3  # Low creativity, high factual accuracy
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # 3. Scientific Metrics
            if self.auditor:
                # Pass a list of raw prompt strings for recall calculation
                raw_lines = user_prompt.split('\n')
                audit_log = self.auditor.audit(self.model, start_time, raw_lines, result_text)
                if audit_log: print(f"\n{audit_log}") 
            
            return result_text

        except Exception as e:
            logger.error(f"❌ AI INFERENCE FAILED: {e}")
            return "SITREP: SYSTEM ERROR. AI UNAVAILABLE."

    def _get_system_prompt(self, persona: str) -> str:
        """Selects the engagement rules based on the chosen Persona."""
        
        base_rules = (
            "GPS QUALITY STANDARDS:\n"
            "- Accuracy < 1.0m: Report as 'EXCELLENT (RTK)'.\n"
            "- Accuracy 1m - 5m: Report as 'ACCEPTABLE'.\n"
            "- Accuracy > 5m: Report as 'POOR / COARSE'. WARN THE PILOT.\n"
            "- If 'SIGNAL LOST': Report immediately.\n\n"
            "VISUAL RULES:\n"
            "- STRICT: Do NOT mention 'Contact' or 'Humans' unless the input explicitly says 'VISUAL'.\n"
            "- If no visual data exists, assume the sensor is BLIND. State: 'Sensors Blind'.\n"
        )

        if persona == "PILOT":
            return (
                "You are a Tactical Officer (PILOT).\n"
                "Input is raw telemetry. Output a Concise Situation Report.\n"
                "RULES:\n" + base_rules
            )
        elif persona == "COMMANDER":
            return (
                "You are the Incident Commander.\n"
                "Input is fleet telemetry. Output Strategic Orders and Risk Assessment.\n"
                "RULES:\n" + base_rules
            )
        else:
            return f"You are a Data Analyst. Summarize the JSON input.\n{base_rules}"

    def _format_telemetry_buffer(self) -> str:
        """Converts the entire memory state into a string for the AI."""
        if not self.telemetry_buffer:
            return "DATA: No Active Telemetry."
            
        lines = []
        for tid, data in self.telemetry_buffer.items():
            acc = data.get('acc', 10)
            
            # Calculate distance to home (mockup fixed point for now)
            # Ensure calculate_distance_3d is available via import
            dist_home = int(calculate_distance_3d(data.get('lat'), data.get('lon'), data.get('alt'), 60.3195, 24.8310, 115))
            
            visuals = f"VISUAL: {data['visual']}" if "visual" in data else "No Visual Data"
            
            lines.append(
                f"Asset: {tid} | Type: {data.get('type', 'GND')} | "
                f"BATT: {data.get('batt', 0)}% | GPS Acc: {acc}m | "
                f"Dist: {dist_home}m (Home) | {visuals}"
            )
        return "\n".join(lines)
