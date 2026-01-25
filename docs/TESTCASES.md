# 🧪 SecuringSkies v0.9.9 - Validation Protocols
**Status:** POST-MORTEM (Field Validated)
**Date:** 2026-01-25

## 🟢 TC-01: "The Silence Check" (Logging Hygiene)
**Objective:** Verify `litellm` and `httpx` noise is suppressed.
- [x] **Action:** Run `python3 securingskies/main.py --debug`
- [x] **Check:** Console does NOT show `INFO:LiteLLM` or HTTP POST requests.
- [x] **Check:** Console DOES show `🦅 GhostCommander Initialized`.

## 🟢 TC-02: "Identity Verification" (Persona Logic)
**Objective:** Ensure CLI flags correctly switch AI engagement rules.
- [x] **Action A:** Run with `--persona pilot` -> Output is telegraphic.
- [x] **Action B:** Run with `--persona commander` -> Output gives orders/outlook.
- [x] **Action C:** Run with `--persona analyst` -> Output provides forensic reasoning.

## 🟢 TC-03: "The Blind Test" (Hallucination Auditor)
**Objective:** Verify the AI does not invent visual contacts when sensors are blind.
- [x] **Action:** Inject telemetry with `visual: null` or no visual field.
- [x] **Check:** AI Output says "Sensors Blind" or "No Visuals".
- [x] **Check:** Metrics Log (`logs/metrics_*.csv`) shows `Hallucination_Visual: 0`.

## 🟢 TC-04: "Black Box Persistence" (Recording)
**Objective:** Ensure mission data is saved to disk.
- [x] **Action:** Run `python3 securingskies/main.py --record`.
- [x] **Check:** `logs/mission_YYYYMMDD_*.jsonl` exists and is growing (55MB confirmed).

## 🟢 TC-05: "The Loop" (MAVLink Integration)
**Objective:** Verify ArduPilot/Pixhawk connectivity.
- [x] **Action:** Start Bridge -> Check Heartbeat.

## 🟢 TC-06: "Hardware Stress" (Gemma 2 Inference)
**Objective:** Verify M4 Max VRAM usage and Latency.
- [x] **Action:** Run `Gemma 2` with Interval 30s.
- [x] **Check:** Latency stays under 6s. (Actual: ~4.8s).

---

## 🛡️ NEW REGRESSION TESTS (Post-Sibbo)

## 🔴 TC-07: "Null GPS Resilience" (The Crash Fix)
**Objective:** Prevent crash when Drone sends `lat: null` during initialization.
- [ ] **Action:** Inject JSON packet: `{"data": {"latitude": null, "longitude": null}}`.
- [ ] **Check:** System does **NOT** crash with `TypeError`.
- [ ] **Check:** Distance defaults to `0m` or maintains last known position.

## 🔴 TC-08: "The Ghost Buster" (Asset Aggregation)
**Objective:** Prevent "Asset UNK" when Controller and Drone data arrive separately.
- [ ] **Action:** Stream Autel Controller packets (no `tid`) followed by Drone packets.
- [ ] **Check:** System aggregates them into single `AUTEL_UAV` asset.
- [ ] **Check:** No `Asset: UNK` appears in SITREP.

## 🔴 TC-09: "Speed Unit Normalization" (The Stationary Car Fix)
**Objective:** Ensure OwnTracks `vel` (km/h) is converted to AI `speed` (m/s).
- [ ] **Action:** Inject OwnTracks packet with `vel: 100`.
- [ ] **Check:** AI prompts receives `H-SPD: 27.7 m/s`.
- [ ] **Check:** AI reports "MOVING" (not "STATIONARY").

**Status note :** PARTIALLY VALIDATED (Autel/Ground Complete, Fleet Pending)
