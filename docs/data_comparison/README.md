# Data Source Comparison

This directory contains comparison analysis between MQTT telemetry data and raw flight data files from the same flight session.

## Generated Files

### `data_source_comparison.png`
Comprehensive visualization comparing three data sources:
- **MQTT Telemetry** (3,434 records, 110 unique fields)
- **Airdata CSV** (2,495 records, 53 fields) 
- **Dronetag Export** (609 records, 14 fields)

The visualization includes:
1. **Record Count Comparison**: Shows MQTT captures the most data points
2. **Update Rate Analysis**: MQTT and Airdata both ~4.5 Hz, Dronetag ~1 Hz
3. **Field Count**: MQTT offers 110 unique fields vs 53 (Airdata) and 14 (Dronetag)
4. **MQTT Topic Distribution**: Breakdown of 8 topics with state topic dominating
5. **Temporal Coverage**: Timeline showing MQTT covers 757s vs 552s (Airdata) and 633s (Dronetag)

### `comparison_report.md`
Detailed markdown report with:
- Complete field listings for each data source
- Key findings on data richness and temporal coverage
- Advantages of each data source
- Recommendations for when to use each source

## Key Findings

### Data Richness
- **MQTT**: 110 unique fields across 8 topics - provides heterogeneous sensor fusion
- **Airdata**: 53 fields focused on drone flight dynamics (RC inputs, gimbal, battery cells)
- **Dronetag**: 14 fields standardized for Remote ID compliance

### Update Rates
- **MQTT**: 4.53 Hz average (varies by topic)
- **Airdata**: 4.52 Hz consistent sampling
- **Dronetag**: 0.96 Hz (~1 Hz updates)

### Temporal Coverage
- **MQTT**: 757 seconds (12.6 minutes) - longest coverage
- **Airdata**: 552 seconds (9.2 minutes)
- **Dronetag**: 633 seconds (10.6 minutes)

## Usage

Run the comparison analysis:

```bash
# Default usage
python labs/compare_data_sources.py

# Custom paths
python labs/compare_data_sources.py \
  --mqtt golden_datasets/mission_20260127_172522.jsonl \
  --raw-dir data/raw \
  --output docs/data_comparison
```

## Recommendations

1. **Use MQTT data** for:
   - Comprehensive multi-sensor analysis
   - Real-time system monitoring
   - RTK positioning with fix status
   - Ground station telemetry and link latency

2. **Use Airdata** for:
   - Detailed drone flight dynamics
   - RC control validation
   - Battery cell analysis
   - Gimbal control verification

3. **Use Dronetag** for:
   - Regulatory compliance (ASTM F3411)
   - Standardized Remote ID reporting
   - Multi-altitude reference validation

4. **Combine sources** for maximum insight into flight operations
