# Exploratory Data Analysis (EDA) - Mission Visualization

This directory contains exploratory data analysis visualizations for SecuringSkies mission telemetry data.

## Generated Visualizations

### 1. Flight Paths (`01_flight_paths.png`)
- **Left Panel**: Multi-sensor flight path overlay showing all tracking sources
  - Ground Station (OwnTracks) - Mobile ground control position
  - Drone RemoteID (Dronetag) - ASTM F3411 compliant remote identification
  - Drone OSD - On-screen display telemetry
  - Drone State - Detailed drone state information
  
- **Right Panel**: Drone path colored by operational state (airborne, grounded, etc.)

### 2. Altitude Profiles (`02_altitude_profiles.png`)
- **Top Left**: Altitude profile from all sources (MSL, ATO, Height)
- **Top Right**: Vertical speed profile showing climb/descent rates
- **Bottom Left**: Altitude distribution histogram with mean indicator
- **Bottom Right**: Atmospheric pressure measurements during flight

### 3. Speed Analysis (`03_speed_analysis.png`)
- **Top Left**: Drone horizontal speed over time
- **Top Right**: Ground station speed tracking
- **Bottom Left**: Speed distribution histogram with statistics
- **Bottom Right**: Heading vs speed correlation plot

### 4. Battery Monitoring (`04_battery_monitoring.png`)
- **Left**: Drone battery level throughout mission
- **Right**: Ground station battery consumption
- Warning levels indicated at 20% threshold

### 5. Link Quality (`05_link_quality.png`)
- **Top Left**: Dronetag position accuracy over time
- **Top Right**: Ground station position accuracy
- **Bottom Left**: Wireless link state monitoring
- **Bottom Right**: Message count distribution by topic

### 6. Temporal Distribution (`06_temporal_distribution.png`)
- **Top**: Message rate per 10-second bins showing data flow intensity
- **Bottom**: Cumulative messages by source over mission time

### 7. Summary Statistics (`07_summary_statistics.png`)
Comprehensive statistical dashboard including:
- Mission overview (duration, timestamps, record counts)
- Dronetag statistics (speed, altitude metrics)
- Ground station statistics (speed, battery usage)
- Drone OSD statistics (height, battery consumption)
- Data source distribution
- Operational state distribution pie chart

### 8. Summary Statistics CSV (`summary_statistics.csv`)
Machine-readable summary of key mission metrics

## Usage

### Running the Analysis

```bash
# Analyze the default mission data
python labs/eda_mission_analysis.py

# Analyze a specific mission file
python labs/eda_mission_analysis.py --input golden_datasets/mission_YYYYMMDD_HHMMSS.jsonl

# Specify custom output directory
python labs/eda_mission_analysis.py --output my_analysis_output/
```

### Command-Line Options

- `--input <path>`: Path to input JSONL mission file (default: `golden_datasets/mission_20260127_172522.jsonl`)
- `--output <dir>`: Output directory for plots (default: `docs/eda_plots`)

## Data Sources

The analysis processes telemetry from multiple heterogeneous sources:

1. **OwnTracks**: Ground station location and status (mobile device)
2. **Dronetag**: ASTM F3411 Remote ID broadcasts (GPS-based)
3. **Autel Drone OSD**: Proprietary telemetry with RTK positioning
4. **Drone State**: Detailed flight controller state

## Key Insights from Mission 20260127_172522

- **Duration**: 12.6 minutes (757 seconds)
- **Total Records**: 3,434 telemetry messages
- **Drone Performance**:
  - Maximum speed: 15.98 m/s (57.5 km/h)
  - Mean speed: 3.18 m/s
  - Maximum altitude: 125.1 m (MSL)
  - Mean altitude: 68.6 m (MSL)
  
- **Data Quality**:
  - Dronetag: 611 records
  - OwnTracks: 379 records
  - Drone OSD: 661 records
  
## Dependencies

Required Python packages (see `requirements.txt`):
- pandas >= 2.2.0
- matplotlib >= 3.8.0
- numpy >= 1.26.0
- seaborn (for improved styling)

## Integration with Platform

This EDA tool complements the existing `compare_sensors.py` script by providing:
- Broader sensor coverage (not just twin-sensor comparison)
- Temporal analysis and message rate monitoring
- Battery and link quality tracking
- Comprehensive statistical summaries

## Future Enhancements

Potential additions:
- 3D flight path visualization
- Wind vector analysis
- RTK fix quality correlation
- Inter-sensor latency analysis
- Geofence boundary plotting
- Mission replay synchronization

## License

MIT License - Part of the SecuringSkies Platform
