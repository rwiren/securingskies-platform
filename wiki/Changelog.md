# 📋 Changelog
[**Home**](Home) > **Changelog**

All notable changes to this project are documented here.  
Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) · Versioning: [Semantic Versioning](https://semver.org/).

---

## [1.2.7] — 2026-02-03
**Status:** STABLE (Unified Visualization)  
**Focus:** 3D Geospatial Integration, macOS Stability, and Post-Mission Forensics.

### Added
- **Visualization:** Implemented **Unified Commander** (`web/templates/unified_map.html`), a hybrid
  dashboard allowing one-click toggling between 2D Tactical (Leaflet) and 3D Globe (CesiumJS).
- **Forensics:** Added `labs/jsonl_to_czml.py` to convert raw JSONL flight logs into **CZML** format
  for cinematic 3D replay in Cesium Stories.
- **Reliability:** "Safe Mode" 3D rendering that defaults to OpenStreetMap if Cesium Ion tokens fail,
  preventing "Black Screen" crashes.
- **Artifacts:** Generated `labs/mission_replay.czml` from the "Jorvas Test" (Mission 20260203).

### Changed
- **Engine:** Switched `web/server.py` from `threading` to **`gevent`** to resolve critical WebSocket
  `AssertionError` crashes on macOS Silicon (M-series) chips.
- **Security:** Refactored `web/server.py` to inject Cesium Tokens via server-side variables,
  removing hardcoded credentials from client-side HTML.
- **Architecture:** Decoupled 3D map initialization from network connectivity.

### Fixed
- **Visuals:** Fixed "Blue Screen" overlay where the 3D container blocked the 2D map.
- **Data:** Resolved "Null Island" filtering — Autel drones invisible during GPS lock acquisition.
- **Parsing:** Updated parsing logic to correctly identify Autel Smart Controllers vs UAVs.

---

## [1.2.3] — 2026-01-27
**Status:** VALIDATED (Production Ready)  
**Focus:** AI Optimization, Scientific Validation, and Documentation.

### Added
- **Optimization:** Integrated **DSPy** (`labs/optimizer.py`) for automated prompt engineering.
- **Intelligence:** Role-Specific Grading Metrics (`validate_pilot`, `validate_commander`, `validate_analyst`).
- **Validation:** Golden Datasets (`golden_datasets/`) — high-fidelity "Jorvas Flight" logs for regression testing.
- **Documentation:** **OPS-002** (`docs/OPS-002_AI_OPTIMIZATION.md`) — "Three-Layer Validation" strategy.
- **Protocol:** Finalized `TEST_PLAN.md` and `TESTCASES.md`.

### Fixed
- **Zombie Process:** Replay loop failed to exit cleanly after log completion.
- **Analyst Silence:** Optimizer bug where Analyst failed to learn technical patterns.
- **Pilot Noise:** Reduced Pilot verbosity by 82% (avg 19 words).

---

## [1.0.0] — 2026-01-26
**Status:** RELEASE (Stable)

### Added
- **Architecture:** Implemented `officer.py` (Micro-Kernel) replacing legacy `drivers/` folder.
- **Protocol:** Adopted **SSTP v1.0** (SecuringSkies Test Protocol), IEEE 829 compliant.
- **KPIs:** Network Latency (Glass-to-Glass) and C2 Latency calculation in `auditor.py`.
- **Docs:** Added `docs/TECH_DEBT.md`.

### Changed
- Asset identification strictly separates "Ground Station (GCS)" from "UAV".
- System Prompt includes "Constitutional Guardrails" for anti-hallucination.
- OwnTracks velocity standardized from `km/h` to `m/s`.

### Fixed
- `TypeError` in `geo.py` when telemetry contains `lat: null` (TC-07).
- `NoneType` timestamp error in `labs/replay/replay_tool.py`.
- Repeating System Prompt spam in console output.

---

## [0.9.9 RC] — 2026-01-25
**Status:** PRE-RELEASE (Field Proven)

### Added
- Native support for Pixhawk/ArduPilot telemetry via `drivers/mavlink.py`.
- Real-time LeafletJS map server (`web/server.py`).
- `mission_*.jsonl` (Black Box) and `metrics_*.csv` (Performance) streams.

### Fixed
- "Ghost Assets" bug — Autel Controller and UAV merged correctly.
- Moving cars reported as "Stationary" due to unit mismatch (km/h vs m/s).

---

## [0.9.9] — 2026-01-25 (The "Sibbo Gauntlet" Release)
**Status:** FIELD PROVEN  
**Focus:** Field Validation, Hardware Integration, Driver Stabilization.

### Validated
- **Operation "Sibbo Gauntlet":** End-to-end AGCS validation in Vantaa/Sipoo.
- Simultaneous tracking of Ground (OwnTracks), Air (Autel), and Vision AI assets confirmed.
- Llama 3.1 (Pilot) and Gemma 2 (Commander) persona efficacy confirmed.

### Critical Field Hotfixes
- Null GPS Crash (`geo.py` TypeError) — fixed v0.9.9e.
- Ghost Assets — aggregation logic added to `officer.py` — fixed v0.9.9d.
- Speed Units — OwnTracks `km/h` → `m/s` conversion — fixed v0.9.9f.

---

## [0.9.4] — 2026-01-24

- Dependency lock: `paho-mqtt>=2.0.0` to prevent API version crashes.
- AI Hallucination prevention for "No humans" negative assertions.
- Hue driver hardened with retry logic.

---

## [0.9.0] — 2026-01-24

- **Modular Core:** Replaced monolithic `ai_officer_v47.py` with `securingskies/core/officer.py`.
- Hardware Abstraction Layer for Autel V3, Remote ID, and OwnTracks.
- Dedicated output modules: `hue`, `recorder`, `auditor`.
- `utils/geo.py` — 3D Haversine separation vectors.
- Forensic Replay: `labs/replay/replay_tool.py`.
