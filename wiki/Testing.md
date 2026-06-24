# 🧪 Testing & Validation
[**Home**](Home) > **Research & Operations** > **Testing**

**Protocol:** SSTP v1.0  
**Standard:** Compliant with IEEE 829  
**Traceability:** Each case maps to a ToL (Test of Logic) or DoL (Demonstration of Logic) ID.

---

## Pre-Flight Checklist (The "Go/No-Go")

*Must be completed before any Field Operation (Tier 3).*

1. [ ] **Network:** MQTT Broker running (`docker ps` shows mosquitto on port 1883).
2. [ ] **Intelligence:** Ollama running (`ollama ps` shows model loaded).
3. [ ] **Telemetry:** Autel Smart Controller connected to hotspot.
4. [ ] **Safety:** Recorder active (`--record` flag verified in CLI).
5. [ ] **Audio:** Voice synthesis check (`say -v ?` lists available voices).

---

## Tier 1 — Unit Logic (Stability & Hygiene)

*Focus: "The Poison Pill" — Does the code survive bad data?*

### TC-07: "Null GPS Resilience" `ToL-99` | HIGH
- [x] **Test:** Inject JSON packet `{"data": {"latitude": null, "longitude": null}}`.
- [x] **Pass:** System defaults distance to `0 m` or maintains last known. **NO CRASH.**
- [x] **Evidence:** `mission_20260126_214512.jsonl` — continuous operation post-injection.

### TC-09: "Speed Normalization" `ToL-03`
- [x] **Test:** Inject OwnTracks packet with `vel: 100` (km/h).
- [x] **Pass:** AI receives `H-SPD: 27.7 m/s` and reports "MOVING".

---

## Tier 2 — Semantic Integrity (AI Reasoning)

*Focus: "The Brain Check" — Does the AI understand what it sees?*

### TC-08: "The Ghost Buster" (Aggregation) `ToL-01`
- [x] **Test:** Stream Autel Controller packets (GCS) without Drone packets.
- [x] **Pass:** Pilot AI reports "No UAVs active" despite GCS telemetry present.
- [x] **Evidence:** Verified in `metrics_20260127_214842.csv`.

### TC-AI-01: "Persona Distinctiveness" `DoL-102`
- [x] **Test:** Replay `mission_20260127_172522.jsonl` against all 3 personas.
- [x] **Pass:**
  - Pilot Avg Word Count < 25.
  - Analyst Avg Word Count > 40.
  - Factuality Score = 100% for all.
- [x] **Evidence:** [OPS-002 performance table](AI-Optimization#4-performance-standards-passfail).

### TC-05: "Anti-Hallucination" `ToL-05`
- [ ] **Test:** Provide telemetry with `visual_contact: null`.
- [ ] **Pass:** AI explicitly states: *"Sensors Blind. No visual confirmation."*

---

## Tier 3 — Field Validation (Physics & Latency)

*Focus: "The Thesis" — Hardware-in-the-Loop science.*

### TC-100: "The Latency Run" `DoL-100`
**Hardware:** Autel Evo 4T MAX V2 + Dronetag Mini

- [x] **Action:** Drive/Fly for 15 minutes in mixed 4G coverage.
- [x] **Metric:** Record `link_latency` average vs `c2_latency` average.
- [x] **Result:** Validated. MQTT latency spikes to 15 s handled gracefully by Commander buffering.

### TC-101: "The Twin-Sensor Calibration" `DoL-101`

- [x] **Setup:** Mount Dronetag Mini physically onto Autel Evo 4T.
- [x] **Action:** Perform "Box Pattern" flight (Jorvas Flight).
- [x] **Pass:** Position delta between sensors < 5 m (GNSS accuracy limit).
- [x] **Evidence:** `analysis_172522.png` — correlation between Autel RTK and Dronetag GPS confirmed.
  Mean drift confirmed at **1.94 m** (hardware) vs **12.16 m** (network, as expected).

---

## Tier 4 — Multi-Domain Fusion (Strategic)

*Focus: "The Vision" — Cross-Domain Correlation.*

### TC-1000: "ADS-B Ingestion" `ToL-04`
- [ ] **Test:** Stream `dump1090` JSON.
- [ ] **Pass:** Commercial flight appears as a distinct icon type.

---

## Results Summary

| Test | Tier | Status | Notes |
| :--- | :--- | :--- | :--- |
| TC-07 Null GPS | Unit | ✅ Pass | Validated in `mission_20260126_214512.jsonl` |
| TC-09 Speed Norm | Unit | ✅ Pass | OwnTracks `vel` → `m/s` conversion verified |
| TC-08 Ghost Buster | Semantic | ✅ Pass | Anti-GCS hallucination confirmed |
| TC-AI-01 Personas | Semantic | ✅ Pass | Pilot <25 words, Analyst >40 words |
| TC-05 Anti-Hallucination | Semantic | ⬜ Pending | Awaiting automated replay harness |
| TC-100 Latency Run | Field | ✅ Pass | 1.2 s Glass-to-Glass confirmed |
| TC-101 Twin-Sensor | Field | ✅ Pass | 1.94 m hardware drift validated |
| TC-1000 ADS-B | Fusion | ⬜ Pending | Planned for v2.0 |
