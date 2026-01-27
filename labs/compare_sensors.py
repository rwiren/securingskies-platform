"""
SecuringSkies Sensor Fusion Validator
-------------------------------------
Purpose: Comparative analysis of RTK (Autel) vs Remote ID (Dronetag) telemetry.
Version: 1.0.0
Author: Ghost Commander

Usage:
    python3 labs/compare_sensors.py logs/mission_20260127_150633.jsonl
"""

import json
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy.interpolate import interp1d

# --- CONFIGURATION ---
LATENCY_SHIFT_SEC = 0.0  # Adjust if you want to artificially compensate for lag
R_EARTH = 6371000  # Earth radius in meters

def load_mission_log(filepath):
    """Parses the JSONL mission log into a Pandas DataFrame."""
    data = []
    print(f"📂 Loading mission log: {filepath}")
    
    with open(filepath, 'r') as f:
        for line in f:
            try:
                entry = json.loads(line)
                # Flatten the 'data' structure slightly for easier access
                row = {'ts': entry.get('ts'), 'topic': entry.get('topic', '')}
                
                # Check for Autel Data (OSD topic or semantic type)
                if 'data' in entry and isinstance(entry['data'], dict):
                    payload = entry['data']
                    row.update(payload)
                    
                    # Tag Autel rows
                    if 'capacity_percent' in payload or 'height' in payload:
                        row['sensor'] = 'AUTEL'
                        
                    # Tag Dronetag rows (Remote ID)
                    elif 'operational_state' in payload or 'altitudes' in payload:
                        row['sensor'] = 'DRONETAG'
                        # Extract nested Remote ID location if present
                        if 'location' in payload:
                            row['dt_lat'] = payload['location'].get('latitude')
                            row['dt_lon'] = payload['location'].get('longitude')
                        # Extract altitude (Prefer MSL)
                        if 'altitudes' in payload:
                            for alt in payload['altitudes']:
                                if alt['type'] == 'MSL':
                                    row['dt_alt'] = alt['value']
                                    break
                
                data.append(row)
            except json.JSONDecodeError:
                continue

    return pd.DataFrame(data)

def process_telemetry(df):
    """Separates and synchronizes the two telemetry streams."""
    
    # 1. Extract Autel Stream (Ground Truth - RTK)
    # Using 'height' as a proxy for valid telemetry packets
    autel_df = df[df['sensor'] == 'AUTEL'].dropna(subset=['latitude', 'longitude']).copy()
    autel_df = autel_df[['ts', 'latitude', 'longitude', 'height']].rename(
        columns={'latitude': 'lat_ref', 'longitude': 'lon_ref', 'height': 'alt_ref'}
    )
    
    # 2. Extract Dronetag Stream (Device Under Test)
    dt_df = df[df['sensor'] == 'DRONETAG'].dropna(subset=['dt_lat', 'dt_lon']).copy()
    dt_df = dt_df[['ts', 'dt_lat', 'dt_lon', 'dt_alt']]
    
    print(f"📊 Extracted Records - Autel: {len(autel_df)} | Dronetag: {len(dt_df)}")

    if autel_df.empty or dt_df.empty:
        print("❌ Error: Insufficient data for comparison.")
        sys.exit(1)

    # 3. Synchronization (Merge Asof)
    # Align Dronetag timestamps to the closest Autel timestamp
    autel_df = autel_df.sort_values('ts')
    dt_df = dt_df.sort_values('ts')
    
    merged = pd.merge_asof(
        autel_df, 
        dt_df, 
        on='ts', 
        direction='nearest', 
        tolerance=2.0 # 2-second tolerance window
    ).dropna()
    
    # 4. Error Calculation (Haversine Approximation for short distances)
    # Convert degrees to meters
    lat_scale = 111320
    lon_scale = 111320 * np.cos(np.deg2rad(merged['lat_ref'].mean()))
    
    merged['delta_lat_m'] = (merged['lat_ref'] - merged['dt_lat']) * lat_scale
    merged['delta_lon_m'] = (merged['lon_ref'] - merged['dt_lon']) * lon_scale
    merged['horizontal_error'] = np.sqrt(merged['delta_lat_m']**2 + merged['delta_lon_m']**2)
    
    # 5. Altitude Normalization (Compensate for AGL vs MSL offset)
    # Calculate the mean difference and subtract it to compare the "profile shape"
    alt_offset = merged['alt_ref'].mean() - merged['dt_alt'].mean()
    merged['dt_alt_aligned'] = merged['dt_alt'] + alt_offset
    
    print(f"ℹ️  Altitude Offset Detected: {alt_offset:.2f}m (Aligned for plotting)")
    
    return merged, alt_offset

