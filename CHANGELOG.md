# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

### Migrated
- Full logic port from Legacy `ai_officer_v47.py`.
