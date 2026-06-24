# 🗺️ Roadmap
[**Home**](Home) > **Roadmap**

This page consolidates all completed milestones and planned future domains for the
SecuringSkies Platform.

---

## ✅ Completed — v0.x (Foundations)

| Release | Date | Theme |
| :--- | :--- | :--- |
| v0.9.0 | Jan 24, 2026 | Modular refactor — `officer.py` Micro-Kernel, output modules |
| v0.9.4 | Jan 24, 2026 | Dependency lock, hallucination prevention, Hue retry hardening |
| v0.9.9 | Jan 25, 2026 | **"Sibbo Gauntlet"** — first end-to-end field validation |
| v0.9.9 RC | Jan 25, 2026 | Pre-release stabilization, Black Box logging |

---

## ✅ Completed — v1.x (Stability & Science)

| Release | Date | Theme |
| :--- | :--- | :--- |
| **v1.0.0** | Jan 26, 2026 | **Stable Release** — SSTP v1.0 protocol; KPI dashboards |
| **v1.2.3** | Jan 27, 2026 | **DSPy Optimization** — Golden Datasets; 82% verbosity reduction |
| **v1.2.7** | Feb 3, 2026 | **3D Visualization** — CesiumJS Unified Dashboard; CZML export |

### v1.0 Phase Validation (SSTP)
- ✅ **TC-08** — Semantic Logic ("Ghost Buster") validated
- ✅ **TC-07** — Null GPS Resilience ("Poison Pill") validated
- ✅ **TC-100 / TC-101** — Latency KPIs and Twin-Sensor Calibration validated

---

## 🔭 Planned — Domain 1: Cyber-Electronic Defense (v1.x)

> **Objective:** Correlate physical telemetry with network signatures to detect spoofing,
> jamming, and C2 hijacking.

| Feature | Description | Technology |
| :--- | :--- | :--- |
| **SIEM Integration** | Ingest logs from OpenSearch and Syslog to detect anomalies in GCS network traffic. | OpenSearch, Syslog |
| **Packet Forensics** | Deep packet inspection of MAVLink/C2 streams. | Arkime |
| **Threat Correlation** | AI correlation of "GPS Jumps" with "Network Latency Spikes" to identify non-kinetic attacks. | LLM + Physics Engine |

---

## 🔭 Planned — Domain 2: Total Airspace Fusion (v2.0)

> **Objective:** Merge Low-Altitude UAS with High-Altitude Manned Aviation for a complete
> Common Operating Picture (COP).

| Feature | Description | Technology |
| :--- | :--- | :--- |
| **ADS-B Fusion** | Integrate 1090 MHz Mode-S data from the ADS-B Research Grid. | `dump1090`, adsb-research-grid |
| **Conflict Prediction** | AI analysis of convergence vectors between Drones and General Aviation. | LLM + Haversine Engine |
| **Swarm Logic** | Multi-Drone deconfliction algorithms. | Phase 4 Research |
| **Edge Intelligence** | Raspberry Pi 5 + Hailo-10H deployment profiles ("Scout" / "Sentinel"). | RPi 5, AI HAT+ 2 |

---

## Test Coverage Target

| Domain | Test Cases | Current Status |
| :--- | :--- | :--- |
| Unit Logic (Tier 1) | TC-07, TC-09 | ✅ Complete |
| Semantic Integrity (Tier 2) | TC-08, TC-AI-01, TC-05 | ✅ / ⬜ Partial |
| Field Validation (Tier 3) | TC-100, TC-101 | ✅ Complete |
| Multi-Domain Fusion (Tier 4) | TC-1000 | ⬜ Planned for v2.0 |

See [Testing & Validation](Testing) for full test case details.

---

## 🤝 Contributing to the Roadmap

Pull requests are welcome for:
- MAVLink integration improvements
- Cyber-Defense SIEM modules
- DSPy prompt optimization and new personas
- ADS-B data connectors

See the repository [CONTRIBUTING](https://github.com/rwiren/securingskies-platform/blob/main/README.md#-how-to-contribute)
section for workflow guidelines.
