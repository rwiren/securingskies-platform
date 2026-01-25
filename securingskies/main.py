#!/usr/bin/env python3
"""
SecuringSkies Platform v0.9.9 (Release Candidate)
=================================================
Role: Bootloader & Command Interface.
Status: PRODUCTION (Full Documentation)
"""

import argparse
import sys
import time
import signal
import logging
import subprocess
import os
from rich.console import Console
from rich.panel import Panel
import paho.mqtt.client as mqtt

# ------------------------------------------------------
# 1. ENVIRONMENT & HYGIENE (The Fixes)
# ------------------------------------------------------
# Silence the Chatty AI Libraries
os.environ["LITELLM_LOG"] = "ERROR"
logging.getLogger("litellm").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.ERROR)

# Ensure Project Root is in Path (Crucial for imports)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load .env if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import Core (Fail Loudly if missing)
try:
    from securingskies.core.officer import GhostCommander
except ImportError as e:
    print(f"❌ CRITICAL IMPORT ERROR: {e}")
    sys.exit(1)

# UI Setup
console = Console()
commander = None

# ------------------------------------------------------
# 2. NETWORK HANDLERS
# ------------------------------------------------------
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        console.print("[green]✅ LINK ESTABLISHED (MQTT)[/green]")
        # Subscribe to all relevant telemetry topics
        client.subscribe([
            ("owntracks/#", 0), 
            ("dronetag/#", 0), 
            ("pixhawk/#", 0),
            ("thing/product/+/osd", 0),
            ("thing/product/+/events", 0),
            ("thing/product/+/state", 0),
            ("thing/product/sn", 0)
        ])
    else:
        console.print(f"[bold red]❌ CONNECTION FAILED (RC: {rc})[/bold red]")
        if rc == 5: console.print("[yellow]💡 Hint: Check your Username/Password[/yellow]")

def on_message(client, userdata, msg):
    """Passes raw MQTT traffic to the Officer for processing."""
    if commander:
        commander.process_traffic(msg.topic, msg.payload)
        print(".", end="", flush=True) 

