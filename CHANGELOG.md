# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.9.9] - 2026-01-25 (The "Long Test Drive" Release)
**Status:** RELEASE CANDIDATE
**Focus:** Hardware Integration, Model Diversity, and Stability.

### 🚀 Added
- **MAVLink Bridge:** Native support for Pixhawk/ArduPilot telemetry via `drivers/mavlink.py`.
- **Web Dashboard:** Real-time LeafletJS map server (`web/server.py`) for visual tracking.
- **Simulator:** `sim_px4.py` for generating synthetic drone traffic over Vantaa.
- **Model Support:** Verified support for `gemma2` (Tactical), `phi3.5` (Speed), and `gpt-4o` (Cloud).
- **Metric Engine:** Scientific logging of Latency, Recall, and Hallucination rates (`outputs/auditor.py`).
- **Test Protocols:** Added `docs/TESTCASES.md` and `docs/TEST_PLAN.md`.

### ⚡ Improved
- **GPS Logic:** strict thresholds (<1m = RTK, >5m = Poor) to prevent AI overconfidence.
- **CLI:** Restored full help documentation and scientific standards text in `main.py`.
- **Logging:** Silenced `LiteLLM` and `HTTPX` console noise for a cleaner tactical display.
- **Architecture:** Decoupled `officer.py` from drivers to allow "Fail-Loud" debugging.

### 🐛 Fixed
- **Hallucinations:** Fixed logic where AI would invent visual contacts when sensor data was missing.
- **Import Crash:** Resolved circular dependency between Core and Recorder.
- **Persona Bug:** Fixed case-sensitivity issue causing AI to default to "Data Analyst".

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
