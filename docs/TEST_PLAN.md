# 🛡️ SecuringSkies Test Protocol (SSTP)
**Version:** 1.0.0
**Status:** ACTIVE

## 1. ToL (Test Object List) - The Components
*Atomic verification of individual drivers and modules.*

| ID | Object | Type | Verification Criteria | Current Status |
| :--- | :--- | :--- | :--- | :--- |
| **ToL-01** | `drivers.autel` | Driver | Must parse `data.data` JSON and separate `UAV` (Orange) from `CTRL` (Cyan). | ✅ v0.9.8 |
| **ToL-02** | `drivers.dronetag` | Driver | Must identify `RID` packets and extract GPS regardless of nesting. | ✅ v0.9.8 |
| **ToL-03** | `drivers.owntracks` | Driver | Must accept HTTP/MQTT JSON from Android/iOS. | ⚠️ v0.9.0 (Needs Retest) |
| **ToL-04** | `drivers.mavlink` | Driver | Must connect to ArduPilot/PX4 via UDP. | ❌ PENDING (Planned) |
| **ToL-05** | `core.officer` | AI | Must output SITREP without "Negative Hallucinations" (blindness). | ✅ v0.9.4 |
| **ToL-06** | `core.optimizer` | DSPy | Must auto-correct system prompts based on Auditor feedback. | ❌ PENDING (Legacy Port) |
| **ToL-07** | `outputs.hue` | HW | Must trigger RED light on Hostile, CYAN on Pilot, BLUE on Guard. | ⚠️ Needs HW Test |
| **ToL-08** | `web.server` | UI | Must visualize all assets on Dark Mode Map via WebSocket. | ✅ v0.9.8 |

## 2. DoL (Demo Object List) - The Missions
*Integrated scenarios that prove business value to stakeholders.*

| ID | Scenario Name | Actors | Description |
| :--- | :--- | :--- | :--- |
| **DoL-A** | "The Ghost Walk" | OwnTracks, Officer | Replay of `mission_20260124`. Verifies Ground Asset tracking and Voice reporting. |
| **DoL-B** | "The Airspace Breach" | RID, Hue, Officer | Simulated Hostile DroneTag. Verifies "RED ALERT" logic and AI detection. |
| **DoL-C** | "The Full Grid" | Autel, RID, Phone | Replay of `mission_20260123`. Verifies multi-vendor fusion on the Tactical Map. |

## 3. Testing Strategy
* **Regression:** Run `tests/regression/` before every merge to `main`.
* **Stability:** Long-duration run (24h) to check for memory leaks in `officer.py`.
* **Performance:** Check `metrics_*.csv` to ensure AI Latency < 5s.