def plot_analysis(df, alt_offset):
    """Generates a comprehensive matplotlib visualization."""
    
    # Setup Time Axis (Relative to start)
    df['rel_time'] = df['ts'] - df['ts'].min()
    
    plt.style.use('seaborn-v0_8-darkgrid')
    fig = plt.figure(figsize=(12, 12))
    gs = fig.add_gridspec(3, 2)

    # --- PLOT 1: Top Down Trajectory (Map) ---
    ax1 = fig.add_subplot(gs[0, :])
    ax1.plot(df['lon_ref'], df['lat_ref'], 'b-', linewidth=2, label='Autel (RTK Ground Truth)')
    ax1.plot(df['dt_lon'], df['dt_lat'], 'r--', linewidth=1.5, label='Dronetag (Remote ID)')
    ax1.set_title('2D Trajectory Trace (WGS84)', fontsize=12, fontweight='bold')
    ax1.set_xlabel('Longitude')
    ax1.set_ylabel('Latitude')
    ax1.axis('equal')
    ax1.legend()

    # --- PLOT 2: Altitude Profile ---
    ax2 = fig.add_subplot(gs[1, 0])
    ax2.plot(df['rel_time'], df['alt_ref'], 'b-', label='Autel (AGL)')
    ax2.plot(df['rel_time'], df['dt_alt_aligned'], 'r--', label=f'Dronetag (Aligned MSL)')
    ax2.fill_between(df['rel_time'], df['alt_ref'], df['dt_alt_aligned'], color='gray', alpha=0.2)
    ax2.set_title(f'Vertical Profile (Offset Corrected: {alt_offset:.1f}m)', fontsize=10, fontweight='bold')
    ax2.set_ylabel('Height (m)')
    ax2.set_xlabel('Mission Time (s)')
    ax2.legend()

    # --- PLOT 3: Horizontal Error over Time ---
    ax3 = fig.add_subplot(gs[1, 1])
    ax3.plot(df['rel_time'], df['horizontal_error'], 'k-', linewidth=1)
    ax3.axhline(df['horizontal_error'].mean(), color='orange', linestyle='--', label=f'Mean: {df["horizontal_error"].mean():.1f}m')
    ax3.set_title('Horizontal Position Error vs Time', fontsize=10, fontweight='bold')
    ax3.set_ylabel('Error (m)')
    ax3.set_xlabel('Mission Time (s)')
    ax3.legend()

    # --- PLOT 4: Error Distribution (Histogram) ---
    ax4 = fig.add_subplot(gs[2, :])
    ax4.hist(df['horizontal_error'], bins=30, color='purple', alpha=0.7, edgecolor='black')
    ax4.set_title('Horizontal Accuracy Distribution', fontsize=10, fontweight='bold')
    ax4.set_xlabel('Position Error (m)')
    ax4.set_ylabel('Count')
    
    # Stats Text
    stats = (
        f"Mean Error: {df['horizontal_error'].mean():.2f}m\n"
        f"Max Error:  {df['horizontal_error'].max():.2f}m\n"
        f"Std Dev:    {df['horizontal_error'].std():.2f}m\n"
        f"Duration:   {df['rel_time'].max():.0f}s"
    )
    ax4.text(0.95, 0.9, stats, transform=ax4.transAxes, 
             fontsize=10, verticalalignment='top', horizontalalignment='right',
             bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    plt.tight_layout()
    output_file = "sensor_comparison_report.png"
    plt.savefig(output_file, dpi=150)
    print(f"✅ Plot saved to: {output_file}")
    plt.show()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 compare_sensors.py <mission.jsonl>")
        # Default fallback for testing
        log_file = "mission_20260127_150633.jsonl"
    else:
        log_file = sys.argv[1]

    df_raw = load_mission_log(log_file)
    df_clean, offset = process_telemetry(df_raw)
    plot_analysis(df_clean, offset)
