# Data Fusion and Latency Effects: A Deep Dive

**Understanding the Two Forces That Pull Your Dots Apart**

## Executive Summary

When comparing real-time drone telemetry from multiple sensors, the observed position difference is influenced by two distinct factors:

1. **Hardware Gap** (Sensor Accuracy): Physical disagreement between sensors
2. **Time Gap** (Network Latency): Ghosting effect from drone movement during data transmission

## The Mathematics

### Total Error Formula

```
Total Error = √((Sensor Drift)² + (Speed × Latency)²)
```

## Measured Results

### Hardware Gap (Sensor Accuracy)

- **Magnitude**: 2.26 meters
- **Source**: Physical disagreement between Autel RTK and Dronetag GPS
- **Latency Dependent**: NO
- **Proof**: Measured during hovering (speed ≈ 0 m/s)

### Time Gap (Network Latency)

- **Magnitude**: Speed × 1.19s
- **Source**: Drone movement during MQTT packet transmission
- **Latency Dependent**: YES
- **Example**: At 10 m/s → 11.87m error

## Scenario Analysis

| Scenario | Speed | Hardware Error | Latency Error | Total Offset |
|----------|-------|----------------|---------------|-------------|
| Hovering        |     0 m/s |   2.26 m |    0.00 m |    2.26 m |
| Slow Cruise     |     5 m/s |   2.26 m |    5.94 m |    6.35 m |
| Normal Cruise   |    10 m/s |   2.26 m |   11.87 m |   12.09 m |
| Fast Cruise     |    15 m/s |   2.26 m |   17.81 m |   17.95 m |
| Sprint          |    20 m/s |   2.26 m |   23.75 m |   23.85 m |

## Why Altitude is Different

**Observed Altitude Error**: 4.36 meters

Altitude error remains consistently low because:

- Drones primarily fly level (horizontal movement)
- Vertical speed is typically near zero
- Latency doesn't significantly affect altitude (no vertical 'ghosting')
- The small error is purely due to reference differences (MSL vs AGL)

## Key Insights

### Position Accuracy
- **HIGHLY dependent on latency** when drone is moving
- Error scales linearly with speed
- At cruising speed (10 m/s): 12.09m total error

### Altitude Accuracy
- **Mostly independent of latency**
- Consistent regardless of horizontal speed
- Error dominated by reference system differences: 4.36m

## System Assessment

✅ **Low Sensor Error** (2.26m) - Excellent hardware
⚠️  **Standard Network Latency** (1.19s) - Typical LTE performance

## Recommendations

1. **For Real-Time Display**: Implement predictive filtering to compensate for latency
2. **For Post-Flight Analysis**: Use timestamp-based alignment (already done)
3. **For Mission Planning**: Account for speed-dependent position uncertainty
4. **For Sensor Validation**: Measure accuracy during hovering to isolate hardware gap

## Technical Notes

### Data Sources
- **Autel Drone**: RTK-enabled high-precision positioning
- **Dronetag**: Standard GPS Remote ID transponder
- **Network**: LTE-based MQTT telemetry

### Calculation Method
1. Extract synchronized position data from both sensors
2. Calculate position error using Haversine formula
3. Identify hovering periods (speed < 0.5 m/s) to measure hardware gap
4. Calculate latency-induced error: Speed × Latency
5. Validate formula: √(Hardware² + Latency²) ≈ Observed Error

---

*Generated: 2026-01-28 14:43:35*
