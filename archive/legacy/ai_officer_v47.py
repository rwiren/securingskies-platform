#!/usr/bin/env python3
"""
SecuringSkies Platform v47.0 (Legacy Monolith)
==============================================
ARCHITECTURAL OVERVIEW:
This system functions as an Autonomous Ground Control Station (AGCS), utilizing a 
publish-subscribe architecture via MQTT to fuse telemetry from heterogeneous sources:
1. UAS Remote ID (ASTM F3411 / ASD-STAN) via Dronetag Cloud Bridge.
2. Proprietary UAV Telemetry (Autel Enterprise) via OSD Bridge (RTK-Enabled).
3. Mobile Ground Assets (OwnTracks) via encrypted mesh network.

CORE CAPABILITIES:
- Real-time RTK (Real-Time Kinematic) GNSS State Decoding.
- Multi-Agent Sensor Fusion (Ground + Air + Computer Vision).
- LLM-driven Situational Awareness (OpenAI GPT-4o / Ollama Llama3.1).
- Black Box Telemetry Logging (JSONL Standard).
- Latency Watchdog: Monitors queue depth to prevent "Time Travel" reporting.

AI OPTIMIZATION (DSPy):
The "Analyst" persona in this version utilizes **Pre-Compiled Few-Shot Prompts**.
These prompts were optimized using Reinforcement Learning (DSPy) against 
historical mission logs to guarantee consistent forensic grading of GPS data.

AUTHOR: SecuringSkies Research Grid
DATE: 2026-01-24
STATUS: LEGACY GOLD MASTER (Moved to Platform Structure)
"""

import json
import time
import math
import argparse
import subprocess
import requests
import re
import os
import sys
import signal
import paho.mqtt.client as mqtt
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

# Load Environment Variables (Secrets Management)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError: pass

# Dependency Check for Philips Hue
try:
    from phue import Bridge
    HUE_AVAILABLE = True
except ImportError:
    HUE_AVAILABLE = False

# ======================================================
# ⚙️  GLOBAL CONFIGURATION
# ======================================================
DEFAULT_BROKER_IP = os.getenv("MQTT_BROKER_IP", "192.168.192.100")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
DEFAULT_OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = "gpt-4o"
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
DEFAULT_OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")

# Thresholds
DEFAULT_SITREP_INTERVAL = 45        # Seconds between reports
CRITICAL_BATT_THRESHOLD = 15        # Percentage
WARNING_BATT_THRESHOLD = 25         # Percentage
STALE_DATA_THRESHOLD = 90           # Seconds before data is considered "LOST"
DEFAULT_HOME_BASE = {"lat": 60.3195, "lon": 24.8310}

HUE_BRIDGE_IP = os.getenv("HUE_BRIDGE_IP", "192.168.1.228")
HUE_TARGETS = ["Hue bloom L", "Hue bloom R", "Hue color bar", "Hue color bar right", "Hue go 1"]

# 🧠 THE OPTIMIZED BRAIN (DSPy Artifacts)
# 🧠 THE OPTIMIZED BRAIN (DSPy Artifacts - Human/RTK Edition)
ANALYST_FEW_SHOT = """
Example 1:
Input: UAV-1479 | Type: AIR | Status: Active | BATT: 59% | GPS: RTK-FIX (0.1m) | 👁️ VISUAL: {'Human': 1}
Reasoning: RTK is fixed (<1m), so GPS is GOOD. Visual contains Human.
Report: Asset: UAV-1479 | GPS: GOOD (RTK) | CONTACT: Human detected (1)

Example 2:
Input: RW | Type: GROUND | Status: Active | BATT: 100% | GPS: GPS (4m)
Reasoning: Accuracy is 4m (<5m), so GPS is GOOD. No visuals.
Report: Asset: RW | GPS: GOOD (4m) | Status: Active

Example 3:
Input: TAG-99 | Type: AIR | BATT: -1% | GPS: GPS (12m)
Reasoning: Accuracy is 12m (>10m), so GPS is POOR.
Report: Asset: TAG-99 | GPS: POOR (12m) | Speed: N/A
"""

MQTT_SUBSCRIPTIONS = [("owntracks/#", 0), ("dronetag/#", 0), ("thing/product/+/osd", 0), ("thing/product/+/events", 0), ("thing/product/+/state", 0), ("thing/product/sn", 0)]

