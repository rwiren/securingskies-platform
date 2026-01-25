# 🧪 SecuringSkies v0.9.9 - Validation Protocols
**Status:** RELEASE CANDIDATE
**Date:** 2026-01-25

## 🟢 TC-01: "The Silence Check" (Logging Hygiene)
**Objective:** Verify `litellm` and `httpx` noise is suppressed.
- [ ] **Action:** Run `python3 securingskies/main.py --debug`
- [ ] **Check:** Console does NOT show `INFO:LiteLLM` or HTTP POST requests.
- [ ] **Check:** Console DOES show `🦅 GhostCommander Initialized`.

## 🟢 TC-02: "Identity Verification" (Persona Logic)
**Objective:** Ensure CLI flags correctly switch AI engagement rules.
- [ ] **Action A:** Run with `--persona pilot`
    - **Expect:** System Prompt contains "Tactical Officer (PILOT)".
    - **Expect:** Output is telegraphic (e.g., "SITREP: Asset RW active...").
- [ ] **Action B:** Run with `--persona commander`
    - **Expect:** System Prompt contains "Incident Commander".
    - **Expect:** Output gives orders (e.g., "RECOMMENDATION: Monitor signal...").

## 🟢 TC-03: "The Blind Test" (Hallucination Auditor)
**Objective:** Verify the AI does not invent visual contacts when sensors are blind.
- [ ] **Action:** Inject telemetry with `visual: null` or no visual field.
- [ ] **Check:** AI Output says "Sensors Blind" or "No Visuals".
- [ ] **Check:** Metrics Log (`logs/metrics_*.csv`) shows `Hallucination_Visual: 0`.
- [ ] **Fail Condition:** If AI says "Visual contact confirmed" on empty data -> **FAIL**.

## 🟢 TC-04: "Black Box Persistence" (Recording)
**Objective:** Ensure mission data is saved to disk.
- [ ] **Action:** Run `python3 securingskies/main.py --record` for 60 seconds.
- [ ] **Check:** `logs/mission_YYYYMMDD_*.jsonl` exists and is growing.
- [ ] **Check:** `logs/metrics_YYYYMMDD_*.csv` exists and has headers.

## 🟢 TC-05: "The Loop" (MAVLink Integration)
**Objective:** Verify ArduPilot/Pixhawk connectivity.
- [ ] **Action 1:** Start Dashboard: `python3 web/server.py`
- [ ] **Action 2:** Start Bridge: `python3 securingskies/drivers/mavlink.py`
- [ ] **Action 3:** Start Sim: `python3 labs/sim_px4.py`
- [ ] **Check:** Dashboard Map shows **Orange Helicopter** icon moving.
- [ ] **Check:** Bridge console shows `✅ HEARTBEAT RECEIVED`.

## 🟢 TC-06: "Hardware Stress" (Gemma 2 Inference)
**Objective:** Verify M4 Max VRAM usage and Latency.
- [ ] **Action:** Run with `--model gemma2 --metrics`
- [ ] **Check:** Latency stays under **5.0s** (Warm).
- [ ] **Check:** No Python memory crashes (OOM).

---
*Execution Log:*
- [ ] TC-01: PASS
- [ ] TC-02: PASS
- [ ] TC-03: PASS
- [ ] TC-04: PASS
- [ ] TC-05: PASS
- [ ] TC-06: PASS
