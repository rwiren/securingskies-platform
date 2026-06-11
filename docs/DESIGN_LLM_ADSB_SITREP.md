# SecuringSkies — LLM-Augmented Situational Awareness for ADS-B Threat Detection
## Design Document v0.1 (2026-05-31)

---

## 1. Problem Statement

The current SecuringSkies ADS-B dashboard presents threat information through:
- Numerical scores (spoof_score, ml_score, persistence counter)
- Color-coded markers (green/amber/red aircraft)
- Alert banners ("CONFIRMED THREAT")
- Expert-mode data tables (GNSS, sensor health)

**Gap:** A human operator in a high-stress aviation environment cannot efficiently interpret raw ML confidence values, per-feature reconstruction errors, or cross-sensor consistency metrics. They need contextual, role-appropriate explanations of *what* is happening, *why* the system flagged it, and *what action* is recommended.

The existing GhostCommander platform (securingskies-platform) already solves this for drone telemetry — it takes raw MQTT/JSON streams, feeds them through persona-specific LLM prompts, and produces natural-language SITREPs with audited quality metrics. The architecture is transport-agnostic (MQTT + JSON), making it directly applicable to ADS-B anomaly data.

---

## 2. Existing Components

### From securingskies-platform (LLM layer)
| Component | Role | Reusable? |
|-----------|------|-----------|
| GhostCommander | MQTT ingestion → LLM → SITREP | ✅ Core architecture unchanged |
| Personas (Pilot/Commander/Analyst) | Role-specific prompt engineering | ✅ New personas needed for ADS-B context |
| DSPy Optimizer | Few-shot prompt training from golden logs | ✅ Train on ADS-B threat scenarios |
| Auditor | Recall, Factuality, Hallucination, Safety scoring | ✅ Adapt metrics for aviation domain |
| Constitutional Guardrails | Prevent hallucination, enforce terminology | ✅ New rules for aviation terminology |
| Black Box Recorder | Forensic JSONL logging | ✅ As-is |

### From ADS-B dashboard (detection layer)
| Component | Data produced | Format |
|-----------|--------------|--------|
| ML Inference (GRU) | Per-aircraft anomaly score, per-feature error | `sensor-core/ml-anomaly` |
| Heuristic engine | spoof_score, spoof_flags | Embedded in `map_update` |
| GNSS Monitor | Per-sensor deviation, alerts, jamming/spoofing flags | `sensor-core/gnss-health` |
| Accuracy Monitor | Cross-sensor consistency, velocity errors | `sensor-core/accuracy` |
| Continual Eval | Model health, threshold drift, FP rate | `sensor-core/ml-health` |
| Persistence gauge | Threat confirmation (0-5 windows) | Client-side state |

### From WebXR (visualization layer)
| Component | Role |
|-----------|------|
| 3D aircraft scene | Spatial awareness — where are threats? |
| Sensor platforms | Network health at a glance |
| GNSS sky dome | Satellite integrity visualization |
| Click-to-inspect | Drill-down on individual aircraft |

---

## 3. Proposed Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MQTT BROKER (mosquitto)                    │
│  Topics:                                                     │
│    +/aircraft, sensor-core/ml-anomaly, sensor-core/gnss-health│
│    sensor-core/accuracy, sensor-core/ml-health               │
└──────────┬──────────────────────────────────────┬────────────┘
           │                                      │
           ▼                                      ▼
┌─────────────────────┐              ┌─────────────────────────┐
│  ADS-B SITREP Agent │              │  Existing Dashboard     │
│  (new component)    │              │  (map_update → browser) │
│                     │              └─────────────────────────┘
│  Subscribes to:     │
│  - ml-anomaly       │              ┌─────────────────────────┐
│  - gnss-health      │              │  WebXR 3D View          │
│  - ml-health        │              │  (aircraft + sensors)   │
│  - +/aircraft (summary)            └─────────────────────────┘
│                     │
│  Triggers SITREP:   │
│  - On threat (persist ≥ 3)│
│  - On GNSS alert    │
│  - On model degradation│
│  - Periodic (every 60s)│
│                     │
│  Publishes to:      │
│  - sensor-core/sitrep│
│                     │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│  PRESENTATION LAYER                                          │
│                                                              │
│  Option A: Text panel in dashboard (like sensor cards)       │
│  Option B: Voice synthesis (Web Speech API in browser)       │
│  Option C: Dedicated SITREP page with history                │
│  Option D: Overlay in WebXR (floating text panel)            │
│  Option E: All of the above, persona-selectable              │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. ADS-B Personas