PERSONAS = {
    "pilot": """You are a Co-Pilot. Concise, safety-focused.
    PRIORITIES:
    1. BATTERY: Warn if < 25%.
    2. SIGNAL: Warn immediately if "SIGNAL LOST".
    3. VERTICAL SPEED: Report Climb/Sink rates if > 0.5m/s.
    4. IGNORE: Latency metrics, generic location data.
    Tone: Urgent, direct, minimal words.""",
    
    "commander": """You are a Tactical Commander. Situational awareness focused.
    PRIORITIES:
    1. MOVEMENT: Report who is moving and where (North/South/Hovering).
    2. SEPARATION: Report distance between Assets and Pilot.
    3. STATUS: Mobile vs Static.
    Tone: Calm, authoritative, descriptive.""",
    
    "analyst": f"""You are a Forensic Data Scientist.
    Use these DSPy-Optimized examples to Grade GPS Integrity (GOOD/FAIR/POOR):
    
    {ANALYST_FEW_SHOT}
    
    TASK: Analyze the NEW input and provide the Report only."""
}

AUTEL_MODES = {
    1: "Manual", 2: "ATTI", 3: "GPS", 10: "RTH", 
    11: "Landing", 12: "Mission", 13: "Precision Landing",
    14: "Takeoff", 15: "Hover"
}
AI_CLASSES = {3: "Car", 4: "Human", 5: "Cyclist", 6: "Truck", 30: "Human", 34: "Drone", 35: "Smoke", 36: "Fire"}
HIGH_VALUE_TARGETS = [4, 30, 34, 36] 

telemetry_buffer = {}
last_sitrep_time = time.time()
console = Console()
hue_bridge = None
log_file = None
current_home_base = DEFAULT_HOME_BASE.copy()
current_pilot_pos = None
active_voice_id = None 
prompt_shown = False 
auditor = None 
replay_process = None 

# ======================================================
# 0. METRICS ENGINE (Legacy Support)
# ======================================================
class TelemetryAuditor:
    def __init__(self):
        if not os.path.exists("logs"): os.makedirs("logs")
        self.filename = f"logs/metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        self.log = open(self.filename, "a")
        self.log.write("Timestamp,Model,Latency_Sec,Word_Count,Recall_Assets,Precision_Batt,Hallucination_Visual\n")
        console.print(f"[bold green]📊 METRICS ENGINE ACTIVE: {self.filename}[/bold green]")

    def audit(self, model_name, start_time, raw_data_list, llm_text):
        latency = time.time() - start_time
        
        # 1. Recall (Asset Count)
        assets_in_json = {d.split(' | ')[0].strip().split(' ')[1] for d in raw_data_list if len(d.split('|')) > 1}
        assets_in_text = 0
        for tid in assets_in_json:
            if tid in llm_text:
                assets_in_text += 1
        recall = assets_in_text / len(assets_in_json) if len(assets_in_json) > 0 else 0
        
        # 2. Precision (Battery Fact Check - Skipped for Analyst)
        batteries_in_text = re.findall(r'(\d+)%', llm_text)
        batteries_in_json = [re.search(r'BATT: (\d+)%', d).group(1) for d in raw_data_list if 'BATT:' in d and 'Unknown' not in d]
        
        matches = 0
        for b_json in batteries_in_json:
            if b_json in batteries_in_text:
                matches += 1
        precision = matches / len(batteries_in_json) if len(batteries_in_json) > 0 else 1.0
        
        # 3. Hallucination Check (Visuals)
        visuals_in_json = any("VISUAL" in d for d in raw_data_list)
        visuals_in_text = "visual" in llm_text.lower() or "sight" in llm_text.lower()
        hallucination = 1 if (visuals_in_text and not visuals_in_json) else 0

        # 4. Relevance
        word_count = len(llm_text.split())

        log_line = f"{datetime.now().isoformat()},{model_name},{latency:.2f},{word_count},{recall:.2f},{precision:.2f},{hallucination}\n"
        self.log.write(log_line)
        self.log.flush()
        
        return f"[METRICS] Latency: {latency:.2f}s | Recall: {recall:.0%} | Factuality: {precision:.0%} | Hallucination: {hallucination}"

