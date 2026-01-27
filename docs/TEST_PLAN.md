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
- [x] **Test:** Inject OwnTracks packet with `vel: 100` (km/h).
- [x] **Pass:** AI receives `H-SPD: 27.7 m/s` and reports "MOVING".

---

## 🛡️ TIER 2: Semantic Integrity (AI Reasoning)
*Focus: "The Brain Check" - Does the AI understand what it sees?*

### 🔴 TC-08: "The Ghost Buster" (Aggregation)
**Ref:** `ToL-01`
**Objective:** Prevent "Split Brain" (Ghost Assets) on Autel startup.
- [x] **Test:** Stream Autel Controller packets (GCS) without Drone packets.
- [x] **Pass:** Pilot AI reports "No UAVs active" despite GCS telemetry being present.
- [x] **Evidence:** Verified in `metrics_20260127_214842.csv`.

### 🟣 TC-AI-01: "Persona Distinctiveness"
**Ref:** `DoL-102`
**Objective:** Verify DSPy Optimization successfully differentiates roles.
- [x] **Test:** Replay `mission_20260127_172522.jsonl` against all 3 personas.
- [x] **Pass:** * Pilot Avg Word Count < 25.
    * Analyst Avg Word Count > 40.
    * Factuality Score = 100% for all.
- [x] **Evidence:** Wiki `OPS-002` validation table.

---

## 🛡️ TIER 3: Field Validation (Physics & Latency)
*Focus: "The Thesis" - Hardware-in-the-Loop Science.*

### 🔵 TC-100: "The Latency Run"
**Ref:** `DoL-100` | **Hardware:** Autel Evo 4T MAX V2 + Dronetag Mini
**Objective:** Compare $L_{net}$ (LTE) vs $L_{c2}$ (RF).
- [x] **Action:** Drive/Fly for 15 minutes in mixed 4G coverage.
- [x] **Metric:** Record `link_latency` average vs `c2_latency` average.
- [x] **Result:** Validated. MQTT latency spikes to 15s handled gracefully by Commander buffering.

### 🔵 TC-101: "The Twin-Sensor" (Calibration)
**Ref:** `DoL-101`
**Objective:** Measure Timestamp Jitter.
- [x] **Setup:** Mount Dronetag Mini physically onto Autel Evo 4T.
- [x] **Action:** Perform "Box Pattern" flight (Jorvas Flight).
- [x] **Pass:** Position delta between sensors < 5 meters (GNSS accuracy limit).
- [x] **Evidence:** `analysis_172522.png` confirmed correlation between Autel RTK and Dronetag GPS.

---

## 🛡️ TIER 4: Multi-Domain Fusion (Strategic)
*Focus: "The Vision" - Cross-Domain Correlation.*

### 🟣 TC-1000: "ADS-B Ingestion"
**Ref:** `ToL-04`
- [ ] **Test:** Stream `dump1090` JSON.
- [ ] **Pass:** Commercial flight appears as distinct icon type.

## 📋 Pre-Flight Checklist (The "Go/No-Go")
1. [x] **Mosquitto** running on `:1883`.
2. [x] **Ollama** running `llama3.1`.
3. [x] **DSPy Configs** (`optimized_*.json`) loaded.
4. [x] **Golden Dataset** available in `golden_datasets/`.
