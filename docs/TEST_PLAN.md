# 🛡️ SecuringSkies Test Protocol (SSTP)
**Version:** v0.9.9f (Field Proven)
**Date:** 2026-01-25
**Status:** PARTIALLY VALIDATED (Autel/Ground Complete, Dronetag and MAVlink field testing pending)

## 1. ToL (Test Object List) - The Components
*Atomic verification of individual drivers and modules.*

| ID | Object | Type | Verification Criteria | Current Status |
| :--- | :--- | :--- | :--- | :--- |
| **ToL-01** | `drivers.autel` | Driver | Must parse `data.data` JSON and separate `UAV` (Orange) from `CTRL` (Cyan). | ✅ **Validated** (Run 5-7) |
| **ToL-02** | `drivers.dronetag` | Driver | Must identify `RID` packets and extract GPS regardless of nesting. | ✅ **Stable** |
| **ToL-03** | `drivers.owntracks` | Driver | Must accept HTTP/MQTT JSON and **normalize Speed (m/s)**. | ✅ **Validated** (Run 15-17) |
| **ToL-04** | `drivers.mavlink` | Driver | Must connect to ArduPilot/PX4 via UDP. | ✅ **Active** |
| **ToL-05** | `core.officer` | AI | Must output SITREP without "Negative Hallucinations" (blindness). | ✅ **Validated** (0 Hallucinations) |
| **ToL-06** | `core.optimizer` | DSPy | Must auto-correct system prompts based on Auditor feedback. | ⏳ **Data Collected** (Ready for Lab) |
| **ToL-07** | `outputs.hue` | HW | Must trigger RED/ORANGE on Hostile, CYAN on Pilot, BLUE on Guard. | ✅ **Validated** (Traffic Alert) |
| **ToL-08** | `web.server` | UI | Must visualize all assets on Dark Mode Map via WebSocket. | ✅ **Validated** |

## 2. DoL (Demo Object List) - The Missions
*Integrated scenarios that prove business value to stakeholders.*

| ID | Scenario Name | Actors | Description | Status |
| :--- | :--- | :--- | :--- | :--- |
| **DoL-A** | "The Ghost Walk" | OwnTracks, Officer | Ground Asset tracking. Verifies Voice reporting. | ✅ **PASS** |
| **DoL-B** | "The Airspace Breach" | RID, Hue, Officer | Simulated Hostile. Verifies "RED ALERT" logic. | ✅ **PASS** |
| **DoL-C** | "The Sibbo Drive" | OwnTracks, Llama 3.1 | **Highway Telemetry.** Verifies GPS tracking at >100km/h. | ✅ **PASS** (Run 16) |
| **DoL-D** | "The Trinity" | Autel, Llama 3.1 | **Persona Validation.** Pilot vs Commander vs Analyst. | ✅ **PASS** (Run 8-10) |
| **DoL-E** | "Ghost Wall Stress" | Gemma 2, Autel | **High Load Vision.** 8+ Objects. Verifies CPU stability. | ⚠️ **Recovered** (Run 11) |
| **DoL-F** | "Night Owl (IFR)" | Gemma 2, Thermal | **Instrument Flight.** Verifies V-SPD/H-SPD without visual. | ✅ **PASS** (Run 14) |

## 3. Architecture Change Log (Field Hotfixes)
* **v0.9.9d:** Added `process_traffic` aggregation to fix "Asset UNK".
* **v0.9.9e:** Added `NoneType` safety check in `geo.py` to fix crash.
* **v0.9.9f:** Added `km/h -> m/s` conversion for OwnTracks.


# 🛡️ SecuringSkies Test Protocol (SSTP)
**Version:** v1.1.0 (Strategic Roadmap)
**Date:** 2026-01-26
**Status:** RELEASE CANDIDATE

## 1. ToL (Test Object List) - The Components

| ID | Object | Type | Verification Criteria | Status |
| :--- | :--- | :--- | :--- | :--- |
| **ToL-01** | `core.officer` | Logic | **Semantic Labeling:** Distinguish GCS vs UAV. | 🟡 Pending TC-08 |
| **ToL-02** | `core.officer` | KPI | **Dronetag Latency:** Glass-to-Glass calc. | 🟡 Field Test |
| **ToL-03** | `core.officer` | KPI | **Autel Latency:** C2 Link calc. | ✅ Validated |
| **ToL-04** | `drivers.adsb` | Future | **Civil Air:** Ingest SBS-1/JSON from `dump1090`. | 🗓️ Strategic |
| **ToL-05** | `drivers.cyber` | Future | **SIEM:** Ingest OpenSearch hits as "Contacts". | 🗓️ Strategic |

## 2. DoL (Demo Object List) - The Missions

| ID | Scenario Name | Actors | Description | Status |
| :--- | :--- | :--- | :--- | :--- |
| **DoL-A** | "The Latency Run" | Dronetag, Autel | **Thesis Core.** Comparative latency analysis. | 🗓️ This Week |
| **DoL-B** | "The Twin-Sensor" | Autel + Dronetag | **Calibration.** Physical mounting of sensors. | 🗓️ This Week |
| **DoL-C** | "The Glide Path" | ADS-B, Autel | **Safety.** Drone intersects airliner approach. | 🗓️ Q2 2026 |
| **DoL-D** | "The Locked Shield" | OpenSearch, Officer | **Cyber.** SSH Brute Force triggers SITREP. | 🗓️ Q2 2026 |
