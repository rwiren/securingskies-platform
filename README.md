# 🦅 SecuringSkies Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-v0.9.0-green.svg)](#)
[![Status](https://img.shields.io/badge/Status-Operational-success.svg)](#)
[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](#)
[![Code Style](https://img.shields.io/badge/Code%20Style-Black-000000.svg)](https://github.com/psf/black)

**Status:** PRODUCTION (Modular Enterprise Architecture)  
**Intelligence:** Neural (Ollama/OpenAI) + Deterministic (RTK/Telemetry)  
**Legacy Parity:** 100% (All features from `v47` restored)

The **SecuringSkies Platform** is an Autonomous Ground Control Station (AGCS) designed to fuse data from heterogeneous sources (Drones, Ground Assets, Remote ID) into a single, AI-analyzed tactical picture.

---

## 📑 Table of Contents
- [🦅 SecuringSkies Platform](#-securingskies-platform)
  - [🏛️ Architectural Overview](#️-architectural-overview)
    - [Core Capabilities](#core-capabilities)
  - [📂 Project Structure](#-project-structure)
  - [🚀 Quick Start](#-quick-start)
    - [1. The "Ghost Commander" (Live Mission)](#1-the-ghost-commander-live-mission)
    - [2. The "Time Machine" (Replay)](#2-the-time-machine-replay)
  - [📡 Telemetry Standards](#-telemetry-standards)
  - [💡 Operational Flags](#-operational-flags)
  - [🛡 License \& Citation](#-license--citation)
  - [🤝 How to Contribute](#-how-to-contribute)
---

## 🏛️ Architectural Overview

This system functions as a publish-subscribe hub via MQTT, fusing telemetry from:
1.  **UAS Remote ID (ASTM F3411)** via Dronetag Cloud Bridge.
2.  **Proprietary UAV Telemetry** (Autel Enterprise) via OSD Bridge (RTK-Enabled).
3.  **Mobile Ground Assets** (OwnTracks) via encrypted mesh network.

### Core Capabilities
* **Real-time RTK Decoding:** Parses GNSS state bitmasks for centimeter-level accuracy (`RTK-FIX` vs `RTK-FLOAT`).
* **Multi-Agent Sensor Fusion:** Combines Ground + Air + Computer Vision streams into a unified fleet state.
* **LLM-driven Situational Awareness:** Uses OpenAI GPT-4o or Ollama Llama3.1 to generate "Voice of God" briefings based on forensic data.
* **Black Box Logging:** Saves forensic evidence in `jsonl` standard for mission replay.
* **Latency Watchdog:** Monitors queue depth to prevent "Time Travel" reporting.

---

## 📂 Project Structure

```plaintext
securingskies-platform/
├── securingskies/              # 🦅 THE CORE PLATFORM (The Agent)
│   ├── main.py                 # -> The Entry Point (CLI & Bootloader)
│   ├── core/                   # -> The "Brain"
│   │   └── officer.py          #    (GhostCommander Logic & State Management)
│   ├── drivers/                # -> The "Ears" (Hardware Abstraction Layer)
│   │   ├── autel.py            #    (Autel Enterprise V3 + RTK Decoder)
│   │   ├── dronetag.py         #    (Remote ID ASTM F3411 Parser)
│   │   └── owntracks.py        #    (Ground Asset & Pilot Tracker)
│   ├── outputs/                # -> The "Voice" (User Interface)
│   │   ├── hue.py              #    (Philips Hue Lighting Controller)
│   │   └── recorder.py         #    (Black Box JSONL Logger)
│   │   └── auditor.py          #    (Scientific Metrics Engine)
│   ├── integration/            # -> [Future] Connectors (InfluxDB, OpenSearch Writers)
│   └── utils/                  # -> Math & Shared Helpers (Geo/Haversine)
│
├── config/                     # ⚙️ CONFIGURATION
│   ├── personas.json           # -> Standard System Prompts
│   └── personas_v2.json        # -> DSPy Optimized Prompts ("The Golden Prompts")
│
├── logs/                       # 💾 MISSION DATA
│   ├── mission_*.jsonl         # -> Raw Black Box Data (Forensic Evidence)
│   └── metrics_*.csv           # -> Performance Report Cards
│
├── ops/                        # 🏗️ INFRASTRUCTURE (DevOps)
│   ├── stack/                  # -> Docker Compose (Mosquitto, Grafana, OpenSearch)
│   └── systemd/                # -> System Service Files
│
├── labs/                       # 🧪 R&D (The Sandbox)
│   ├── replay/                 # -> "Time Machine" (Forensic Replay Tools)
│   ├── optimizer/              # -> DSPy Prompt Training Scripts
│   └── experiments/            # -> Prototype Code
│
├── web/                        # 🌐 WEB DASHBOARD [Future]
│   ├── server.py               # -> Lightweight Web Server
│   ├── static/                 # -> JS/CSS Assets
│   └── templates/              # -> HTML Views
│
├── docs/                       # 📘 KNOWLEDGE BASE
│   └── ARCHITECTURE.md         # -> Network Diagrams & Design Docs
│
└── archive/                    # 🏛️ THE MUSEUM
    └── legacy/                 # -> Deprecated Monoliths (v47.py)
```

---

## 🚀 Quick Start

### 1. The "Ghost Commander" (Live Mission)
Connects to the local MQTT broker and starts the AI Officer.

```bash
# Standard Analyst Mode (Cloud AI + Voice + Lights)
python3 securingskies/main.py --persona analyst --cloud --voice --hue --ip 192.168.1.100

# Stealth Mode (Local AI, No Voice, Traffic Tracking)
python3 securingskies/main.py --persona pilot --model llama3.1 --traffic --record
```

### 2. The "Time Machine" (Replay)
Re-lives a previous mission log as if it were happening *right now*.

```bash
# Replay a log at 1.0x speed, jumping to the interesting part
python3 securingskies/main.py --replay logs/mission_20260124_192621.jsonl --jump --show-prompt
```

---

## 💡 Operational Flags

| Category | Flag | Description |
| :--- | :--- | :--- |
| **Mission** | `--persona [NAME]` | AI Personality (`pilot`, `commander`, `analyst`). Default: `pilot`. |
| | `--interval [SEC]` | Seconds between voice reports. Default: `45`. |
| | `--traffic` | Enables AI Computer Vision tracking for Cars/Trucks. |
| **Network** | `--ip [IP]` | MQTT Broker Address. Default: `192.168.192.100`. |
| | `--port [PORT]` | MQTT Broker Port. Default: `1883`. |
| | `--cloud` | Use OpenAI GPT-4o (Smarter, costs money) instead of local Ollama. |
| | `--model [NAME]` | Local LLM Model Name. Default: `llama3.1`. |
| **Output** | `--voice` | Enables Text-to-Speech (MacOS `say` command). |
| | `--voice_id [ID]` | Selects the system voice. Default: `Satu`. |
| | `--hue` | Enables Philips Hue integration (Blue=Contact, Red=Lost). |
| **Logging** | `--record` | Saves a `logs/mission_YYYYMMDD.jsonl` file (Recommended). |
| | `--metrics` | Enables Scientific Accuracy Logging (`logs/metrics_*.csv`). |
| **Debug** | `--debug` | Shows raw JSON stream dots (`.......`) in the console. |
| | `--show-prompt` | Displays the hidden System Prompt sent to the AI. |
| **Replay** | `--replay [FILE]` | Path to a `.jsonl` log file for Time Machine mode. |
| | `--jump` | Skips empty data to the first "Airborne" event. |
| | `--speed [FLOAT]` | Playback speed multiplier (e.g., `2.0` for 2x). Default: `1.0`. |

---

---

## 🛡 License & Citation

**MIT License** - Open for academic and research use.

### Citation
If you use this dataset, architecture, or tooling in your research, please cite:

> Wiren, Richard. (2026). *SecuringSkies: Autonomous Multi-Agent Fusion Platform* [Software]. https://github.com/rwiren/securingskies-platform

See `CITATION.cff` for BibTeX format.

---

## 🤝 How to Contribute

We follow a strict DevOps workflow to ensure integrity across Apple Silicon, Intel, and Windows.

### 1. The Golden Rule
**Main is protected.** Never push directly to main. Always use a feature branch.

### 2. Workflow
1.  **Sync:** `git checkout main && git pull origin main`
2.  **Branch:** `git checkout -b feature/your-feature-name`
3.  **Test:** Run `make report` (Must pass locally!)
4.  **Commit:** Use [Conventional Commits](https://www.conventionalcommits.org/) (e.g., `feat:`, `fix:`, `docs:`).
5.  **Merge:** Open a Pull Request.

### 3. Setup
- **Vault Password:** You need the project secret to decrypt configuration files.
    - *Action:* Ask the Maintainer for the password, then run:
    - `echo 'THE_PASSWORD' > .vault_pass`
- **Environment:** Run `make setup` to initialize the Python environment.

---

*SecuringSkies Research Grid | Status: OPERATIONAL*