# ------------------------------------------------------
# 3. MAIN EXECUTION
# ------------------------------------------------------
def main():
    global commander
    
    # Clean Exit Handler
    signal.signal(signal.SIGINT, lambda s, f: sys.exit(0))
    
    # CLI Argument Definition (Restoring Full Verbosity)
    parser = argparse.ArgumentParser(
        description="🦅 GHOST COMMANDER v0.9.9 - Modular AGCS Platform",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
SCIENTIFIC TELEMETRY STANDARDS:
-------------------------------
1. AUTEL ENTERPRISE (RTK-Enabled)
   - Decodes 'position_state' bitmask for RTK status.
   - States: RTK-FIXED (Cm-level), RTK-FLOAT (Dm-level).

2. DRONETAG (Remote ID) & MAVLINK (Pixhawk)
   - Supports DroneTag (ASTM F3411) and ArduPilot/PX4 (MAVLink v2).

3. OWNTRAKS (Mobile Assets)
   - Role: Provides 'Ground Truth' and 'Operator Location'.

AI MODEL SELECTION (Ollama/Local):
----------------------------------
- llama3.1 (Default): Balanced General Purpose.
- gemma2   (Tactical): High logic reasoning, good for SITREP.
- phi3.5   (Speed): Ultra-fast (<1s latency), best for drone swarms.

VOICE SYNTHESIS (MacOS):
------------------------
- "Satu"   : Finnish accent (The "Rally English" Co-Pilot).
- "Daniel" : Standard British Command.

CLOUD OPERATIONS (securingskies.eu):
------------------------------------
  python3 main.py --ip mqtt.securingskies.eu --tls --username "admin" --password "secret"
        """
    )
    
    # Mission Control
    mission = parser.add_argument_group('🎮 Mission Control')
    mission.add_argument("--interval", type=int, default=45, help="Report Interval (Default: 45s)")
    mission.add_argument("--traffic", action="store_true", help="Track Cars/Trucks in Vision AI")
    mission.add_argument("--persona", type=str, default="pilot", choices=["pilot", "commander", "analyst"], help="Select AI Personality")
    
    # Network & Intelligence
    net = parser.add_argument_group('📡 Network & Intelligence')
    net.add_argument("--ip", type=str, default="192.168.192.100", help="Broker IP/Domain (Default: 192.168.192.100)")
    net.add_argument("--port", type=int, default=1883, help="Broker Port (Default: 1883, or 8883 for TLS)")
    net.add_argument("--tls", action="store_true", help="Enable SSL/TLS Encryption (Required for Cloud)")
    net.add_argument("--username", type=str, help="MQTT Username")
    net.add_argument("--password", type=str, help="MQTT Password")
    net.add_argument("--model", type=str, default="llama3.1", help="AI Model (Default: llama3.1)")
    net.add_argument("--cloud", action="store_true", help="Use OpenAI (Cloud) instead of Ollama (Local)")

    # Atmosphere & Debug
    fx = parser.add_argument_group('💡 Atmosphere & Debug')
    fx.add_argument("--voice", action="store_true", help="Enable Voice Synthesis")
    fx.add_argument("--voice_id", type=str, default="Satu", help="Voice Persona (e.g. Satu for Rally English)")
    fx.add_argument("--hue", action="store_true", help="Enable Philips Hue Lighting integration")
    fx.add_argument("--record", action="store_true", help="Enable Black Box JSONL Recording")
    fx.add_argument("--metrics", action="store_true", help="Enable Scientific Metrics Engine")
    fx.add_argument("--debug", action="store_true", help="Show raw debugging info")
    fx.add_argument("--show-prompt", action="store_true", help="Show AI System Prompt in console")

    # Time Machine
    sim = parser.add_argument_group('📼 Time Machine (Replay)')
    sim.add_argument("--replay", type=str, help="Path to JSONL log file for replay")
    sim.add_argument("--jump", action="store_true", help="Jump to interesting activity (Airborne)")
    sim.add_argument("--speed", type=float, default=1.0, help="Playback speed (Default: 1.0)")
    
    args = parser.parse_args()

    # Replay Shim
    if args.replay:
        target_ip = args.ip if args.ip != "192.168.192.100" else "127.0.0.1"
        args.ip = target_ip 
        try:
            cmd = [sys.executable, "labs/replay/replay_tool.py", args.replay, "--ip", target_ip, "--speed", str(args.speed)]
            if args.jump: cmd.append("--jump")
            subprocess.Popen(cmd)
            console.print(Panel(f"[magenta]📼 REPLAY ACTIVE: {args.replay}[/magenta]"))
        except FileNotFoundError:
            console.print("[red]❌ Replay Tool not found in labs/replay/replay_tool.py[/red]")

    console.print(Panel.fit(f"[bold yellow]🦅 GHOST COMMANDER v0.9.9 (Modular Platform)[/bold yellow]"))
    
    ai_engine = "openai" if args.cloud else "ollama"
    model_name = "gpt-4o" if args.cloud else args.model.replace("ollama:", "")
    
    console.print(f"🧠 BRAIN: [bold green]{model_name.upper()} ({ai_engine})[/bold green]")
    console.print(f"🎭 PERSONA: [bold cyan]{args.persona.upper()}[/bold cyan] | 📡 BROKER: {args.ip}")

    # Initialize Core (Explicitly passing all flags)
    commander = GhostCommander(
        model_name=model_name,
        use_cloud=args.cloud,
        record_enabled=args.record,
        hue_enabled=args.hue,
        metrics_enabled=args.metrics
    )
    commander.debug_mode = args.debug
    commander.track_traffic = args.traffic

    # Connect to MQTT
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    if args.username and args.password:
        client.username_pw_set(args.username, args.password)
        console.print("[dim]🔑 Authentication Enabled[/dim]")

    if args.tls or (args.port == 8883):
        client.tls_set()
        console.print("[dim]🔒 TLS Encryption Enabled[/dim]")
        if args.port == 1883: args.port = 8883

    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        client.connect(args.ip, args.port, 60)
        client.loop_start()
    except Exception as e:
        console.print(f"[bold red]❌ NETWORK ERROR: {e}[/bold red]")
        sys.exit(1)

    # Main Mission Loop
    last_report = time.time()
    
    while True:
        try:
            time.sleep(1)
            if time.time() - last_report > args.interval:
                print("") 
                console.print(Panel(f"[bold cyan]⚡ DIRECTOR UPDATE ({time.strftime('%H:%M:%S')})[/bold cyan]", border_style="cyan"))
                
                # Execute AI Analysis (Upper case persona for consistency)
                report = commander.generate_sitrep(args.persona.upper(), show_prompt=args.show_prompt)
                
                console.print(f"[white]{report}[/white]")
                
                # Trigger Voice
                if args.voice:
                    try: 
                        subprocess.Popen(["say", "-v", args.voice_id, "-r", "185", report])
                    except FileNotFoundError: pass
                
                last_report = time.time()
                
        except KeyboardInterrupt:
            console.print("\n\n[bold yellow]🛑 MISSION END. DISENGAGING...[/bold yellow]")
            sys.exit(0)

if __name__ == "__main__":
    main()