### 4.1 ATC Operator (Air Traffic Control)
**Context:** Monitoring airspace for unauthorized or anomalous traffic.
**Style:** Concise, procedural, uses ICAO phraseology.
**Triggers on:** New threat, threat escalation, threat cleared.
**Example output:**
> TRAFFIC ADVISORY: Suspect track 461FA4, FL168, bearing 059 from EFHK, velocity inconsistent with declared flight plan. Confidence HIGH (5/5 windows). Recommend: verify with adjacent FIR.

### 4.2 Security Analyst
**Context:** Investigating potential electronic warfare or spoofing campaigns.
**Style:** Technical, references specific features and scores, pattern-oriented.
**Triggers on:** Any anomaly, GNSS degradation, model drift.
**Example output:**
> ANALYSIS: GRU reconstruction error 0.14 on hex 461FA4 (FIN1DF), dominant feature: velocity_drift (62%). Pattern consistent with gradual position manipulation — reported GS 406kt but position-derived velocity shows 380kt divergence over 30s window. Cross-sensor RSSI consistent (seen by 3/3 sensors at expected power). Assessment: kinematic spoofing, not RF replay.

### 4.3 Duty Commander
**Context:** Decision authority for escalation, sector closure, military coordination.
**Style:** Strategic, focuses on patterns across multiple aircraft, recommends actions.
**Triggers on:** Confirmed threats, multi-aircraft anomalies, GNSS-wide events.
**Example output:**
> SITUATION: 2 confirmed anomalous tracks in sector 090-180, FL300-350, both showing velocity drift pattern. GNSS integrity nominal across all ground sensors. Assessment: localized ADS-B spoofing, not wide-area GNSS jamming. Recommend: notify EFHK TWR, cross-reference with primary radar, maintain current operations.

### 4.4 System Engineer
**Context:** Monitoring platform health, model performance, sensor status.
**Style:** Metrics-focused, infrastructure-aware.
**Triggers on:** Model drift, sensor offline, GNSS degradation, high FP rate.
**Example output:**
> HEALTH: ML model threshold drifted 2.6x from baseline (0.136 → 0.357). FP rate 0%. Cause: score distribution shift — p95 dropped from 0.03 to 0.01, suggesting traffic pattern change (night hours, fewer aircraft). Action: monitor, no recalibration needed unless FP emerges.

---

## 5. Confidence Communication Design

### The core research question:
*How does a human operator interact with AI confidence in high-stress aviation?*

### Design principles:

**1. Never show raw numbers alone.**
Confidence is communicated through multiple channels simultaneously:
- **Spatial** (WebXR): threat position, proximity to airports, clustering
- **Temporal** (persistence gauge): how long has the system been confident?
- **Linguistic** (SITREP): natural-language explanation calibrated to role
- **Visual** (color/animation): immediate pre-attentive processing

**2. Explain the "why" not just the "what".**
The LLM bridges ML features → human understanding:
- "velocity_drift = 0.62" → "aircraft is reporting speed inconsistent with its position changes"
- "spoof_score = 0.8, flags=[rssi_error]" → "signal strength doesn't match the claimed distance"

**3. Calibrated language for confidence levels.**
| Persistence | ML Score | Language |
|-------------|----------|----------|
| 1/5 | > threshold | "Anomaly detected, monitoring" |
| 3/5 | sustained | "Suspected threat, elevated confidence" |
| 5/5 | confirmed | "Confirmed threat, high confidence" |
| 5/5 + multi-aircraft | pattern | "Coordinated attack pattern detected" |

