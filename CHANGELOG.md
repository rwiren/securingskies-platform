# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.7] - 2026-02-03
**Status:** STABLE (Unified Visualization)
**Focus:** 3D Geospatial Integration, macOS Stability, and Post-Mission Forensics.

### Added
- **Visualization:** Implemented **Unified Commander** (`web/templates/unified_map.html`), a hybrid dashboard allowing one-click toggling between 2D Tactical (Leaflet) and 3D Globe (CesiumJS) views.
- **Forensics:** Added `labs/jsonl_to_czml.py` to convert raw JSONL flight logs into **CZML** format, enabling cinematic 3D replay of missions in Cesium Stories.
- **Reliability:** Introduced "Safe Mode" 3D rendering that defaults to OpenStreetMap imagery if Cesium Ion tokens fail, preventing "Black Screen" crashes.
- **Artifacts:** Generated `labs/mission_replay.czml` from the "Jorvas Test" (Mission 20260203), proving data integrity for Autel and OwnTracks assets.

### Changed
- **Engine:** Switched `web/server.py` from `threading` to **`gevent`** to resolve critical WebSocket `AssertionError` crashes on macOS Silicon (M-series) chips.
- **Security:** Refactored `web/server.py` to inject Cesium Tokens securely via server-side variables, removing hardcoded credentials from client-side HTML.
- **Architecture:** Decoupled 3D map initialization from network connectivity; the HUD now reports "ONLINE" status even if the 3D globe fails to load (e.g., firewall issues).

### Fixed
- **Visuals:** Fixed "Blue Screen" overlay issue where the 3D container blocked the 2D map by enforcing strict CSS `display: none` toggling.
- **Data:** Resolved "Null Island" filtering issue where Autel drones were invisible during GPS lock acquisition phase.
- **Parsing:** Updated parsing logic in `web/server.py` to correctly identify Autel Smart Controllers (`TH*`) versus UAVs (`1748*`) and assign distinct icons.

## [1.2.3] - 2026-01-27
**Status:** VALIDATED (Production Ready)
**Focus:** AI Optimization, Scientific Validation, and Documentation.

### Added
- **Optimization:** Integrated **DSPy** (`labs/optimizer.py`) for automated prompt engineering, replacing brittle static system prompts.
- **Intelligence:** Implemented Role-Specific Grading Metrics to enforcing doctrine:
    - `validate_pilot`: Enforces extreme brevity (<20 words) and safety.
    - `validate_commander`: Rewards spatial logic and vector tracking.
    - `validate_analyst`: Rewards technical vocabulary (RTK, Latency, Delta).
- **Validation:** Added **Golden Datasets** (`golden_datasets/`) containing high-fidelity "Jorvas Flight" logs (`172522`) for regression testing.
- **Documentation:** Created **OPS-002** (`docs/AI_OPTIMIZATION.md`) detailing the "Three-Layer Validation" strategy (Hardware -> Network -> Cognitive).
- **Protocol:** Finalized `TEST_PLAN.md` and `TESTCASES.md` with successful pass rates for "Twin-Sensor Calibration" (TC-101) and "Latency Run" (TC-100).

### Fixed
- **Zombie Process:** Resolved issue where `main.py` replay loop failed to exit cleanly after log completion.
- **Analyst Silence:** Fixed optimizer bug where the Analyst failed to learn technical reporting patterns due to improper grading logic.
- **Pilot Noise:** Reduced Pilot verbosity by 82% (avg 19 words), eliminating operator distraction during nominal flight phases.

### Changed
- **CLI:** Enhanced `main.py` to support explicit `--persona` selection for targeted simulation replay.
- **Hygiene:** Standardized logging outputs to strictly separate `metrics_*.csv` (Scientific Data) from `mission_*.jsonl` (Audit Trail).

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
