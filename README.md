# 🦅 SecuringSkies Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-v1.2.7-success.svg)](#)
[![Wiki](https://img.shields.io/badge/Docs-Wiki-blueviolet.svg)](https://github.com/rwiren/securingskies-platform/wiki)
[![Status](https://img.shields.io/badge/Status-Field_Proven-success.svg)](https://github.com/rwiren/securingskies-platform/wiki/Field%E2%80%90Reports)
[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](#)
[![Code Style](https://img.shields.io/badge/Code%20Style-Black-000000.svg)](https://github.com/psf/black)
[![Last Commit](https://img.shields.io/github/last-commit/rwiren/securingskies-platform?style=flat&color=blue)](https://github.com/rwiren/securingskies-platform/commits/main)

**Status:** RELEASED v1.2.7.

**Intelligence:** Neural (Llama 3.1 / Gemma 2) + Deterministic (RTK/Telemetry)  
**Documentation:** [**Read the Field Reports & Benchmarks on the Wiki**](https://github.com/rwiren/securingskies-platform/wiki)

The **SecuringSkies Platform** is an AI-driven sensor fusion engine that turns raw telemetry (Air/Ground/RF) into a **Vocal** Co-Pilot. It provides hands-free, real-time situational awareness and precise logging for field engineers conducting sensor validation and calibration as well as an Autonomous Ground Control Station (AGCS) designed to fuse data from heterogeneous sources (Drones, Ground Assets, Remote ID and more) into a single, AI-analyzed tactical picture, and provide Situational Awereness, ie. SITREP report based on specific stakeholder needs.

---

## 📑 Table of Contents
- [🦅 SecuringSkies Platform](#-securingskies-platform)
  - [🏛️ Architectural Overview](#️-architectural-overview)
    - [Core Capabilities](#core-capabilities)
  - [📂 Project Structure](#-project-structure)
  - [🚀 Quick Start](#-quick-start)
    - [1. The "Ghost Commander" (Live Mission)](#1-the-ghost-commander-live-mission)
    - [2. The "Time Machine" (Replay)](#2-the-time-machine-replay)
  - [🧪 Field Validation](#-field-validation)
  - [🛡 License & Citation](#-license--citation)
  - [🤝 How to Contribute](#-how-to-contribute)

---

## 🏛️ Architectural Overview

This system functions as a publish-subscribe hub via MQTT, fusing telemetry from:
1.  **UAS Remote ID (ASTM F3411)** over 4G via Dronetag Cloud Bridge and (tls) encrypted forwarding.
2.  **Proprietary UAV Telemetry** (Autel Enterprise) via direct locally hosted secured OSD Bridge (RTK-Enabled).
3.  **Mobile Ground Assets** (OwnTracks) also via end to end encrypted networking.

### Core Capabilities
* **Real-time RTK Decoding:** Parses GNSS state bitmasks for centimeter-level accuracy (`RTK-FIX` vs `RTK-FLOAT` or only `GNSS`).
* **Multi-Agent Sensor Fusion:** Combines Ground + Air + Computer Vision streams into a unified fleet state.
* **LLM-driven Situational Awareness:** Uses OpenAI GPT-4o or Ollama Llama3.1 to generate "Voice of Persona" briefings based on forensic data. Includes possibility to easily switch between models and "Prompts Persona´s" (Pilot, Commander and, Analyst) that can be self-optimized based on different **Use Cases** or **Stakeholder needs**. 
* **Black Box Logging:** Saves forensic evidence in `jsonl` standard for mission replay.
* **Latency Watchdog:** Monitors queue depth to prevent "Time Travel" reporting.

---

## 📂 Project Structure

```plaintext
securingskies-platform/
├── securingskies/              # 🦅 THE CORE PLATFORM
│   ├── main.py                 # -> Internal Bootloader
│   ├── core/                   # -> The "Brain" (Logic Unit)
│   │   └── officer.py          #    (Ingestion, Normalization & AI)
│   ├── outputs/                # -> The "Voice" (IO Subsystem)
│   │   ├── auditor.py          #    (Scientific Metrics Engine)
│   │   ├── recorder.py         #    (Black Box Logger)
│   │   └── hue.py              #    (Philips Hue Bridge)
│   └── utils/                  # -> Shared Libraries
│       └── geo.py              #    (Geodesic Math)
│
├── config/                     # ⚙️ CONFIGURATION
│   ├── personas.json           # -> Standard System Prompts
│   └── optimized_*.json        # -> Optimized DSPy Artifacts
│
├── docs/                       # 📘 KNOWLEDGE BASE
│   ├── ARCHITECTURE.md         # -> System Design Document
│   ├── TEST_PLAN.md            # -> TDD Strategy
│   ├── TESTCASES.md            # -> Field Validation Cases
│   └── TECH_DEBT.md            # -> Architectural Trade-offs
│
├── labs/                       # 🧪 RESEARCH & DEVELOPMENT
│   ├── replay/                 # -> "Time Machine" (HITL Tools)
│   │   └── replay_tool.py
│   ├── optimizer/              # -> DSPy Prompt Optimization
│   ├── optimizer.py            # -> Training Entry Point (DSPy)
│   ├── eda_mission_analysis.py # -> Exploratory Data Analysis & Visualization
│   ├── compare_sensors.py      # -> Twin-Sensor Correlation Analysis
│   ├── compare_data_sources.py # -> Data Source Comparison Tool
│   └── analyze_latency_effects.py # -> Latency Error Decomposition
│
├── ops/                        # 🏗️ DEVOPS
│   └── stack/                  # -> Docker Compose (Mosquitto/Grafana)
│
├── web/                        # 🌐 WEB DASHBOARD 
│   ├── server.py               # -> Lightweight Web Server
│   ├── static/                 # -> JS/CSS Assets
│   └── templates/              # -> HTML Views
│
├── golden_datasets/            # 🏆 VALIDATION DATA
│   └── mission_*.jsonl         # -> High-Fidelity Jorvas Flight Logs (Ground Truth)
│
├── logs/                       # 💾 TELEMETRY (GitIgnored)
│   └── ...                     #    (Local Mission Data)
│
├── main.py                     # 🚀 CLI ENTRY POINT
├── requirements.txt            # -> Dependency Manifest
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

### 3. The "Data Explorer" (EDA Analysis)
Generate comprehensive visualizations and statistics from mission logs.

```bash
# Analyze the golden dataset with full EDA suite
python3 labs/eda_mission_analysis.py

# Analyze a custom mission file
python3 labs/eda_mission_analysis.py --input logs/mission_YYYYMMDD_HHMMSS.jsonl --output my_analysis/
```

Generates 9 visualization plots including:
- Multi-sensor flight paths
- Altitude profiles and vertical speed
- Speed analysis and heading correlation
- Battery monitoring for all assets
- Link quality and message rate metrics
- Temporal distribution of events
- **GNSS accuracy comparison (RTK vs GPS)** 🆕
- **Latency analysis across data sources** 🆕
- Comprehensive statistical summaries

See [docs/eda_plots/README.md](docs/eda_plots/README.md) for detailed documentation.

### 4. The "Data Comparator" (Source Analysis)
Compare MQTT telemetry with raw flight data files to analyze data richness.

```bash
# Compare MQTT data with raw files from same flight session
python3 labs/compare_data_sources.py

# Custom paths
python3 labs/compare_data_sources.py \
  --mqtt golden_datasets/mission_20260127_172522.jsonl \
  --raw-dir data/raw \
  --output docs/data_comparison
```

Analyzes and compares:
- **MQTT telemetry**: 110 unique fields across 8 topics (4.53 Hz)
- **Airdata CSV**: 53 drone-specific fields (4.52 Hz)  
- **Dronetag exports**: 14 Remote ID fields (0.96 Hz)

Generates comparison visualization and detailed report highlighting differences in data richness, temporal coverage, and field availability.

See [docs/data_comparison/README.md](docs/data_comparison/README.md) for analysis results.

### 5. The "Latency Analyzer" (Error Decomposition)
Decompose sensor position error into Hardware Gap and Time Gap components.

```bash
# Analyze latency effects on sensor accuracy
python3 labs/analyze_latency_effects.py

# Custom paths
python3 labs/analyze_latency_effects.py \
  --mqtt golden_datasets/mission_20260127_172522.jsonl \
  --output docs/latency_analysis
```

Implements the data fusion formula:
```
Total Error = √((Hardware Gap)² + (Speed × Latency)²)
```

**Key Findings:**
- Hardware Gap (Sensor Accuracy): 2.26m
- Network Latency: 1.19s
- At 10 m/s cruise speed: Total error = 12.09m (2.26m sensor + 11.87m latency)
- Altitude error remains low (~4.36m) - independent of latency

Generates comprehensive visualization showing error decomposition by flight scenario and validates that position accuracy is HIGHLY dependent on latency while altitude accuracy is mostly independent.

See [docs/latency_analysis/README.md](docs/latency_analysis/README.md) for detailed analysis.

---

## 💡 Operational Flags

| Category | Flag | Description |
| :--- | :--- | :--- |
| **Mission** | `--persona [NAME]` | AI Personality (`pilot`, `commander`, `analyst`). Default: `pilot`. |
| | `--interval [SEC]` | Seconds between voice reports. Default: `45`. |
| | `--traffic` | Enables AI Computer Vision tracking for Cars/Trucks. When not enabled the system still tracks High Value targets such as Humans and Drones by default.|
| **Network** | `--ip [IP]` | MQTT Broker Address. Default: `192.168.192.100`. |
| | `--port [PORT]` | MQTT Broker Port. Default: `8883` (tls), however `1883` also supported if using encrypted networking.  |
| | `--cloud` | Use OpenAI GPT-4o (Smarter, costs money) instead of local Ollama. |
| | `--model [NAME]` | Local LLM Model Name. Default: `llama3.1`. |
| **Output** | `--voice` | Enables Text-to-Speech (MacOS `say` command). |
| | `--voice_id [ID]` | Selects the system voice. Default: `Satu` Finnish/English ;-). |
| | `--hue` | Enables Philips Hue integration (Blue=Contact, Red=Lost). |
| **Logging** | `--record` | Saves a `logs/mission_YYYYMMDD.jsonl` file (Recommended). |
| | `--metrics` | Enables Scientific Accuracy Logging (`logs/metrics_*.csv`). |
| **Debug** | `--debug` | Shows raw JSON stream dots (`.......`) in the console. |
| | `--show-prompt` | Displays the hidden System Prompt sent to the AI. |
| **Replay** | `--replay [FILE]` | Path to a `.jsonl` log file for Time Machine mode. |
| | `--jump` | Skips empty data to the first "Airborne" event. |
| | `--speed [FLOAT]` | Playback speed multiplier (e.g., `2.0` for 2x). Default: `1.0`. |

---

## 🧪 Field Validation & Scientific Benchmarking

The platform validates architectural theses through rigorous Hardware-in-the-Loop (HITL) field trials, moving beyond theoretical simulation into physical RF environments.

* **Operation "Sibbo Gauntlet" (Jan 2026):**
    * **Scope:** High-velocity Telemetry Fusion ($v > 100 \text{ km/h}$) and Computer Vision integration.
    * **Result:** Validated real-time correlation of heterogeneous data streams (Autel, OwnTracks, Android) under dynamic urban conditions.
* **Operation "Jorvas Triangle" (Jan 2026):**
    * **Scope:** Twin-Sensor Calibration and AI Doctrine Optimization.
    * **Result:** Quantified GNSS drift ($L_{net}$ vs $L_{c2}$) and validated the **OPS-002** DSPy Optimization protocol, achieving 100% Factuality Scores in AI reporting.

> 📚 **Methodology & Data:** Review full [Mission Logs and Benchmarks](https://github.com/rwiren/securingskies-platform/wiki) on the Wiki.

---

## 🛡 License & Citation

**MIT License** - Open for academic and research use.

### Citation
If you use this dataset, architecture, or tooling in your research, please cite:

> Wiren, Richard. (2026). *SecuringSkies: Autonomous Multi-Agent Fusion Platform*.

See [CITATION.cff](https://github.com/rwiren/securingskies-platform/blob/main/CITATION.cff) for BibTeX format.

---

## 🤝 How to Contribute

We follow a lean Research & Development workflow focused on the **nightly** branch.

### 1. The Golden Rule
**Nightly is the Edge.** We develop on `nightly`. `main` is for stable releases only.

### 2. Workflow
1.  **Sync:** `git checkout nightly && git pull origin nightly`
2.  **Branch:** `git checkout -b feat/your-new-driver`
3.  **Test:** * Run `python3 web/server.py` (Dashboard)
    * Run `python3 labs/sim_px4.py` (Simulator)
    * *Verify the Orange Dot appears.*
4.  **Commit:** Use [Conventional Commits](https://www.conventionalcommits.org/) (e.g., `feat:`, `fix:`, `docs:`).
5.  **Push:** Push to origin and open a PR against `nightly`.

### 3. Setup
-   **Secrets:** We use a local `.env` file (not committed) for IP configuration.
    ```bash
    cp .env.example .env
    # Edit MQTT_BROKER=192.168.x.xx
    # I can also provide you MQTT_BROKER= mqtt.securingskies.eu (need to ask for credentials)
    ```
-   **Environment:** Standard Python Virtual Environment.
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

---
*SecuringSkies Research Grid | Status: main v1.2.7*
