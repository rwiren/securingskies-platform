# 🦅 SecuringSkies Platform (AGCS)

> **Autonomous Ground Control Station for UAS Situational Awareness**

[![Version](https://img.shields.io/badge/Version-v1.2.7-success?style=for-the-badge&logo=github)](https://github.com/rwiren/securingskies-platform/releases)
[![AI Engine](https://img.shields.io/badge/Intelligence-Llama_3.1_%7C_Gemma_2-blueviolet?style=for-the-badge&logo=openai)](https://ollama.com)
[![Protocol](https://img.shields.io/badge/Telemetry-MQTT_%7C_MAVLink_%7C_RID-orange?style=for-the-badge)](https://mqtt.org)

---

## 📡 System Overview

**SecuringSkies** is an open-source Autonomous Ground Control Station (AGCS) designed to
provide cognitive situational awareness for drone operators. Unlike traditional GCS software
that displays raw data, SecuringSkies uses an **Event-Driven Micro-Kernel** to fuse telemetry
and **Local Large Language Models (LLMs)** to analyze the airspace in real-time. It acts as a
"Ghost Commander"—a vocal co-pilot that provides tactical advice, risk assessment, and anomaly
detection without requiring visual attention.

## 🎯 The Mission: Eyes-Up Situational Awareness

**The Problem:** Field engineers often work alone. Whether flying a drone to validate sensors or
driving a vehicle to establish ground truth, you cannot look down at a laptop to check logs or telemetry.

**The Solution:** SecuringSkies acts as a **"Ghost Commander"**—an AI co-pilot that continuously
monitors live MQTT streams (Ground Truth + Sensor Data) and speaks critical anomalies to you via
voice synthesis.

**The Value:**
* **Safety:** Keep your eyes on the drone/road, not the screen.
* **Calibration:** Logs strictly timestamped data (`tst`) to correlate "Ground Truth" positions
  with sensor readings later.
* **Scientific Validation:** Provides real-time feedback on GNSS accuracy (`RTK-FIX` vs `FLOAT`)
  and calculates **Glass-to-Glass Latency** so you don't waste hours recording bad data.

---

### 🧠 Core Philosophy: The OODA Loop

The system creates an AI-driven feedback loop based on the OODA (Observe-Orient-Decide-Act) model:

1. **Observe:** Ingests heterogeneous telemetry (Autel Enterprise, Remote ID, OwnTracks, MAVLink).
2. **Orient:** Normalizes data into a unified tactical map (The `TelemetryBuffer`) using a Semantic
   Identity Engine.
3. **Decide:** Uses persona-based AI agents (Pilot, Commander, Analyst) to interpret the situation
   under **Constitutional Guardrails**.
4. **Act:** Verbalizes concise SITREPs (Situation Reports) and triggers ambient lighting alerts (Hue).

---

## 🚀 Key Capabilities

| Component | Function | Technology |
| :--- | :--- | :--- |
| **Multi-Vendor Fusion** | Unifies proprietary drone data with open standards. | `Autel V3` + `ASTM F3411 (RID)` + `OwnTracks` |
| **Neural Analysis** | Context-aware reasoning with safety overrides. | `Ollama` (Llama 3.1 / Gemma 2) + `Regex Guardrails` |
| **AI Optimization** | DSPy-compiled prompts for brevity and factuality. | `DSPy BootstrapFewShot` + `labs/optimizer.py` |
| **Scientific Logging** | "Black Box" recording with Latency KPIs. | JSONL Stream + `auditor.py` Metrics |
| **Tactical Dashboard** | Real-time visual tracking — 2D and 3D globe. | `Flask` + `Flask-SocketIO` + `LeafletJS` + `CesiumJS` |
| **Adaptive Personas** | Switch engagement rules instantly. | **PILOT** (Tactical), **COMMANDER** (Strategic), **ANALYST** (Forensic) |

---

## 🌍 Roadmap Summary

See the full [Roadmap](Roadmap) page for milestones, upcoming domains, and completed phases.

| Version | Status | Theme |
| :--- | :--- | :--- |
| v0.9.0 – v0.9.9 | ✅ Complete | Modular refactor, field validation, stabilization |
| v1.0.0 | ✅ Complete (Jan 26, 2026) | Micro-Kernel release; SSTP validation |
| v1.2.3 | ✅ Complete (Jan 27, 2026) | DSPy optimization; Golden Datasets |
| **v1.2.7** | ✅ **Current** (Feb 3, 2026) | Unified 3D Dashboard; Cesium integration |
| v1.x | 🔭 Planned | Cyber-Electronic Defense (SIEM / Arkime) |
| v2.0 | 🔭 Planned | ADS-B fusion; Swarm deconfliction |

---

## 🤝 Contribute

SecuringSkies is a research initiative. Pull requests regarding MAVLink integration,
Cyber-Defense modules, and DSPy prompt optimization are welcome.

*Maintained by the SecuringSkies Research Grid.*
