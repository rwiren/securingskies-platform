# 🛡️ SecuringSkies Test Protocol (SSTP)
**Standard:** SSTP v1.0 (IEEE 829 Compliant)
**Status:** RELEASE CANDIDATE
**Badge:** [![Safety](https://img.shields.io/badge/Safety_Level-Critical-red?style=for-the-badge)](Test-Protocol)

> **Philosophy:** "Trust, but Verify." We use Hardware-in-the-Loop (HITL) to validate Multi-Domain Fusion in three concentric circles of trust: **Unit** (Code), **System** (Integration), and **Field** (Physics).

## 1. ToL (Test Object List) - Unit Level
*Atomic verification of individual logic modules. (ID Range: 00-99)*

| ID | Component | Verification Criteria | Tooling |
| :--- | :--- | :--- | :--- |
| **ToL-01** | `core.officer` | **Autel Logic:** Parse `data` JSON; separate `UAV` (Orange) from `CTRL` (Cyan). | `replay_tool.py` |
| **ToL-02** | `core.officer` | **Dronetag Logic:** Identify `RID` packets and extract GPS regardless of nesting. | MQTT Injector |
| **ToL-03** | `core.officer` | **OwnTracks Logic:** Normalize Speed (`km/h` $\to$ `m/s`). | iPhone App |
| **ToL-05** | `core.officer` | **Anti-Hallucination:** Report "Sensors Blind" when visual data is null. | `main.py --debug` |
| **ToL-07** | `outputs.hue` | **Alerts:** Trigger RED/ORANGE on Hostile, CYAN on Pilot. | Philips Hue Bridge |
| **ToL-99** | `ops.stack` | **Infrastructure:** Mosquitto, Ollama, and Recorder are active. | `docker ps` |

## 2. DoL (Demo Object List) - System & Field Level
*Integrated scenarios that prove operational and scientific capability.*

### 🟢 Phase 1: Operational Baseline (IDs 10-99)
| ID | Scenario Name | Actors | Description | Status |
| :--- | :--- | :--- | :--- | :--- |
| **DoL-10** | "The Ghost Walk" | OwnTracks, Officer | **Ground Truth.** Operator walks with phone. Verifies tracking accuracy. | ✅ **PASS** |
| **DoL-11** | "The Airspace Breach" | RID, Hue, Officer | **Hostile Simulation.** Inject unknown Serial. Verifies RED ALERT logic. | ✅ **PASS** |
| **DoL-12** | "The Full Grid" | Multi-Vendor | **Fusion.** Stream Autel + OwnTracks simultaneously. Verifies map/icon logic. | 🟡 Pending |

### 🔵 Phase 2: Thesis Field Science (IDs 100-999)
| ID | Scenario Name | Actors | Description | Status |
| :--- | :--- | :--- | :--- | :--- |
| **DoL-100** | "The Latency Run" | Dronetag, Autel | **Comparative Analysis.** LTE vs RF Latency ($L_{net}$ vs $L_{c2}$). | 🗓️ Scheduled |
| **DoL-101** | "The Twin-Sensor" | Autel 4T + Dronetag | **Calibration.** Dronetag Mini mounted on Autel Evo 4T. Measures drift. | 🗓️ Scheduled |

### 🟣 Phase 3: Strategic Expansion (IDs 1000+)
| ID | Scenario Name | Actors | Description | Status |
| :--- | :--- | :--- | :--- | :--- |
| **DoL-1000** | "The Airport Breach" | ADS-B, Remote ID | **Safety.** Drone altitude intersects Commercial Air Glide Path. | 🗓️ Future |
| **DoL-1001** | "The Locked Shield" | OpenSearch, AI | **Cyber.** SSH Brute Force triggers AI SITREP. | 🗓️ Future |

## 3. Hardware Setup (Thesis Validation)
To reproduce results, the following Reference Architecture is used:
1.  **Sensor A (RF):** Autel Smart Controller (Skylink 2.0).
2.  **Sensor B (LTE):** Dronetag Mini 4G (Network Remote ID).
3.  **Sensor C (ADS-B):** RTL-SDR (`dump1090` / `adsb-research-grid`).
4.  **Sensor D (Cyber):** OpenSearch (Syslogs).
