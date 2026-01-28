# Data Source Comparison Report

**Generated:** 2026-01-28 13:54:10

## Overview

This report compares MQTT telemetry data with raw flight data files from the same flight session to analyze differences in data richness, temporal coverage, and data quality.

## Data Sources

### MQTT Telemetry

- **Total Records:** 3,434
- **Duration:** 757.2s (12.6 minutes)
- **Update Rate:** 4.53 Hz
- **Topics:** 8
- **Unique Fields:** 110

**Topic Breakdown:**

- `owntracks/viewer/SamsungZ7`: 379 records, 20 fields
- `thing/product/TH7825451059/events`: 8 records, 3 fields
- `dronetag`: 617 records, 17 fields
- `thing/product/TH7825451059/osd`: 341 records, 9 fields
- `thing/product/1748FEV3HMM825451479/osd`: 320 records, 45 fields
- `thing/product/sn`: 320 records, 3 fields
- `thing/product/TH7825451059/state`: 1,441 records, 10 fields
- `thing/product/1748FEV3HMM825451479/state`: 8 records, 11 fields

### Airdata CSV (Autel Drone)

- **Total Records:** 2,495
- **Duration:** 552.0s (9.2 minutes)
- **Update Rate:** 4.52 Hz
- **Fields:** 53

**Available Fields:**

1. `time(millisecond)`
2. `datetime(utc)`
3. `latitude`
4. `longitude`
5. `height_above_takeoff(meters)`
6. `height_above_ground_at_drone_location(meters)`
7. `ground_elevation_at_drone_location(meters)`
8. `altitude_above_seaLevel(meters)`
9. `height_sonar(meters)`
10. `speed(m/s)`
11. `distance(meters)`
12. `mileage(meters)`
13. `satellites`
14. `gpslevel`
15. `voltage(v)`
16. `max_altitude(meters)`
17. `max_ascent(meters)`
18. `max_speed(m/s)`
19. `max_distance(meters)`
20. ` xSpeed(m/s)`
21. ` ySpeed(m/s)`
22. ` zSpeed(m/s)`
23. ` compass_heading(degrees)`
24. ` pitch(degrees)`
25. ` roll(degrees)`
26. `isPhoto`
27. `isVideo`
28. `rc_elevator`
29. `rc_aileron`
30. `rc_throttle`
31. `rc_rudder`
32. `rc_elevator(percent)`
33. `rc_aileron(percent)`
34. `rc_throttle(percent)`
35. `rc_rudder(percent)`
36. `gimbal_heading(degrees)`
37. `gimbal_pitch(degrees)`
38. `gimbal_roll(degrees)`
39. `battery_percent`
40. `voltageCell1`
41. `voltageCell2`
42. `voltageCell3`
43. `voltageCell4`
44. `voltageCell5`
45. `voltageCell6`
46. `current(A)`
47. `battery_temperature(c)`
48. `altitude(meters)`
49. `ascent(meters)`
50. `flycStateRaw`
51. `flycState`
52. `message`
53. `datetime`

### Dronetag Export (Remote ID)

- **Total Records:** 609
- **Duration:** 633.0s (10.6 minutes)
- **Update Rate:** 0.96 Hz
- **Fields:** 14

**Available Fields:**

1. `altitude`
2. `geo_altitude`
3. `height`
4. `horizontal_accuracy`
5. `location.lat`
6. `location.lon`
7. `pressure`
8. `speed_accuracy`
9. `time`
10. `velocity.x`
11. `velocity.y`
12. `velocity.z`
13. `vertical_accuracy`
14. `datetime`

## Key Findings

### Data Richness

- **MQTT** provides 110 unique fields across multiple topics, offering heterogeneous sensor fusion from multiple sources (ground station, drone OSD, RemoteID, etc.)
- **Airdata** provides 53 fields focused on detailed drone flight parameters including RC inputs, gimbal angles, battery cells, etc.

### Temporal Coverage

- **MQTT**: 757s coverage with mixed update rates across topics
- **Airdata**: 552s coverage with consistent 4.5 Hz sampling
- **Dronetag**: 633s coverage with ~1.0 Hz updates

### Data Quality Advantages

**MQTT Data Advantages:**
- Real-time sensor fusion from multiple heterogeneous sources
- Ground station telemetry and link latency metrics
- RTK positioning data with fix status
- Network connectivity and wireless link quality
- Comprehensive system state across all components

**Airdata Advantages:**
- High-frequency (5 Hz) drone-specific data
- Detailed RC control inputs (elevator, aileron, throttle, rudder)
- Individual battery cell voltages
- Gimbal control angles (pitch, roll, yaw)
- Sonar height and flight state information
- Photo/video capture states

**Dronetag Advantages:**
- Standardized ASTM F3411 Remote ID format
- Multiple altitude references (HAE, PA-QNE, ATO, MSL)
- Velocity components in 3D space
- Explicit accuracy metrics (horizontal, vertical)
- Air pressure measurements

## Recommendations

1. **Use MQTT data** for comprehensive multi-sensor analysis and real-time system monitoring
2. **Use Airdata** for detailed drone flight dynamics analysis and RC control validation
3. **Use Dronetag** for regulatory compliance verification and standardized reporting
4. **Combine sources** for maximum insight: MQTT for context, Airdata for detail, Dronetag for compliance