**4. Distinguish sensor issues from actual threats.**
The LLM must cross-reference:
- Is GNSS degraded? → "Reduced detection confidence due to sensor-east multipath"
- Is model drifting? → "Note: ML threshold elevated, detection sensitivity reduced"
- Single sensor vs multi-sensor? → "Corroborated by 3/3 sensors" vs "Single-sensor detection only"

**5. Action-oriented, not information-oriented.**
Each SITREP ends with a recommended action appropriate to the persona's authority level.

---

## 6. Integration with WebXR

### Concept: "AI Wingman" overlay in 3D view

In the WebXR scene, a floating panel (like the existing HUD) shows the latest SITREP. When a threat is active:
- The flagged aircraft gets a pulsing ring (already exists)
- A "thought bubble" line connects the aircraft to a floating text card explaining why
- The card content is the LLM-generated explanation, not raw numbers
- Voice readout via Web Speech API (optional, toggle button)

### Data flow:
```
sensor-core/sitrep (MQTT) → browser subscribes → update HUD panel
                                               → trigger TTS if enabled
                                               → highlight referenced aircraft
```

---

## 7. Auditor Adaptation for Aviation

The existing auditor measures Recall, Factuality, Hallucination, Safety. For ADS-B:

| Metric | Aviation adaptation |
|--------|-------------------|
| **Recall** | Did the SITREP mention all flagged aircraft? |
| **Factuality** | Do stated scores/altitudes/callsigns match the data? |
| **Hallucination** | Did it invent aircraft, threats, or sensor states? |
| **Safety** | Does it recommend actions within authority? No "shoot down" language? |
| **Timeliness** (new) | Was the SITREP generated within 2s of trigger? |
| **Consistency** (new) | Does repeated analysis of same data produce same assessment? |

---

## 8. Implementation Phases

### Phase 1: Backend SITREP agent (minimal)
- New service: `adsb_sitrep_agent.py`
- Subscribes to ml-anomaly, gnss-health, ml-health
- On threat trigger: formats context, calls LLM, publishes to `sensor-core/sitrep`
- Single persona (Security Analyst)
- Model: Ollama llama3.1 (local) or litellm for cloud fallback

### Phase 2: Dashboard integration
- Add SITREP panel to main dashboard (collapsible, like sensor cards)
- Subscribe to `sensor-core/sitrep` via Socket.IO
- Show latest SITREP with timestamp and confidence level

### Phase 3: Multi-persona + WebXR
- Persona selector in UI
- WebXR floating SITREP panel
- Voice synthesis toggle
- DSPy optimization using recorded threat events as training data

### Phase 4: Research evaluation
- A/B test: operators with/without LLM SITREP
- Measure: time-to-decision, false alarm response rate, situational awareness score
- Publish findings on human-AI teaming in aviation security

---

## 9. Key Design Decisions (TBD)

1. **Local vs cloud LLM?** Latency requirement is <2s for threat response. Llama 3.1 8B on local GPU vs API call?
2. **Trigger frequency?** Every anomaly? Only on persistence ≥ 3? Periodic summary?
3. **How much context to feed?** Full aircraft list + all scores? Or just the flagged aircraft?
4. **Voice in WebXR?** Spatial audio (threat direction) or standard TTS?
5. **Multi-language?** Finnish/English for ATC context?
6. **Liability framing?** "AI recommends" vs "AI observes" — EU AI Act implications for aviation safety systems.

---

## 10. Relationship to Existing Work

This design bridges two existing systems without modifying either:
- **securingskies-platform**: Proven LLM-MQTT-SITREP architecture (drone domain)
- **adsb-dashboard**: Proven ML anomaly detection (ADS-B domain)

The new component (`adsb_sitrep_agent`) is a subscriber/publisher that reads from one and writes for the other. Both existing systems continue to operate independently.

The research contribution is the **confidence communication framework** — how to translate ML model outputs into actionable human understanding in safety-critical aviation contexts, using role-specific LLM personas with audited quality guarantees.
