#!/usr/bin/env python3
"""
SecuringSkies Platform v2.7 - Command & Control Interface
=========================================================
ARCHITECTURAL OVERVIEW:
This is the bootloader for the Autonomous Ground Control Station (AGCS).
It initializes the Modular Architecture:
1. Drivers (securingskies.drivers.*) - Hardware abstraction.
2. Officer (securingskies.core.officer) - Central intelligence.
3. Network (Paho MQTT) - Data transport layer.

STATUS: PRODUCTION (Full Feature Parity)
"""

import argparse
import sys
import time
import signal
import logging
import subprocess
from rich.console import Console
from rich.panel import Panel
import paho.mqtt.client as mqtt

# Load Environment Variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import Core Logic
try:
    from securingskies.core.officer import GhostCommander
except ImportError:
    sys.path.append('.')
    from securingskies.core.officer import GhostCommander

# UI Setup
console = Console()
logging.basicConfig(level=logging.WARNING)

# Global State
commander = None
replay_process = None

# ======================================================
# 1. CLI CONFIGURATION (Legacy Help Text)
# ======================================================
def get_cli_args():
    parser = argparse.ArgumentParser(
        description="🦅 GHOST COMMANDER v2.7 - Modular AGCS Platform",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
SCIENTIFIC TELEMETRY STANDARDS:
-------------------------------
1. AUTEL ENTERPRISE (RTK-Enabled)
   - Decodes 'position_state' bitmask for RTK status.
   - States: RTK-FIXED (Cm-level), RTK-FLOAT (Dm-level).

2. DRONETAG (Remote ID)
   - Fusion Engine: Parsers both ASTM F3411 (Standard) and Legacy JSON.

3. OWNTRAKS (Mobile Assets)
   - Role: Provides 'Ground Truth' and 'Operator Location'.

4. SENSOR FUSION & WATCHDOG
   - Latency: Optimized for <100ms processing time (QoS 0).
   - Watchdog: Validates telemetry freshness (Threshold: 90s).

USEFUL UTILITIES:
  ollama list           # List installed models
  say -v "?"            # List available system voices (MacOS)
        """
    )
    
    # Mission Control
    mission = parser.add_argument_group('🎮 Mission Control')
    mission.add_argument("--interval", type=int, default=45, help="Report Interval (Default: 45s)")
    mission.add_argument("--traffic", action="store_true", help="Track Cars/Trucks in Vision AI")
    mission.add_argument("--persona", type=str, default="pilot", choices=["pilot", "commander", "analyst"], help="Select AI Personality")
    
    # Network
    net = parser.add_argument_group('📡 Network & Intelligence')
    net.add_argument("--ip", type=str, default="192.168.192.100", help="Broker IP (Default: 192.168.192.100)")
    net.add_argument("--port", type=int, default=1883, help="Broker Port")
    net.add_argument("--model", type=str, default="llama3.1", help="AI Model (Default: llama3.1)")
    net.add_argument("--cloud", action="store_true", help="Use OpenAI (Cloud) instead of Ollama (Local)")

    # FX & Debug
    fx = parser.add_argument_group('💡 Atmosphere & Debug')
    fx.add_argument("--voice", action="store_true", help="Enable Voice Synthesis")
    fx.add_argument("--voice_id", type=str, default="Satu", help="Voice Persona")
    fx.add_argument("--hue", action="store_true", help="Enable Philips Hue Lighting integration")
    fx.add_argument("--record", action="store_true", help="Enable Black Box JSONL Recording")
    fx.add_argument("--metrics", action="store_true", help="Enable Scientific Metrics Engine")
    fx.add_argument("--debug", action="store_true", help="Show raw debugging info")
    fx.add_argument("--show-prompt", action="store_true", help="Show AI System Prompt in console")

    # Replay
    sim = parser.add_argument_group('📼 Time Machine (Replay)')
    sim.add_argument("--replay", type=str, help="Path to JSONL log file for replay")
    sim.add_argument("--jump", action="store_true", help="Jump to interesting activity (Airborne)")
    sim.add_argument("--speed", type=float, default=1.0, help="Playback speed (Default: 1.0)")

    return parser.parse_args()

# ======================================================
# 2. NETWORK HANDLERS
# ======================================================
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        console.print("[green]✅ LINK ESTABLISHED (MQTT)[/green]")
        topics = [
            ("owntracks/#", 0), ("dronetag/#", 0),
            ("thing/product/+/osd", 0), ("thing/product/+/events", 0),
            ("thing/product/+/state", 0), ("thing/product/sn", 0)
        ]
        client.subscribe(topics)
    else:
        console.print(f"[bold red]❌ CONNECTION FAILED (RC: {rc})[/bold red]")

def on_message(client, userdata, msg):
    if commander:
        commander.process_traffic(msg.topic, msg.payload)
        if commander.debug_mode:
            print(".", end="", flush=True)

# ======================================================
# 3. REPLAY ENGINE
# ======================================================
def start_replay(file, jump, speed, target_ip):
    global replay_process
    console.print(Panel(f"[bold magenta]📼 TIME MACHINE ACTIVE: {file}[/bold magenta]"))
    console.print(f"[dim]   -> Injecting Telemetry into: {target_ip}[/dim]")
    
    cmd = [sys.executable, "labs/replay/replay_tool.py", file, "--ip", target_ip, "--speed", str(speed)]
    if jump: cmd.append("--jump")
    
    try:
        replay_process = subprocess.Popen(cmd)
    except FileNotFoundError:
        console.print("[red]❌ Replay Tool not found in labs/replay/replay_tool.py[/red]")

def cleanup(sig, frame):
    console.print("\n\n[bold yellow]🛑 MISSION END. DISENGAGING...[/bold yellow]")
    if replay_process:
        console.print("[magenta]Stopping Replay Engine...[/magenta]")
        replay_process.terminate()
    sys.exit(0)

# ======================================================
# 4. MAIN EXECUTION
# ======================================================
def main():
    global commander
    signal.signal(signal.SIGINT, cleanup)

    args = get_cli_args()

    if args.replay:
        target_ip = args.ip if args.ip != "192.168.192.100" else "127.0.0.1"
        args.ip = target_ip 
        start_replay(args.replay, args.jump, args.speed, target_ip)
        time.sleep(2) 

    console.print(Panel.fit(f"[bold yellow]🦅 GHOST COMMANDER v2.7 (Modular Platform)[/bold yellow]"))
    
    ai_engine = "openai" if args.cloud else "ollama"
    model_name = "gpt-4o" if args.cloud else args.model.replace("ollama:", "")
    
    console.print(f"🧠 BRAIN: [bold green]{model_name.upper()} ({ai_engine})[/bold green]")
    console.print(f"🎭 PERSONA: [bold cyan]{args.persona.upper()}[/bold cyan] | 📡 BROKER: {args.ip}")

    # Correctly initializing the Commander with Hue support
    commander = GhostCommander(
        ai_engine=ai_engine, 
        model=model_name, 
        record_enabled=args.record, 
        hue_enabled=args.hue
    )
    commander.debug_mode = args.debug
    commander.track_traffic = args.traffic

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        client.connect(args.ip, args.port, 60)
        client.loop_start()
    except Exception as e:
        console.print(f"[bold red]❌ NETWORK ERROR: {e}[/bold red]")
        sys.exit(1)

    last_report = time.time()
    
    while True:
        try:
            time.sleep(1)
            if time.time() - last_report > args.interval:
                console.print(Panel(f"[bold cyan]⚡ DIRECTOR UPDATE ({time.strftime('%H:%M:%S')})[/bold cyan]", border_style="cyan"))
                
                report = commander.generate_sitrep(args.persona, show_prompt=args.show_prompt)
                console.print(f"[white]{report}[/white]")
                
                if args.voice:
                    try:
                        subprocess.Popen(["say", "-v", args.voice_id, "-r", "185", report])
                    except FileNotFoundError: pass
                
                last_report = time.time()
                
        except KeyboardInterrupt:
            cleanup(None, None)

if __name__ == "__main__":
    main()