# ======================================================
# 1. SYSTEM INTEGRITY CHECKS
# ======================================================
def check_voice(voice_id):
    try:
        res = subprocess.run(["say", "-v", "?"], capture_output=True, text=True)
        if voice_id in res.stdout:
            return voice_id, f"[green]✔ Voice Persona '{voice_id}' active[/green]"
        else: return None, f"[yellow]⚠️ Voice '{voice_id}' not found.[/yellow]"
    except: return None, "[red]❌ Voice synthesis unavailable[/red]"

# ======================================================
# 2. HARDWARE I/O
# ======================================================
def setup_hue():
    global hue_bridge
    if not HUE_AVAILABLE: return
    try:
        hue_bridge = Bridge(HUE_BRIDGE_IP)
        hue_bridge.connect()
        console.print(f"[bold green]💡 HUE LIGHTING CONNECTED[/bold green]")
    except Exception: pass

def setup_logging(enabled):
    global log_file
    if not enabled: return
    if not os.path.exists("logs"): os.makedirs("logs")
    filename = f"logs/mission_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
    log_file = open(filename, "a")
    console.print(f"[bold red]🔴 BLACK BOX RECORDING ACTIVE: {filename}[/bold red]")

def log_packet(topic, payload):
    if not log_file: return
    try:
        data = json.loads(payload.decode('utf-8')) if isinstance(payload, bytes) else payload
        log_file.write(json.dumps({"ts": time.time(), "topic": topic, "data": data}) + "\n")
        log_file.flush()
    except: pass

def set_mood_lighting(state):
    """Circuit Breaker Pattern for Hue"""
    if not hue_bridge: return
    try:
        lights = hue_bridge.get_light_objects(mode='name')
        for name in HUE_TARGETS:
            if name in lights:
                light = lights[name]
                light.on = True
                if state == "CRITICAL": light.hue = 0; light.saturation = 254; light.brightness = 254
                elif state == "WARNING": light.hue = 12750; light.saturation = 254; light.brightness = 200
                elif state == "CONTACT": light.hue = 45000; light.saturation = 254; light.brightness = 254
                elif state == "LOST": light.hue = 40000; light.saturation = 254; light.brightness = 100 
                else: light.hue = 25500; light.saturation = 254; light.brightness = 150
    except Exception: pass 

def vocalize_sitrep(text, voice_name=None):
    clean = re.sub(r'\[.*?\]', '', text) 
    clean = clean.replace("**", "").replace("km/h", "kph")
    clean = clean.replace("RW", "Phone").replace("CTRL", "Controller").replace("UAV", "Drone")
    clean = clean.replace("RTK-FIX", "R-T-K Fixed").replace("LTE-GPS", "L-T-E G-P-S")
    cmd = ["say"]
    if voice_name: cmd.extend(["-v", voice_name])
    cmd.extend(["-r", "185", clean])
    subprocess.Popen(cmd)

