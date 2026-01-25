# 🛡️ SecuringSkies Test Protocol (SSTP)
**Version:** v0.9.9
**Status:** ACTIVE (Sibbo Field Test Ready)

## 1. ToL (Test Object List) - The Components
*Atomic verification of individual drivers and modules.*

| ID | Object | Type | Verification Criteria | Current Status |
| :--- | :--- | :--- | :--- | :--- |
| **ToL-01** | `drivers.autel` | Driver | Must parse `data.data` JSON and separate `UAV` (Orange) from `CTRL` (Cyan). | ✅ v0.9.8 |
| **ToL-02** | `drivers.dronetag` | Driver | Must identify `RID` packets and extract GPS regardless of nesting. | ✅ v0.9.8 |
| **ToL-03** | `drivers.owntracks` | Driver | Must accept HTTP/MQTT JSON from Android/iOS. | ✅ v0.9.9 (Sibbo Ready) |
| **ToL-04** | `drivers.mavlink` | Driver | Must connect to ArduPilot/PX4 via UDP. | ✅ v0.9.9 (Active) |
| **ToL-05** | `core.officer` | AI | Must output SITREP without "Negative Hallucinations" (blindness). | ✅ v0.9.9 (Logic Fixed) |
| **ToL-06** | `core.optimizer` | DSPy | Must auto-correct system prompts based on Auditor feedback. | ⚠️ Deferred (v1.1) |
| **ToL-07** | `outputs.hue` | HW | Must trigger RED/ORANGE on Hostile, CYAN on Pilot, BLUE on Guard. | ✅ v0.9.9 (API Synced) |
| **ToL-08** | `web.server` | UI | Must visualize all assets on Dark Mode Map via WebSocket. | ✅ v0.9.9 |

## 2. DoL (Demo Object List) - The Missions
*Integrated scenarios that prove business value to stakeholders.*

| ID | Scenario Name | Actors | Description |
| :--- | :--- | :--- | :--- |
| **DoL-A** | "The Ghost Walk" | OwnTracks, Officer | Replay of `mission_20260124`. Verifies Ground Asset tracking and Voice reporting. |
| **DoL-B** | "The Airspace Breach" | RID, Hue, Officer | Simulated Hostile DroneTag. Verifies "RED ALERT" logic and AI detection. |
| **DoL-C** | "The Full Grid" | Autel, RID, Phone | Replay of `mission_20260123`. Verifies multi-vendor fusion on the Tactical Map. |
| **DoL-D** | "The Sibbo Drive" | OwnTracks, Llama3.1 | Real-world road test (30km). Verifies Latency and GPS Logic under motion. |

## 3. Testing Strategy
* **Regression:** Run `python3 main.py --metrics` to ensure Hallucination Rate == 0.
* **Stability:** Long-duration run (30m+) to check for memory leaks in `officer.py`.
* **Performance:** Check `metrics_*.csv` to ensure AI Latency < 5s (Llama 3.1) or < 2s (GPT-4o).
