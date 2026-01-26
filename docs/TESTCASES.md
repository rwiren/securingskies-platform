# 🧪 SecuringSkies Validation Protocols
**Protocol:** SSTP v1.0
**Traceability:** Maps to `TEST_PLAN.md` (ToL/DoL IDs).

## 🛡️ TIER 1: Unit Logic (Stability & Hygiene)
*Focus: "The Poison Pill" - Does the code survive bad data?*

### 🟢 TC-07: "Null GPS Resilience"
**Ref:** `ToL-99` | **Criticality:** HIGH
- [x] **Test:** Inject JSON packet: `{"data": {"latitude": null, "longitude": null}}`.
- [x] **Pass:** System defaults distance to `0m` or maintains last known. **NO CRASH.**
- [x] **Evidence:** Log `mission_20260126_214512.jsonl` shows continuous operation post-injection.

### 🔴 TC-09: "Speed Normalization"
**Ref:** `ToL-03`
**Objective:** Verify Physics Engine inputs.
- [ ] **Test:** Inject OwnTracks packet with `vel: 100` (km/h).
- [ ] **Pass:** AI receives `H-SPD: 27.7 m/s` and reports "MOVING".

---

## 🛡️ TIER 2: Semantic Integrity (AI Reasoning)
*Focus: "The Brain Check" - Does the AI understand what it sees?*

### 🔴 TC-08: "The Ghost Buster" (Aggregation)
**Ref:** `ToL-01`
**Objective:** Prevent "Split Brain" (Ghost Assets) on Autel startup.
- [ ] **Test:** Stream Autel Controller packets (no `tid`) followed by Drone packets.
- [ ] **Pass:** System aggregates them into single `AUTEL_UAV` asset. No "Asset UNK".

### 🟢 TC-05: "Anti-Hallucination"
**Ref:** `ToL-05`
**Objective:** Verify negative constraints.
- [ ] **Test:** Provide telemetry with `visual_contact: null`.
- [ ] **Pass:** AI explicitly states: *"Sensors Blind. No visual confirmation."*

---

## 🛡️ TIER 3: Field Validation (Physics & Latency)
*Focus: "The Thesis" - Hardware-in-the-Loop Science.*

### 🔵 TC-100: "The Latency Run"
**Ref:** `DoL-100` | **Hardware:** Autel Evo 4T MAX V2 + Dronetag Mini
**Objective:** Compare $L_{net}$ (LTE) vs $L_{c2}$ (RF).
- [ ] **Action:** Drive/Fly for 15 minutes in mixed 4G coverage.
- [ ] **Metric:** Record `link_latency` average vs `c2_latency` average.

### 🔵 TC-101: "The Twin-Sensor" (Calibration)
**Ref:** `DoL-101`
**Objective:** Measure Timestamp Jitter.
- [ ] **Setup:** Mount Dronetag Mini physically onto Autel Evo 4T.
- [ ] **Action:** Perform "Box Pattern" flight.
- [ ] **Pass:** Position delta between sensors < 5 meters (GNSS accuracy limit).

---

## 🛡️ TIER 4: Multi-Domain Fusion (Strategic)
*Focus: "The Vision" - Cross-Domain Correlation.*

### 🟣 TC-1000: "ADS-B Ingestion"
**Ref:** `ToL-04`
- [ ] **Test:** Stream `dump1090` JSON.
- [ ] **Pass:** Commercial flight appears as distinct icon type.

---

## 📋 Pre-Flight Checklist (The "Go/No-Go")
*Must be completed before any Field Operation (Tier 3).*

1. [ ] **Network:** MQTT Broker running (`docker ps` shows mosquitto).
2. [ ] **Intelligence:** Ollama running (`ollama ps` shows model loaded).
3. [ ] **Telemetry:** Autel Smart Controller connected to Hotspot.
4. [ ] **Safety:** Recorder Active (`--record` flag verified).
5. [ ] **Audio:** Voice Synthesis check (`say -v ?`).