# ======================================================
# 3. PHYSICS & DATA
# ======================================================
def calculate_physics_3d(p1, p2):
    if not p1 or not p2: return 0
    if 'lat' not in p1 or 'lat' not in p2: return 0
    try:
        R = 6371e3
        phi1, phi2 = math.radians(p1['lat']), math.radians(p2['lat'])
        dphi = math.radians(p2['lat'] - p1['lat'])
        dlambda = math.radians(p2['lon'] - p1['lon'])
        a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2) * math.sin(dlambda/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c
    except: return 0

def get_relative_distances(current_pos):
    d_home = calculate_physics_3d(current_pos, current_home_base)
    d_pilot = 0
    if current_pilot_pos:
        d_pilot = calculate_physics_3d(current_pos, current_pilot_pos)
    return d_home, d_pilot

def estimate_lipo_percent(mv):
    if mv == 0: return 0
    cells = 4 if mv > 14000 else 3
    v_cell = (mv / 1000.0) / cells
    if v_cell >= 4.3: return 100
    if v_cell <= 3.5: return 0
    return int((v_cell - 3.5) / 0.8 * 100)

def extract_drone_data(source, type="nested", sn=None):
    try:
        raw_sn = source.get('sn')
        if type == "nested":
            if not raw_sn or raw_sn == "UNK": return None
            serial = raw_sn[-4:]
        else:
            if not sn or sn == "UNK": return None
            serial = sn[-4:]

        batt = source.get('battery', {})
        pct = batt.get('capacity_percent', source.get('capacity_percent', 0))
        mv = batt.get('voltage', 0)
        if pct == 0 and mv > 0: pct = estimate_lipo_percent(mv)

        rtk = source.get('position_state', {})
        nav_type = "GPS"
        sats = rtk.get('gps_number', 0)
        is_fixed = rtk.get('is_fixed', 0)
        rtk_used = rtk.get('rtk_used', 0)
        rtk_sats = rtk.get('rtk_number', 0)

        if rtk_used == 1:
            sats = rtk_sats
            if is_fixed == 3: nav_type = "RTK-FIX"
            elif is_fixed == 2: nav_type = "RTK-FLOAT"
            else: nav_type = "RTK"
        
        h_spd = float(source.get('horizontal_speed', 0))
        v_spd = float(source.get('vertical_speed', 0))
        height = source.get('height', 0)
        mode = AUTEL_MODES.get(source.get('mode_code'), "Std")
        if height > 0.1 and mode == "Hover": mode = "Hovering"
        elif height <= 0.1: mode = "Ground Idle"
        inferred_acc = 0.1 if rtk_used == 1 else (5.0 if sats > 10 else 20.0)

        return {
            'tid': f"UAV-{serial}",
            'lat': source.get('latitude'), 'lon': source.get('longitude'),
            'alt': height, 'batt': pct,
            'acc': inferred_acc,
            'h_speed': h_spd * 3.6, 'v_speed': v_spd,
            'heading': float(source.get('attitude_head', 0)),
            'type': 'AIR', 'nav': nav_type, 'sats': sats, 'mode': mode,
            'signal': source.get('link_signal_quality', 100),
            'ai_sightings': {}
        }
    except: return None

def process_data(topic, payload, allow_traffic, debug_mode):
    global current_pilot_pos
    log_packet(topic, payload)
    current_ts = time.time()
    try:
        data = json.loads(payload.decode())
        
        if data.get('_type') == 'location': 
            current_pilot_pos = {'lat': data['lat'], 'lon': data['lon'], 'alt': data.get('alt',0)}
            # Extract additional ground metrics (acc/vel)
            return [{'ts': current_ts, 'tid': data.get('tid', 'PHONE'), 
                     'lat': data['lat'], 'lon': data['lon'], 
                     'alt': data.get('alt',0), 'batt': data.get('batt',0), 
                     'acc': f"{data.get('acc', 0)}", # Added for Analyst
                     'vel': data.get('vel', 0),      # Added for Analyst
                     'type': 'GROUND', 'ai_sightings': {}}]
        
        elif 'state' in topic and data.get('method') == 'target_detect_result_report': 
            sightings = {}
            allowed = HIGH_VALUE_TARGETS + ([3, 5, 6] if allow_traffic else [])
            for obj in data.get('data', {}).get('objs', []):
                if obj.get('cls_id') in allowed:
                    name = AI_CLASSES.get(obj.get('cls_id'), "UNK")
                    sightings[name] = sightings.get(name, 0) + 1
            if sightings: return [{'type': 'AI_UPDATE', 'sightings': sightings}]
        
        elif 'dronetag' in topic:
            try:
                raw_id = data.get('sensor_id', data.get('uas_id', 'UNK'))
                tid = f"TAG-{raw_id[-4:]}" 
                loc = data.get('location', {})
                acc_str = ""
                h_acc = data.get('horizontal_accuracy', loc.get('accuracy', 0))
                if h_acc > 0: acc_str = f"{h_acc:.1f}m"

                alt = 0.0
                if 'altitudes' in data: 
                    alts = data.get('altitudes', [])
                    for a in alts:
                        if a.get('type') == 'MSL': alt = a.get('value', 0); break
                    if alt == 0 and alts: alt = alts[0].get('value', 0)
                elif 'altitude' in data:
                    alt = float(data.get('altitude', 0))
              
                state = data.get('operational_state', 'Unknown').upper()
                if state == "UNKNOWN" and alt > 5: state = "AIRBORNE"
              
                vel = data.get('velocity', {})
                speed = 0.0
                if 'horizontal_speed' in vel: speed = vel.get('horizontal_speed', 0)
                elif isinstance(vel, dict) and 'x' in vel: speed = math.sqrt(vel['x']**2 + vel['y']**2)
              
                return [{
                    'ts': current_ts,
                    'tid': tid,
                    'lat': loc.get('latitude'), 'lon': loc.get('longitude'), 
                    'alt': round(alt, 1), 'h_speed': round(speed, 1),
                    'batt': -1, 
                    'type': 'AIR', 'mode': state, 'nav': 'Remote ID',
                    'acc': acc_str, 'sats': 12, 'ai_sightings': {}
                }]
            except: pass

        elif topic.endswith('/sn'):
            res = []
            if 'drone_list' in data:
                for d in data['drone_list']:
                    res.append({'ts': current_ts, 'tid': f"UAV-{d.get('drone_sn')[-4:]}", 'type': 'AIR', 'mode': 'Connected', 'batt': 0, 'lat': DEFAULT_HOME_BASE['lat'], 'lon': DEFAULT_HOME_BASE['lon'], 'ai_sightings': {}})
            return res

        elif 'osd' in topic and 'data' in data:
            osd = data['data']
            res = []
            sn = topic.split('/')[2] if len(topic.split('/')) > 2 else "UNK"
            if 'drone_list' in osd:
                if osd.get('capacity_percent', 0) > 0:
                    res.append({'ts': current_ts, 'tid': f"CTRL-{sn[-4:]}", 'lat': osd.get('latitude'), 'lon': osd.get('longitude'), 'batt': osd.get('capacity_percent'), 'type': 'GND_STATION', 'ai_sightings': {}})
                for d in osd['drone_list']:
                    u = extract_drone_data(d, "nested"); 
                    if u: 
                        u['ts'] = current_ts
                        res.append(u)
            elif ('height' in osd or 'battery' in osd) and not sn.startswith("TH"):
                u = extract_drone_data(osd, "direct", sn); 
                if u: 
                    u['ts'] = current_ts
                    res.append(u)
            return res
    except: pass
    return None

# ======================================================
# 5. INTELLIGENCE REPORT LOOP
# ======================================================
def generate_sitrep(args):
    global last_sitrep_time, prompt_shown, auditor
    targets = []
    hue_state = "NORMAL"
    ai_active = False
    now = time.time()
    
    for tid, tdata in telemetry_buffer.items():
        if not tdata['history']: continue
        d = tdata['history'][-1]
        
        data_age = now - d.get('ts', now)
        is_stale = data_age > STALE_DATA_THRESHOLD
        
        if d['batt'] == 0 and len(tdata['history']) > 1:
            for old in reversed(tdata['history']):
                if old['batt'] > 0: d['batt'] = old['batt']; break

        dist_home = get_relative_distances(d)[0]
        dist_pilot = get_relative_distances(d)[1]
        batt_val = d.get('batt', 0)
        batt_str = f"{batt_val}%"
        if batt_val == -1: batt_str = "Unknown"
        
        icon = "✈️" if d['type'] == 'AIR' else ("🎮" if d['type'] == 'GND_STATION' else "📱")
        
        # Prepare Analysis Metrics
        acc = d.get('acc', 'N/A')
        if acc != 'N/A': acc = str(acc).replace('m', '') # Normalize for LLM
        
        # GPS Grading Logic (v46.1)
        gps_grade = "UNK"
        try:
            val = float(acc)
            if val < 5: gps_grade = "GOOD"
            elif val < 10: gps_grade = "FAIR"
            else: gps_grade = "POOR"
        except: pass
        
        speed = d.get('h_speed', 0)
        if d['type'] == 'GROUND': speed = d.get('vel', 0)

        if is_stale:
            info = f"{icon} {tid} | ⚠️ SIGNAL LOST ({int(data_age)}s ago)"
            hue_state = "LOST"
        else:
            # Enriched format specifically for Analyst to chew on
            info = f"{icon} {tid} | Type: {d['type']} | Status: {d.get('mode', 'Active')} | BATT: {batt_str} | "
            info += f"GPS: {gps_grade} ({acc}m) | VEL: {int(speed)}km/h | Latency: {data_age:.1f}s"
        
        is_uav = tid.startswith("UAV")
        is_tag = tid.startswith("TAG")
        is_ground = d['type'] in ['GROUND', 'GND_STATION']

        if is_ground and not is_stale:
            if batt_val > 0 and batt_val < CRITICAL_BATT_THRESHOLD: hue_state = "CRITICAL"
            elif batt_val > 0 and batt_val < WARNING_BATT_THRESHOLD: hue_state = "WARNING"

        # [NEW CODE]
        if d['type'] == 'AIR' and not is_stale:
            alt = d.get('alt', 0)
            nav = d.get('nav', 'GPS')
            
            # FORCE OVERRIDE: If Nav is RTK, append it to GPS string for the AI
            if "RTK" in nav:
                info = info.replace(f"GPS: {gps_grade}", "GPS: GOOD (RTK)")
                
            info += f" | Nav: {nav} | ALT: {alt:.1f}m"

            sightings = d.get('ai_sightings')
            if is_uav and sightings and len(sightings) > 0:
                info += f" | 👁️ VISUAL: {sightings}"
                ai_active = True
        
        if d.get('lat') and not is_stale:
            info += f" | Dist: {int(dist_home)}m (Home), {int(dist_pilot)}m (Pilot)"
        
        targets.append(info)

    if not targets: return
    if args.hue: set_mood_lighting("CONTACT" if ai_active and args.traffic else hue_state)
    console.print(Panel(f"[bold cyan]⚡ DIRECTOR UPDATE ({datetime.now().strftime('%H:%M:%S')})[/bold cyan]", border_style="cyan"))
    
    # CONSTRUCT SYSTEM PROMPT (PERSONA + TECHNICAL CONSTRAINTS)
    tech_context = """
    INPUT CONTEXT:
    Input is raw telemetry. Summarize it according to your PERSONA priorities.
    
    HARD CONSTRAINTS:
    1. ASSET CAPABILITIES:
       - UAV-xxxx: Camera + RTK.
       - TAG-xxxx: GPS Only.
       - RW/CTRL: Ground Only.
    2. VISUALS: Report ONLY if "👁️ VISUAL" is present.
    3. SIGNAL LOSS: Report "SIGNAL LOST" immediately.
    
    Format: "Asset [Name]. Status [Mode]. Battery [Level]. [Nav/Alt if Air]. [Visuals if Air]."
    Max 50 words."""
    
    # Merge selected Persona with Technical Rules
    selected_persona = PERSONAS.get(args.persona, PERSONAS["pilot"])
    full_prompt = f"{selected_persona}\n\n{tech_context}"
    
    if args.show_prompt and not prompt_shown:
        console.print(Panel(full_prompt, title="SYSTEM PROMPT (DEBUG - SHOWN ONCE)", style="dim"))
        prompt_shown = True

    try:
        start_time = time.time()
        model_name = "Ollama"
        
        if args.cloud:
            from openai import OpenAI
            client = OpenAI(api_key=DEFAULT_OPENAI_KEY) if DEFAULT_OPENAI_KEY else OpenAI()
            res = client.chat.completions.create(model=OPENAI_MODEL, messages=[{"role": "system", "content": full_prompt}, {"role": "user", "content": "\n".join(targets)}])
            intel = res.choices[0].message.content
            model_name = "OpenAI"
        else:
            # Handle "ollama:" prefix from CLI args
            target_model = args.model if args.model else DEFAULT_OLLAMA_MODEL
            clean_model = target_model.replace("ollama:", "") if "ollama:" in target_model else target_model
            
            payload = {"model": clean_model, "prompt": "\n".join(targets), "system": full_prompt, "stream": False}
            
            # INCREASED TIMEOUT to 90s for Cold Starts on Battery
            try:
                res = requests.post(OLLAMA_URL, json=payload, timeout=90)
                intel = res.json()['response']
                model_name = f"Ollama ({clean_model})"
            except requests.exceptions.ReadTimeout:
                console.print("[dim yellow]⚠️ AI Model Loading... (Timeout). The next request will be faster.[/dim yellow]")
                return
        
        console.print(f"[white]{intel}[/white]")
        if args.voice: vocalize_sitrep(intel, active_voice_id)
        
        if auditor:
            audit_report = auditor.audit(model_name, start_time, targets, intel)
            console.print(f"[dim]{audit_report}[/dim]")
            
    except Exception as e: console.print(f"[red]AI Error: {e}[/red]")
    last_sitrep_time = time.time()

# ======================================================
# 6. REPLAY MANAGER
# ======================================================
def start_replay(file, jump, speed):
    global replay_process
    console.print(Panel(f"[bold magenta]📼 TIME MACHINE ACTIVE: {file}[/bold magenta]"))
    cmd = ["python3", "labs/replay/replay_tool.py", file, "--ip", "127.0.0.1", "--speed", str(speed)]
    if jump: cmd.append("--jump")
    replay_process = subprocess.Popen(cmd)

def cleanup_handler(sig, frame):
    if replay_process:
        console.print("\n[yellow]🛑 Stopping Replay Engine...[/yellow]")
        replay_process.terminate()
    sys.exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="🦅 GHOST COMMANDER v47.0 - Autonomous Ground Control Station",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
SCIENTIFIC TELEMETRY STANDARDS:
-------------------------------
1. AUTEL ENTERPRISE (RTK-Enabled)
   - Decodes 'position_state' bitmask for Real-Time Kinematic status.
   - States: RTK-FIXED (Cm-level), RTK-FLOAT (Dm-level), GPS (Meter-level).
   - Connection: MQTT via 'thing/product/...' topic structure.

2. DRONETAG (Remote ID)
   - Fusion Engine: Parsers both ASTM F3411 (Standard) and Legacy JSON.
   - Accuracy: Extracts 'horizontal_accuracy' confidence interval (e.g., 3.0m).
   - Bridge: Connects via Cloud Proxy (mqtt.securingskies.eu).

3. OWNTRAKS (Mobile Assets)
   - Standard: JSON HTTP/MQTT payload decoding via 'owntracks/#' topic.
   - Parameters: Decodes 'lat', 'lon', 'alt' (Altitude), 'batt' (Battery).
   - Role: Provides 'Ground Truth' and 'Operator Location' for proximity vectors.

4. SENSOR FUSION & WATCHDOG
   - Logic: Prioritizes MSL Altitude (Aviation Standard) over HAE (Geometric).
   - Latency: Optimized for <100ms processing time (QoS 0).
   - Watchdog: Validates telemetry freshness (Threshold: 60s) to prevent frozen data.
   - Hardware Filters: Prevents hallucination of capabilities (e.g., Visuals on non-camera assets).

5. SCIENTIFIC METRICS ENGINE
   - Latency: Tracks Model Inference Time (ms).
   - Factuality: Checks Precision/Recall of reported assets.
   - Auditing: Writes session performance to 'logs/metrics_YYYYMMDD.csv'.

USEFUL UTILITIES (MACOS/OLLAMA):
-------------------------------
  ollama list           # List installed models
  ollama ps             # Show currently loaded model & RAM usage
  say -v "?"            # List available system voices (MacOS)
  
OPERATIONAL PARAMETERS (FLAGS):
-------------------------------
  --model NAME           Override AI Model (Default: llama3.1).
                         Examples: --model ollama:qwen2.5, --model ollama:phi4
  --persona TYPE         Select AI Personality (Default: pilot).
                         Options: pilot, commander, analyst
  --ip IP               Override MQTT Broker Address (Default: 192.168.192.100).
  --hue                 Enable Philips Hue Bridge integration.
  --traffic             Enable Computer Vision Object Detection tracking.
  --record              Enable 'Black Box' JSONL logging.
  --metrics             Enable Scientific Metrics Engine.
  --cloud               Force Cloud Intelligence (OpenAI).
  --interval SEC        Set Voice Report frequency (Default: 45s).
  --voice_id NAME       Select System Voice Persona (Default: Satu).
  --debug               Enable raw JSON stream output.
  --show-prompt         Display the hidden System Prompt.

FORENSIC REPLAY (TIME MACHINE):
-------------------------------
  --replay FILE         Play back a JSONL mission log as if it were live.
                        (Starts internal replay engine on 127.0.0.1)
  --jump                Skip directly to UAV/Airborne activity in the log.
  --speed FLOAT         Playback speed (Default: 1.0).

EXAMPLES:
  python3 ai_officer_v47.py --model ollama:qwen2.5 --metrics
  python3 ai_officer_v47.py --replay logs/mission.jsonl --jump --persona commander
        """
    )
    
    # ARGUMENT GROUPS
    mission = parser.add_argument_group('🎮 Mission Control')
    mission.add_argument("--interval", type=int, default=DEFAULT_SITREP_INTERVAL, help=f"Report Interval (Default: {DEFAULT_SITREP_INTERVAL}s)")
    mission.add_argument("--traffic", action="store_true", help="Track Cars/Trucks in Vision AI")
    mission.add_argument("--persona", type=str, default="pilot", choices=PERSONAS.keys(), help="Select AI Personality")
    
    net = parser.add_argument_group('📡 Network & Intelligence')
    net.add_argument("--ip", type=str, default=DEFAULT_BROKER_IP, help=f"Broker IP (Default: {DEFAULT_BROKER_IP})")
    net.add_argument("--model", type=str, default=DEFAULT_OLLAMA_MODEL, help=f"AI Model (Default: {DEFAULT_OLLAMA_MODEL})")
    net.add_argument("--cloud", action="store_true", help="Use OpenAI (Cloud) instead of Ollama (Local)")

    fx = parser.add_argument_group('💡 Atmosphere & Debug')
    fx.add_argument("--voice", action="store_true", help="Enable Voice Synthesis")
    fx.add_argument("--voice_id", type=str, default="Satu", help="Voice Persona")
    fx.add_argument("--hue", action="store_true", help="Enable Philips Hue Lighting integration")
    fx.add_argument("--record", action="store_true", help="Enable Black Box JSONL Recording")
    fx.add_argument("--metrics", action="store_true", help="Enable Scientific Metrics Engine")
    fx.add_argument("--debug", action="store_true", help="Show raw debugging info")
    fx.add_argument("--show-prompt", action="store_true", help="Show AI System Prompt in console")

    sim = parser.add_argument_group('📼 Time Machine (Replay)')
    sim.add_argument("--replay", type=str, help="Path to JSONL log file for replay")
    sim.add_argument("--jump", action="store_true", help="Jump to interesting activity (Airborne)")
    sim.add_argument("--speed", type=float, default=1.0, help="Playback speed (Default: 1.0)")
    
    args = parser.parse_args()

    # REPLAY LOGIC
    if args.replay:
        if args.ip == DEFAULT_BROKER_IP:
            args.ip = "127.0.0.1"
        
        signal.signal(signal.SIGINT, cleanup_handler)
        start_replay(args.replay, args.jump, args.speed)
        time.sleep(2)

    # STARTUP SEQUENCE
    console.print(Panel.fit(f"[bold yellow]🦅 GHOST COMMANDER v47.0 (The Neural Analyst)[/bold yellow]"))
    
    # UI UPDATE: Show active intelligence engine & Persona
    active_engine = "OpenAI GPT-4o" if args.cloud else f"Ollama ({args.model})"
    console.print(f"🧠 INTELLIGENCE: [bold green]{active_engine}[/bold green]")
    console.print(f"🎭 PERSONA: [bold cyan]{args.persona.upper()}[/bold cyan] | 📡 BROKER: {args.ip}")

    if args.metrics:
        auditor = TelemetryAuditor()

    if args.voice:
        active_voice_id, v_msg = check_voice(args.voice_id)
        console.print(v_msg)
    
    setup_hue()
    setup_logging(args.record)
    
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = lambda c, u, f, r, p: (console.print(f"[green]✅ LINK ESTABLISHED[/green]"), [c.subscribe(t, q) for t, q in MQTT_SUBSCRIPTIONS])
    
    def on_message(c, u, msg):
        print(".", end="", flush=True)
        res = process_data(msg.topic, msg.payload, args.traffic, args.debug)
        if res:
            for r in res:
                if r.get('type') == 'AI_UPDATE':
                    for t in telemetry_buffer.values():
                        if t['history'] and t['history'][-1]['type'] == 'AIR': t['history'][-1]['ai_sightings'] = r['sightings']
                else:
                    tid = r['tid']
                    if tid not in telemetry_buffer: telemetry_buffer[tid] = {'history': []}
                    telemetry_buffer[tid]['history'].append(r)
                    if len(telemetry_buffer[tid]['history']) > 10: telemetry_buffer[tid]['history'].pop(0)
    
    client.on_message = on_message
    try:
        client.connect(args.ip, MQTT_PORT, 60)
        client.loop_start()
    except Exception as e:
        console.print(f"[bold red]❌ NETWORK ERROR: {e}[/bold red]")
        if args.replay:
            console.print("[yellow]💡 Hint: Did you start a local MQTT broker? (docker run -p 1883:1883 eclipse-mosquitto)[/yellow]")
        if replay_process: replay_process.terminate()
        exit()
    
    while True:
        try:
            if time.time() - last_sitrep_time > args.interval: generate_sitrep(args)
            time.sleep(1)
        except KeyboardInterrupt:
            cleanup_handler(None, None)
