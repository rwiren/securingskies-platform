"""
SecuringSkies Platform - The Officer (Core Logic)
=================================================
Role: Fleet Manager & Intelligence Dispatcher
Status: FINAL (Includes Drivers, Hue, Recorder, Auditor, GeoMath)
"""

import time
import json
import logging
import requests
import os
from rich.console import Console
from rich.panel import Panel

# 1. DRIVERS (Senses)
from securingskies.drivers.autel import AutelDriver
from securingskies.drivers.owntracks import OwnTracksDriver
from securingskies.drivers.dronetag import DronetagDriver 

# 2. OUTPUTS (Actions)
from securingskies.outputs.recorder import BlackBox 
from securingskies.outputs.hue import HueController
from securingskies.outputs.auditor import TelemetryAuditor # <--- NEW

# 3. UTILS (Math)
from securingskies.utils.geo import calculate_distance # <--- NEW

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("core.officer")
console = Console()

class GhostCommander:
    STALE_THRESHOLD_SEC = 90
    DEFAULT_OLLAMA_URL = "http://localhost:11434/api/generate"
    # Hardcoded Home Base (from Legacy)
    HOME_BASE = {"lat": 60.3195, "lon": 24.8310} 
    
    def __init__(self, ai_engine="ollama", model="llama3.1", 
                 record_enabled=False, hue_enabled=False, metrics_enabled=False):
        self.ai_engine = ai_engine
        self.model = model
        self.fleet = {} 
        
        # Init Stack
        self.autel_driver = AutelDriver()
        self.owntracks_driver = OwnTracksDriver()
        self.dronetag_driver = DronetagDriver() 
        self.recorder = BlackBox(enabled=record_enabled) 
        self.hue = HueController(enabled=hue_enabled)
        self.auditor = TelemetryAuditor(enabled=metrics_enabled) # <--- NEW
        
        self.debug_mode = False
        self.track_traffic = False
        self.prompt_shown_once = False
        
        logger.info(f"🦅 GhostCommander Initialized. Intelligence: {ai_engine.upper()}")

    def process_traffic(self, topic, payload):
        self.recorder.log(topic, payload)
        try:
            parsed_packets = None
            if "thing/product" in topic:
                parsed_packets = self.autel_driver.parse(topic, payload)
            elif "owntracks" in topic:
                parsed_packets = self.owntracks_driver.parse(topic, payload)
            elif "dronetag" in topic:
                parsed_packets = self.dronetag_driver.parse(topic, payload)

            if parsed_packets:
                if isinstance(parsed_packets, dict): packets = [parsed_packets]
                else: packets = parsed_packets
                for p in packets: self._update_fleet_state(p)
        except Exception as e:
            logger.error(f"Traffic Error: {e}")

    def _update_fleet_state(self, asset_data):
        tid = asset_data.get('tid', 'UNK')
        if 'AI_EVENT' in asset_data.get('type', ''):
            if self.track_traffic:
                self.hue.set_state("CONTACT")
                for ftid, record in self.fleet.items():
                    if record['data'].get('type') == 'AIR':
                        record['data']['sightings'] = asset_data.get('sightings')
        else:
            self.fleet[tid] = {'data': asset_data, 'last_seen': time.time()}

    def generate_sitrep(self, persona="analyst", show_prompt=False):
        prompts = []
        now = time.time()
        hue_status = "NORMAL"
        
        # Find Pilot (RW) for distance calculations
        pilot_pos = self.HOME_BASE
        if 'RW' in self.fleet:
            pilot_pos = self.fleet['RW']['data']

        for tid, record in self.fleet.items():
            data = record['data']
            age = now - record['last_seen']
            
            if age > self.STALE_THRESHOLD_SEC:
                prompts.append(f"Asset: {tid} | Status: SIGNAL LOST ({int(age)}s ago)")
                hue_status = "LOST"
                continue

            # DISTANCE MATH (Legacy Feature)
            dist_home = int(calculate_distance(data, self.HOME_BASE))
            dist_pilot = int(calculate_distance(data, pilot_pos))
            dist_str = f" | Dist: {dist_home}m (Home), {dist_pilot}m (Pilot)"

            status_str = f"Asset: {tid} | Type: {data.get('type')} | Status: {data.get('mode', 'Active')}"
            batt_str = f" | BATT: {data.get('batt', 'UNK')}%"
            gps_str = f" | GPS: {data.get('nav', 'GPS')} ({data.get('acc', 0)}m)"
            
            vis_str = ""
            if 'sightings' in data:
                vis_str = f" | 👁️ VISUAL: {data['sightings']}"
                hue_status = "CONTACT"

            prompts.append(f"{status_str}{batt_str}{gps_str}{dist_str}{vis_str}")

        self.hue.set_state(hue_status)

        if not prompts: return "Status: Waiting..."

        # Query AI & Audit
        start = time.time()
        response = self._query_ai(prompts, persona, show_prompt)
        
        # Log Performance Metrics
        self.auditor.audit(self.model, start, prompts, response) # <--- NEW
        
        return response

    def _query_ai(self, context_list, persona, show_prompt):
        # (Same AI logic as before)
        system_prompt = f"""
        You are a Tactical Officer ({persona.upper()}).
        Input is raw telemetry. Output a Concise Situation Report.
        
        RULES:
        1. If "RTK-FIX" or "0.1m" -> GPS is GOOD (RTK).
        2. If "SIGNAL LOST" -> Report immediately.
        3. If "Human" detected -> Report CONTACT.
        
        DATA:
        {chr(10).join(context_list)}
        """
        
        if show_prompt and not self.prompt_shown_once:
            console.print(Panel(system_prompt, title="SYSTEM PROMPT (DEBUG)", style="dim"))
            self.prompt_shown_once = True
        
        try:
            if self.ai_engine == "openai":
                from openai import OpenAI
                client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "system", "content": system_prompt}])
                return res.choices[0].message.content
            else:
                payload = {"model": self.model, "prompt": "Analyze.", "system": system_prompt, "stream": False}
                res = requests.post(self.DEFAULT_OLLAMA_URL, json=payload, timeout=10)
                return res.json()['response']
        except Exception as e: return f"Intelligence Offline: {e}"
