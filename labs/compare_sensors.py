"""
LABS: Twin-Sensor Correlation Analysis
Version: 1.2.3
Author: SecuringSkies Data Science
Description: Validates RTK vs GPS accuracy from raw MQTT logs.
"""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Configuration
LOG_FILE = 'golden_datasets/mission_20260127_172522.jsonl'
DRONE_SERIAL = '1748FEV3HMM825451479'  # Filter strict drone telemetry
OUTPUT_IMAGE = 'docs/images/twin_sensor_correlation.png'

def load_telemetry(filepath):
    data = []
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return []
        
    with open(filepath, 'r') as f:
        for line in f:
            try:
                data.append(json.loads(line))
            except:
                pass
    return data

def process_data(data):
    rows = []
    for entry in data:
        ts = entry.get('ts')
        topic = entry.get('topic', '')
        payload = entry.get('data', {})
        
        row = {'ts': ts, 'topic': topic}
        
        # 1. Autel Drone (RTK Source)
        if 'thing/product' in topic and DRONE_SERIAL in topic:
            row['sensor'] = 'AUTEL'
            row['lat'] = payload.get('latitude')
            row['lon'] = payload.get('longitude')
            row['alt'] = payload.get('height') # AGL
            row['pos_type'] = payload.get('pos_type') # 50 = RTK Fixed
            
        # 2. Dronetag Mini (GPS Source)
        elif 'dronetag' in topic:
            row['sensor'] = 'DRONETAG'
            loc = payload.get('location', {})
            row['dt_lat'] = loc.get('latitude')
            row['dt_lon'] = loc.get('longitude')
            
            # Extract MSL Altitude
            alts = payload.get('altitudes', [])
            msl_val = next((item['value'] for item in alts if item['type'] == 'MSL'), None)
            if msl_val is None and alts:
                 msl_val = alts[0]['value']
            row['dt_alt'] = msl_val
        
        rows.append(row)
    return pd.DataFrame(rows)

def analyze_and_plot(df):
    # Split Streams
    autel = df[df['sensor'] == 'AUTEL'][['ts', 'lat', 'lon', 'alt']].dropna().sort_values('ts')
    dronetag = df[df['sensor'] == 'DRONETAG'][['ts', 'dt_lat', 'dt_lon', 'dt_alt']].dropna().sort_values('ts')

    print(f"📊 Data Points - Autel: {len(autel)}, Dronetag: {len(dronetag)}")

    if autel.empty or dronetag.empty:
        print("⚠️ Insufficient data for correlation.")
        return

    # Merge on Timestamp (Nearest Neighbor within 2.0s)
    merged = pd.merge_asof(autel, dronetag, on='ts', direction='nearest', tolerance=2.0)
    merged = merged.dropna(subset=['lat', 'dt_lat'])
    
    # Calculate Haversine Error (Drift)
    lat_scale = 111320
    lon_scale = 111320 * np.cos(np.deg2rad(merged['lat'].mean()))
    
    merged['delta_lat_m'] = (merged['lat'] - merged['dt_lat']) * lat_scale
    merged['delta_lon_m'] = (merged['lon'] - merged['dt_lon']) * lon_scale
    merged['horiz_error'] = np.sqrt(merged['delta_lat_m']**2 + merged['delta_lon_m']**2)
    
    # Align Altitude Baselines (AGL vs MSL)
    alt_offset = merged['dt_alt'].mean() - merged['alt'].mean()
    merged['dt_alt_aligned'] = merged['dt_alt'] - alt_offset

    print(f"✅ ANALYSIS COMPLETE")
    print(f"   Mean Drift: {merged['horiz_error'].mean():.2f} m (Includes Network Latency)")
    print(f"   Max Drift:  {merged['horiz_error'].max():.2f} m")
    print(f"   Alt Offset: {alt_offset:.2f} m (MSL - AGL)")

    # Plotting
    fig, axs = plt.subplots(3, 1, figsize=(10, 15))
    
    # 1. Map Path
    axs[0].plot(merged['lon'], merged['lat'], label='Autel (RTK)', color='blue', linewidth=2)
    axs[0].plot(merged['dt_lon'], merged['dt_lat'], label='Dronetag (GPS)', color='orange', linestyle='--', linewidth=2)
    axs[0].set_title(f'Twin-Sensor Flight Path (Correlation: {len(merged)} pts)')
    axs[0].legend()
    axs[0].grid(True)
    axs[0].set_aspect('equal')
    
    # 2. Altitude Profile
    time_base = merged['ts'].min()
    axs[1].plot(merged['ts'] - time_base, merged['alt'], label='Autel AGL', color='blue')
    axs[1].plot(merged['ts'] - time_base, merged['dt_alt_aligned'], label='Dronetag (Aligned)', color='orange', linestyle='--')
    axs[1].set_title(f'Altitude Profile (Aligned by {alt_offset:.1f}m)')
    axs[1].set_ylabel('Height (m)')
    axs[1].legend()
    axs[1].grid(True)
    
    # 3. Error Delta
    axs[2].plot(merged['ts'] - time_base, merged['horiz_error'], color='purple', alpha=0.7)
    axs[2].set_title('Real-Time Position Drift (Sensor Variance + Network Latency)')
    axs[2].set_xlabel('Mission Time (s)')
    axs[2].set_ylabel('Error (m)')
    axs[2].grid(True)
    
    plt.tight_layout()
    os.makedirs(os.path.dirname(OUTPUT_IMAGE), exist_ok=True)
    plt.savefig(OUTPUT_IMAGE)
    print(f"🖼️  Plot saved to: {OUTPUT_IMAGE}")

if __name__ == "__main__":
    raw_data = load_telemetry(LOG_FILE)
    if raw_data:
        df = process_data(raw_data)
        analyze_and_plot(df)
