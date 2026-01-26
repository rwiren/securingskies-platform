# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-01-26
**Status:** RELEASE (Stable)

### Added
- **Architecture:** Implemented `officer.py` (Micro-Kernel) to replace legacy `drivers/` folder, reducing ingestion latency to <100ms.
- **Protocol:** Adopted **SSTP v1.0** (SecuringSkies Test Protocol) compliant with IEEE 829.
- **KPIs:** Added Network Latency (Glass-to-Glass) and C2 Latency calculation in `auditor.py`.
- **Docs:** Added `docs/TECH_DEBT.md` to track architectural trade-offs.

### Changed
- **Logic:** Refactored Asset Identification to strictly separate "Ground Station (GCS)" from "UAV" based on metadata type.
- **Safety:** Updated System Prompt to include "Constitutional Guardrails" (Regex overrides) for anti-hallucination.
- **Units:** Standardized OwnTracks velocity from `km/h` to `m/s` for consistency with Physics Engine.

### Fixed
- **Stability:** Resolved `TypeError` in `geo.py` when telemetry contains `lat: null` (Verified via TC-07).
- **Crash:** Fixed `NoneType` timestamp error in `labs/replay/replay_tool.py` when parsing corrupted logs.
- **UI:** Suppressed repeating System Prompt spam in the console output.

## [0.9.9 RC] - 2026-01-25
**Status:** PRE-RELEASE (Field Proven)

### Added
- **Hardware:** Native support for Pixhawk/ArduPilot telemetry via `drivers/mavlink.py`.
- **Visualization:** Real-time LeafletJS map server (`web/server.py`).
- **Logging:** Added `mission_*.jsonl` (Black Box) and `metrics_*.csv` (Performance) streams.

### Fixed
- **Critical:** Fixed "Ghost Assets" bug where Autel Controller and UAV were reported as separate unknown entities.
- **Critical:** Fixed AI reporting moving cars as "Stationary" due to unit mismatch.

## [0.9.9-patch1] - 2026-01-26
### Fixed
- **Identity Crisis:** Implemented Semantic Labeling to explicitly distinguish "Ground Station (GCS)" from "UAV".
- **Hallucinations:** Added "Constitutional Guardrails" to the System Prompt to override stale few-shot examples.
- **UI:** Fixed repeating System Prompt spam; added heartbeat dots (`.`) for better connection visibility.

### Added
- **KPI:** Real-time **Network Latency** calculation for Dronetag (ISO 8601 parsing).
- **KPI:** **C2 Latency** calculation for Autel Smart Controller (Heartbeat analysis).
- **Replay:** Validated HITL simulation speeds for post-mission analysis.

## [0.9.9] - 2026-01-25 (The "Sibbo Gauntlet" Release)
**Status:** FIELD PROVEN (Stable)
**Focus:** Field Validation, Hardware Integration, and Driver Stabilization.

### 🚀 Validated (Field Operations)
- **Operation "Sibbo Gauntlet":** Successful end-to-end validation of the AGCS in Vantaa/Sipoo.
- **Fusion Engine:** Validated simultaneous tracking of Ground (OwnTracks), Air (Autel), and Vision AI assets.
- **AI Personas:** Confirmed efficacy of **Llama 3.1** (Pilot) for tactical alerts and **Gemma 2** (Commander) for strategic reasoning.
- **Stress Testing:** Validated system stability under "Ghost Wall" conditions (8+ vision targets).

### 🚑 Field Hotfixes (Critical)
- **Null GPS Crash:** Fixed `TypeError` in `geo.py` when drones initialize with `lat: null` (v0.9.9e).
- **Ghost Assets:** Added aggregation logic to `officer.py` to merge Autel Controller and UAV streams (v0.9.9d).
- **Speed Units:** Fixed logic where AI reported moving cars as "Stationary" by converting OwnTracks `km/h` to `m/s` (v0.9.9f).
- **Battery Glitch:** Added safety checks for `0%` battery reports from telemetry signal loss.

### 🚀 Added
- **MAVLink Bridge:** Native support for Pixhawk/ArduPilot telemetry via `drivers/mavlink.py`.
- **Web Dashboard:** Real-time LeafletJS map server (`web/server.py`) for visual tracking.
- **Scientific Logging:** Added `mission_*.jsonl` (Black Box) and `metrics_*.csv` (Performance) streams.
- **Instrument Flight Rules (IFR):** AI now analyzes Vertical Speed (`V-SPD`) and Horizontal Speed (`H-SPD`) for non-visual situational awareness.

### ⚡ Improved
- **GPS Logic:** Strict thresholds (<1m = RTK, >5m = Poor) to prevent AI overconfidence.
- **Console Hygiene:** Silenced `LiteLLM` and `HTTPX` noise for cleaner tactical display.
- **Architecture:** Decoupled `officer.py` from drivers to allow "Fail-Loud" debugging during field ops.

### 🐛 Fixed
- **Hallucinations:** Fixed logic where AI would invent visual contacts when sensor data was missing.
- **Import Crash:** Resolved circular dependency between Core and Recorder.
- **Persona Bug:** Fixed case-sensitivity issue causing AI to default to "D

## [0.9.8] - 2026-01-25
### Added
- **Tactical Dashboard (Phase 3):** Real-time WebSocket map (`web/server.py`) using Flask & Leaflet.js.
- **Recursive Parsing:** "Nuclear Option" JSON extractor to handle nested Autel/DroneTag telemetry.
- **Icon Classification:** Added visual distinction for Controllers (Cyan), Drones (Orange), Phones (Blue), and Hostiles (Red).
- **Dark Mode:** Tactical CSS theme for the frontend map.

### Fixed
- **Autel Driver:** Resolved issue where `data.data` nesting caused GPS packets to be dropped.
- **Controller Detection:** Fixed logic to identify Smart Controllers (`TH78...`) vs UAVs (`1748...`).
- **Null Island:** Added filtering to ignore coordinates at (0.0, 0.0).

## [0.9.4] - 2026-01-24
### Security & Stability
- **Dependency Lock:** Frozen `requirements.txt` with `paho-mqtt>=2.0.0` to prevent API version crashes.
- **AI Hallucinations:** Updated `officer.py` System Prompt to prevent "Negative Hallucinations" (claiming "No humans" when blind).
- **Hue Driver:** Hardened `hue.py` with retry logic to prevent crashes during network blips.

## [0.9.0] - 2026-01-24
### Added
- **Modular Core:** Replaced monolithic `ai_officer_v47.py` with `securingskies/core/officer.py`.
- **Drivers:** Hardware Abstraction Layer for Autel V3 (`drivers/autel.py`), Remote ID (`drivers/dronetag.py`), and OwnTracks (`drivers/owntracks.py`).
- **Outputs:** Dedicated modules for `hue` (lighting) and `recorder` (JSONL logging).
- **Scientific Metrics:** Added `auditor.py` for calculating LLM Hallucination/Recall rates.
- **GeoSpatial Math:** Added `utils/geo.py` for 3D Haversine separation vectors.
- **Forensic Replay:** Added `labs/replay/replay_tool.py` for simulating missions from log files.
- **Documentation:** Comprehensive `README.md` with architectural diagrams and citation standards.

### Changed
- **CLI:** `main.py` now uses a standardized `argparse` structure with rich help menus.
- **Logging:** All logs now persist to `logs/mission_*.jsonl` by default when enabled.
