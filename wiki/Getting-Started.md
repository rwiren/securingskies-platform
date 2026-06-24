# 🚀 Getting Started
[**Home**](Home) > **Getting Started**

This page walks you through installing, configuring, and running the SecuringSkies Platform
from scratch.

---

## Prerequisites

| Requirement | Version | Notes |
| :--- | :--- | :--- |
| Python | 3.12+ | Verify with `python3 --version` |
| Ollama | latest | Local LLM runtime — [download](https://ollama.com) |
| Mosquitto | 2.x | MQTT broker — `brew install mosquitto` / `apt install mosquitto` |
| Git | any | For cloning the repository |

---

## 1. Clone the Repository

```bash
git clone https://github.com/rwiren/securingskies-platform.git
cd securingskies-platform
```

---

## 2. Create a Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Configure Environment Variables

Copy the example file and fill in your values:

```bash
cp .env.example .env
```

Open `.env` in your editor and set at minimum:

```dotenv
# Required — your local Mosquitto IP or the cloud broker
MQTT_BROKER=192.168.192.100

# Required for 3D dashboard — obtain free token at https://ion.cesium.com/tokens
CESIUM_TOKEN=your_token_here

# Required for cloud AI mode (--cloud flag)
OPENAI_API_KEY=sk-...

# Required for local AI mode (default) — leave as-is for localhost
OLLAMA_HOST=http://localhost:11434

# Required only if using --hue flag
HUE_BRIDGE_IP=192.168.1.228
```

---

## 5. Start Infrastructure

### MQTT Broker (Mosquitto)
```bash
# macOS (Homebrew)
brew services start mosquitto

# Linux (systemd)
sudo systemctl start mosquitto

# Docker (from ops/stack/)
cd ops/stack && docker compose up -d
```

### Local AI Engine (Ollama)
```bash
# Pull the default model (first run only)
ollama pull llama3.1

# Start the Ollama server
ollama serve
```

---

## 6. Run the Platform

### Ghost Commander (Live Mission)
Connect to your MQTT broker and start the AI Officer:

```bash
# Pilot mode — local AI, no extras
python3 main.py --persona pilot --model llama3.1

# Analyst mode — cloud AI + voice + Hue lighting
python3 main.py --persona analyst --cloud --voice --hue --ip 192.168.1.100

# Full debug mode
python3 main.py --persona commander --debug --record --metrics
```

### Tactical Dashboard (Web)
Opens the 2D/3D map in your browser at `http://localhost:5000`:

```bash
python3 web/server.py
```

---

## 7. Replay a Previous Mission

Re-live a recorded log at any speed:

```bash
# Replay at 1.0× speed, jumping to first airborne event
python3 main.py --replay golden_datasets/mission_20260127_172522.jsonl --jump

# Replay at 4× speed
python3 main.py --replay logs/mission_20260203_102010.jsonl --speed 4.0
```

---

## 8. Available CLI Flags

| Category | Flag | Description |
| :--- | :--- | :--- |
| **Mission** | `--persona [NAME]` | `pilot`, `commander`, or `analyst`. Default: `pilot` |
| | `--interval [SEC]` | Seconds between AI reports. Default: `45` |
| | `--traffic` | Track Cars/Trucks via Vision AI |
| **Network** | `--ip [IP]` | MQTT Broker address. Default: `192.168.192.100` |
| | `--port [PORT]` | Broker port. Default: `1883` (or `8883` for TLS) |
| | `--tls` | Enable SSL/TLS encryption |
| | `--cloud` | Use OpenAI GPT-4o instead of local Ollama |
| | `--model [NAME]` | Local LLM model name. Default: `llama3.1` |
| **Output** | `--voice` | Enable Text-to-Speech (macOS `say` command) |
| | `--voice_id [ID]` | Voice persona. Default: `Satu` |
| | `--hue` | Enable Philips Hue integration |
| **Logging** | `--record` | Save mission log to `logs/mission_*.jsonl` |
| | `--metrics` | Enable scientific accuracy CSV logging |
| **Debug** | `--debug` | Show raw JSON stream in console |
| | `--show-prompt` | Display AI system prompt (once) |
| **Replay** | `--replay [FILE]` | Path to `.jsonl` log file |
| | `--jump` | Skip to first airborne event |
| | `--speed [FLOAT]` | Playback speed multiplier. Default: `1.0` |

---

## Troubleshooting

**Connection refused on MQTT:**
Check that Mosquitto is running: `mosquitto -v` or `docker ps`.

**Ollama not responding:**
Ensure the server is running: `ollama serve`. Confirm the model is pulled: `ollama list`.

**3D globe shows black screen:**
Set `CESIUM_TOKEN` in your `.env`. Without a valid token, the dashboard falls back to 2D OpenStreetMap automatically.

**Hue bridge not connecting:**
Ensure `HUE_BRIDGE_IP` is correct and press the physical button on your Hue Bridge before first connection.
