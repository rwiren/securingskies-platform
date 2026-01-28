"""
Exploratory Data Analysis (EDA) for SecuringSkies Mission Data
Version: 1.0.0
Author: SecuringSkies Data Science
Description: Comprehensive visualization and analysis of mission telemetry from multiple sensors.

Usage:
    python labs/eda_mission_analysis.py [--input <path>] [--output <dir>]
"""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os
import argparse

# Set style for better-looking plots
sns.set_style('whitegrid')
plt.rcParams['figure.figsize'] = (14, 8)
plt.rcParams['figure.dpi'] = 100

class MissionDataAnalyzer:
    """Analyzes and visualizes SecuringSkies mission telemetry data."""
    
    # Configuration constants
    OUTPUT_DPI = 150
    BATTERY_WARNING_THRESHOLD = 20  # Battery warning level (%)
    TEMPORAL_BIN_SIZE_SECONDS = 10  # Bin size for temporal analysis
    
    def __init__(self, jsonl_path, output_dir='docs/eda_plots'):
        """
        Initialize the analyzer.
        
        Args:
            jsonl_path: Path to the mission JSONL file
            output_dir: Directory to save output plots
        """
        self.jsonl_path = jsonl_path
        self.output_dir = output_dir
        self.records = []
        self.df_owntracks = None
        self.df_dronetag = None
        self.df_drone_osd = None
        self.df_drone_state = None
        self.df_drone_rtk = None  # New: Autel RTK data
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
    def load_data(self):
        """Load and parse the JSONL file."""
        print(f"📂 Loading data from: {self.jsonl_path}")
        
        if not os.path.exists(self.jsonl_path):
            raise FileNotFoundError(f"Data file not found: {self.jsonl_path}")
        
        with open(self.jsonl_path, 'r') as f:
            for line in f:
                try:
                    record = json.loads(line)
                    # Validate basic structure
                    if 'ts' in record and 'topic' in record and 'data' in record:
                        self.records.append(record)
                except json.JSONDecodeError:
                    continue
        
        if not self.records:
            raise ValueError(f"No valid records found in {self.jsonl_path}")
        
        print(f"✅ Loaded {len(self.records)} records")
        return self
    
    def parse_data(self):
        """Parse records into structured DataFrames."""
        print("🔄 Parsing data into structured format...")
        
        owntracks_data = []
        dronetag_data = []
        drone_osd_data = []
        drone_state_data = []
        drone_rtk_data = []  # New: Autel drone with RTK data
        
        for record in self.records:
            ts = record.get('ts')
            topic = record.get('topic', '')
            data = record.get('data', {})
            
            # Parse OwnTracks (Ground Station)
            if 'owntracks' in topic:
                # Parse link latency
                link_latency_str = data.get('link_latency', '0s')
                try:
                    link_latency = float(link_latency_str.replace('s', ''))
                except:
                    # Calculate from timestamp difference
                    created_at = data.get('created_at') or data.get('tst')
                    link_latency = (ts - created_at) if created_at else 0
                
                owntracks_data.append({
                    'timestamp': ts,
                    'lat': data.get('lat'),
                    'lon': data.get('lon'),
                    'alt': data.get('alt'),
                    'speed': data.get('speed', 0),
                    'battery': data.get('batt'),
                    'accuracy': data.get('acc'),
                    'cog': data.get('cog', 0),  # Course over ground
                    'type': data.get('type', 'Unknown'),
                    'link_latency': link_latency
                })
            
            # Parse Dronetag (Remote ID)
            elif topic == 'dronetag' and 'location' in data:
                location = data.get('location', {})
                velocity = data.get('velocity', {})
                altitudes = data.get('altitudes', [])
                
                # Extract different altitude types
                msl_alt = next((a['value'] for a in altitudes if a['type'] == 'MSL'), None)
                hae_alt = next((a['value'] for a in altitudes if a['type'] == 'HAE-WGS84'), None)
                ato_alt = next((a['value'] for a in altitudes if a['type'] == 'ATO'), None)
                
                dronetag_data.append({
                    'timestamp': ts,
                    'lat': location.get('latitude'),
                    'lon': location.get('longitude'),
                    'accuracy': location.get('accuracy', 0),
                    'altitude_msl': msl_alt,
                    'altitude_hae': hae_alt,
                    'altitude_ato': ato_alt,
                    'heading': velocity.get('heading', 0),
                    'horizontal_speed': velocity.get('horizontal_speed', 0),
                    'vertical_speed': velocity.get('vertical_speed', 0),
                    'operational_state': data.get('operational_state', 'unknown'),
                    'air_pressure': data.get('air_pressure'),
                    'sensor_id': data.get('sensor_id', 'unknown')
                })
            
            # Parse Drone OSD (On-Screen Display - telemetry)
            elif 'osd' in topic:
                # Extract RTK position data for Autel drones
                position_state = data.get('position_state', {})
                pos_type = data.get('pos_type', '0')
                
                # Determine RTK status
                rtk_status = 'GPS'
                if pos_type == '50':
                    rtk_status = 'RTK_FIXED'
                elif pos_type == '16':
                    rtk_status = 'RTK_FLOAT'
                
                drone_osd_data.append({
                    'timestamp': ts,
                    'topic': topic,
                    'lat': data.get('latitude'),
                    'lon': data.get('longitude'),
                    'height': data.get('height', 0),
                    'battery': data.get('capacity_percent'),
                    'firmware': data.get('firmware_version'),
                    'wireless_link_state': data.get('wireless_link', {}).get('sdr_link_state', 0),
                    'wireless_quality': data.get('wireless_link', {}).get('sdr_quality', 0),
                })
                
                # If this is Autel drone with RTK data, add to RTK DataFrame
                if position_state and 'rtk_lat' in position_state:
                    drone_rtk_data.append({
                        'timestamp': ts,
                        'lat': data.get('latitude'),
                        'lon': data.get('longitude'),
                        'height': data.get('height', 0),
                        'rtk_lat': position_state.get('rtk_lat'),
                        'rtk_lon': position_state.get('rtk_lon'),
                        'rtk_hgt': position_state.get('rtk_hgt'),
                        'rtk_number': position_state.get('rtk_number', 0),
                        'gps_number': position_state.get('gps_number', 0),
                        'is_fixed': position_state.get('is_fixed', 0),
                        'rtk_inpos': position_state.get('rtk_inpos', 0),
                        'pos_type': pos_type,
                        'rtk_status': rtk_status,
                    })
            
            # Parse Drone State
            elif 'state' in topic and 'latitude' in data:
                drone_state_data.append({
                    'timestamp': ts,
                    'topic': topic,
                    'lat': data.get('latitude'),
                    'lon': data.get('longitude'),
                    'height': data.get('height', 0),
                    'battery': data.get('capacity_percent'),
                    'home_lat': data.get('home_point', {}).get('latitude'),
                    'home_lon': data.get('home_point', {}).get('longitude'),
                    'elevation': data.get('elevation'),
                    'gear': data.get('gear'),
                    'height_limit': data.get('height_limit'),
                    'horizontal_speed': data.get('horizontal_speed', 0),
                    'mode_code': data.get('mode_code'),
                    'wind_direction': data.get('wind_direction'),
                    'wind_speed': data.get('wind_speed', 0),
                })
        
        # Create DataFrames
        self.df_owntracks = pd.DataFrame(owntracks_data)
        self.df_dronetag = pd.DataFrame(dronetag_data)
        self.df_drone_osd = pd.DataFrame(drone_osd_data)
        self.df_drone_state = pd.DataFrame(drone_state_data)
        self.df_drone_rtk = pd.DataFrame(drone_rtk_data)
        
        # Convert timestamps to datetime
        for df in [self.df_owntracks, self.df_dronetag, self.df_drone_osd, self.df_drone_state, self.df_drone_rtk]:
            if not df.empty and 'timestamp' in df.columns:
                df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
                df['mission_time_s'] = df['timestamp'] - df['timestamp'].min()
        
        print(f"  📍 OwnTracks records: {len(self.df_owntracks)}")
        print(f"  🏷️  Dronetag records: {len(self.df_dronetag)}")
        print(f"  🚁 Drone OSD records: {len(self.df_drone_osd)}")
        print(f"  📡 Drone State records: {len(self.df_drone_state)}")
        print(f"  📡 Drone RTK records: {len(self.df_drone_rtk)}")
        
        return self
    
    def plot_flight_paths(self):
        """Create a comprehensive flight path map."""
        print("📊 Generating flight path visualization...")
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8))
        
        # Plot 1: All sensors overlaid
        if not self.df_owntracks.empty:
            ax1.plot(self.df_owntracks['lon'], self.df_owntracks['lat'], 
                    'o-', label='Ground Station (OwnTracks)', alpha=0.6, markersize=3, linewidth=1.5)
        
        if not self.df_dronetag.empty:
            ax1.plot(self.df_dronetag['lon'], self.df_dronetag['lat'], 
                    's-', label='Drone RemoteID (Dronetag)', alpha=0.6, markersize=4, linewidth=1.5)
        
        if not self.df_drone_osd.empty:
            osd_clean = self.df_drone_osd.dropna(subset=['lat', 'lon'])
            if not osd_clean.empty:
                ax1.plot(osd_clean['lon'], osd_clean['lat'], 
                        '^-', label='Drone OSD', alpha=0.6, markersize=4, linewidth=1.5)
        
        if not self.df_drone_state.empty:
            state_clean = self.df_drone_state.dropna(subset=['lat', 'lon'])
            if not state_clean.empty:
                ax1.plot(state_clean['lon'], state_clean['lat'], 
                        'x-', label='Drone State', alpha=0.4, markersize=3, linewidth=1)
        
        ax1.set_xlabel('Longitude')
        ax1.set_ylabel('Latitude')
        ax1.set_title('Multi-Sensor Flight Path Overlay', fontsize=14, fontweight='bold')
        ax1.legend(loc='best')
        ax1.grid(True, alpha=0.3)
        ax1.set_aspect('equal', adjustable='box')
        
        # Plot 2: Dronetag detailed path with operational state
        if not self.df_dronetag.empty:
            states = self.df_dronetag['operational_state'].unique()
            colors = plt.cm.Set2(np.linspace(0, 1, len(states)))
            
            for state, color in zip(states, colors):
                mask = self.df_dronetag['operational_state'] == state
                df_state = self.df_dronetag[mask]
                ax2.scatter(df_state['lon'], df_state['lat'], 
                           c=[color], label=f'{state}', alpha=0.7, s=30)
            
            ax2.set_xlabel('Longitude')
            ax2.set_ylabel('Latitude')
            ax2.set_title('Drone Path by Operational State', fontsize=14, fontweight='bold')
            ax2.legend(loc='best')
            ax2.grid(True, alpha=0.3)
            ax2.set_aspect('equal', adjustable='box')
        
        plt.tight_layout()
        output_path = os.path.join(self.output_dir, '01_flight_paths.png')
        plt.savefig(output_path, dpi=self.OUTPUT_DPI, bbox_inches='tight')
        print(f"  ✅ Saved: {output_path}")
        plt.close()
    
    def plot_altitude_profiles(self):
        """Plot altitude profiles over time."""
        print("📊 Generating altitude profiles...")
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 10))
        
        # Plot 1: All altitude sources
        ax = axes[0, 0]
        if not self.df_dronetag.empty:
            ax.plot(self.df_dronetag['mission_time_s'], self.df_dronetag['altitude_msl'], 
                   label='Dronetag MSL', alpha=0.7, linewidth=2)
            ax.plot(self.df_dronetag['mission_time_s'], self.df_dronetag['altitude_ato'], 
                   label='Dronetag ATO', alpha=0.7, linewidth=2)
        
        if not self.df_drone_osd.empty:
            osd_clean = self.df_drone_osd.dropna(subset=['height'])
            ax.plot(osd_clean['mission_time_s'], osd_clean['height'], 
                   label='Drone OSD Height', alpha=0.7, linewidth=1.5)
        
        if not self.df_drone_state.empty:
            state_clean = self.df_drone_state.dropna(subset=['height'])
            ax.plot(state_clean['mission_time_s'], state_clean['height'], 
                   label='Drone State Height', alpha=0.5, linewidth=1)
        
        ax.set_xlabel('Mission Time (seconds)')
        ax.set_ylabel('Altitude (meters)')
        ax.set_title('Altitude Profile - All Sources', fontweight='bold')
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)
        
        # Plot 2: Vertical speed
        ax = axes[0, 1]
        if not self.df_dronetag.empty:
            ax.plot(self.df_dronetag['mission_time_s'], self.df_dronetag['vertical_speed'], 
                   color='green', alpha=0.7, linewidth=2)
            ax.axhline(y=0, color='red', linestyle='--', alpha=0.5)
            ax.set_xlabel('Mission Time (seconds)')
            ax.set_ylabel('Vertical Speed (m/s)')
            ax.set_title('Vertical Speed Profile', fontweight='bold')
            ax.grid(True, alpha=0.3)
        
        # Plot 3: Altitude histogram
        ax = axes[1, 0]
        if not self.df_dronetag.empty:
            alt_data = self.df_dronetag['altitude_msl'].dropna()
            ax.hist(alt_data, bins=30, color='skyblue', alpha=0.7, edgecolor='black')
            ax.axvline(alt_data.mean(), color='red', linestyle='--', 
                      label=f'Mean: {alt_data.mean():.1f}m')
            ax.set_xlabel('Altitude MSL (meters)')
            ax.set_ylabel('Frequency')
            ax.set_title('Altitude Distribution', fontweight='bold')
            ax.legend()
            ax.grid(True, alpha=0.3)
        
        # Plot 4: Air pressure
        ax = axes[1, 1]
        if not self.df_dronetag.empty:
            pressure_data = self.df_dronetag.dropna(subset=['air_pressure'])
            if not pressure_data.empty:
                ax.plot(pressure_data['mission_time_s'], pressure_data['air_pressure'], 
                       color='purple', alpha=0.7, linewidth=2)
                ax.set_xlabel('Mission Time (seconds)')
                ax.set_ylabel('Air Pressure (hPa)')
                ax.set_title('Atmospheric Pressure', fontweight='bold')
                ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        output_path = os.path.join(self.output_dir, '02_altitude_profiles.png')
        plt.savefig(output_path, dpi=self.OUTPUT_DPI, bbox_inches='tight')
        print(f"  ✅ Saved: {output_path}")
        plt.close()
    
    def plot_speed_analysis(self):
        """Plot speed and velocity analysis."""
        print("📊 Generating speed analysis...")
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 10))
        
        # Plot 1: Horizontal speed (Dronetag)
        ax = axes[0, 0]
        if not self.df_dronetag.empty:
            speed_data = self.df_dronetag.dropna(subset=['horizontal_speed'])
            ax.plot(speed_data['mission_time_s'], speed_data['horizontal_speed'], 
                   color='blue', alpha=0.7, linewidth=2)
            ax.set_xlabel('Mission Time (seconds)')
            ax.set_ylabel('Horizontal Speed (m/s)')
            ax.set_title('Drone Horizontal Speed (RemoteID)', fontweight='bold')
            ax.grid(True, alpha=0.3)
        
        # Plot 2: Ground station speed
        ax = axes[0, 1]
        if not self.df_owntracks.empty:
            ax.plot(self.df_owntracks['mission_time_s'], self.df_owntracks['speed'], 
                   color='green', alpha=0.7, linewidth=2)
            ax.set_xlabel('Mission Time (seconds)')
            ax.set_ylabel('Speed (m/s)')
            ax.set_title('Ground Station Speed', fontweight='bold')
            ax.grid(True, alpha=0.3)
        
        # Plot 3: Speed histogram
        ax = axes[1, 0]
        if not self.df_dronetag.empty:
            speed_data = self.df_dronetag['horizontal_speed'].dropna()
            ax.hist(speed_data, bins=30, color='orange', alpha=0.7, edgecolor='black')
            ax.axvline(speed_data.mean(), color='red', linestyle='--', 
                      label=f'Mean: {speed_data.mean():.2f} m/s')
            ax.axvline(speed_data.max(), color='green', linestyle='--', 
                      label=f'Max: {speed_data.max():.2f} m/s')
            ax.set_xlabel('Horizontal Speed (m/s)')
            ax.set_ylabel('Frequency')
            ax.set_title('Drone Speed Distribution', fontweight='bold')
            ax.legend()
            ax.grid(True, alpha=0.3)
        
        # Plot 4: Heading analysis
        ax = axes[1, 1]
        if not self.df_dronetag.empty:
            heading_data = self.df_dronetag.dropna(subset=['heading'])
            if not heading_data.empty:
                ax.scatter(heading_data['mission_time_s'], heading_data['heading'], 
                          c=heading_data['horizontal_speed'], cmap='viridis', 
                          alpha=0.6, s=30)
                cbar = plt.colorbar(ax.collections[0], ax=ax)
                cbar.set_label('Speed (m/s)')
                ax.set_xlabel('Mission Time (seconds)')
                ax.set_ylabel('Heading (degrees)')
                ax.set_title('Heading vs Speed', fontweight='bold')
                ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        output_path = os.path.join(self.output_dir, '03_speed_analysis.png')
        plt.savefig(output_path, dpi=self.OUTPUT_DPI, bbox_inches='tight')
        print(f"  ✅ Saved: {output_path}")
        plt.close()
    
    def plot_battery_monitoring(self):
        """Plot battery levels over time."""
        print("📊 Generating battery monitoring...")
        
        fig, axes = plt.subplots(1, 2, figsize=(16, 6))
        
        # Plot 1: Drone battery
        ax = axes[0]
        if not self.df_drone_osd.empty:
            battery_data = self.df_drone_osd.dropna(subset=['battery'])
            if not battery_data.empty:
                ax.plot(battery_data['mission_time_s'], battery_data['battery'], 
                       color='red', linewidth=2, marker='o', markersize=3)
                ax.fill_between(battery_data['mission_time_s'], battery_data['battery'], 
                               alpha=0.3, color='red')
                ax.axhline(y=self.BATTERY_WARNING_THRESHOLD, color='orange', linestyle='--', 
                          label=f'Warning Level ({self.BATTERY_WARNING_THRESHOLD}%)', alpha=0.7)
                ax.set_xlabel('Mission Time (seconds)')
                ax.set_ylabel('Battery Level (%)')
                ax.set_title('Drone Battery Level', fontweight='bold')
                ax.legend()
                ax.grid(True, alpha=0.3)
                ax.set_ylim(0, 105)
        
        # Plot 2: Ground station battery
        ax = axes[1]
        if not self.df_owntracks.empty:
            battery_data = self.df_owntracks.dropna(subset=['battery'])
            if not battery_data.empty:
                ax.plot(battery_data['mission_time_s'], battery_data['battery'], 
                       color='blue', linewidth=2, marker='o', markersize=3)
                ax.fill_between(battery_data['mission_time_s'], battery_data['battery'], 
                               alpha=0.3, color='blue')
                ax.axhline(y=self.BATTERY_WARNING_THRESHOLD, color='orange', linestyle='--', 
                          label=f'Warning Level ({self.BATTERY_WARNING_THRESHOLD}%)', alpha=0.7)
                ax.set_xlabel('Mission Time (seconds)')
                ax.set_ylabel('Battery Level (%)')
                ax.set_title('Ground Station Battery Level', fontweight='bold')
                ax.legend()
                ax.grid(True, alpha=0.3)
                ax.set_ylim(0, 105)
        
        plt.tight_layout()
        output_path = os.path.join(self.output_dir, '04_battery_monitoring.png')
        plt.savefig(output_path, dpi=self.OUTPUT_DPI, bbox_inches='tight')
        print(f"  ✅ Saved: {output_path}")
        plt.close()
    
    def plot_link_quality(self):
        """Plot link quality and latency metrics."""
        print("📊 Generating link quality analysis...")
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 10))
        
        # Plot 1: Position accuracy
        ax = axes[0, 0]
        if not self.df_dronetag.empty:
            acc_data = self.df_dronetag.dropna(subset=['accuracy'])
            if not acc_data.empty:
                ax.plot(acc_data['mission_time_s'], acc_data['accuracy'], 
                       color='green', linewidth=2)
                ax.set_xlabel('Mission Time (seconds)')
                ax.set_ylabel('Position Accuracy (meters)')
                ax.set_title('Dronetag Position Accuracy', fontweight='bold')
                ax.grid(True, alpha=0.3)
        
        # Plot 2: Ground station accuracy
        ax = axes[0, 1]
        if not self.df_owntracks.empty:
            acc_data = self.df_owntracks.dropna(subset=['accuracy'])
            if not acc_data.empty:
                ax.plot(acc_data['mission_time_s'], acc_data['accuracy'], 
                       color='purple', linewidth=2)
                ax.set_xlabel('Mission Time (seconds)')
                ax.set_ylabel('Position Accuracy (meters)')
                ax.set_title('Ground Station Position Accuracy', fontweight='bold')
                ax.grid(True, alpha=0.3)
        
        # Plot 3: Wireless link state
        ax = axes[1, 0]
        if not self.df_drone_osd.empty:
            link_data = self.df_drone_osd.dropna(subset=['wireless_link_state'])
            if not link_data.empty:
                ax.plot(link_data['mission_time_s'], link_data['wireless_link_state'], 
                       'o-', color='blue', linewidth=2, markersize=4)
                ax.set_xlabel('Mission Time (seconds)')
                ax.set_ylabel('Link State')
                ax.set_title('Drone Wireless Link State', fontweight='bold')
                ax.grid(True, alpha=0.3)
        
        # Plot 4: Data rate by topic
        ax = axes[1, 1]
        topic_counts = {}
        for record in self.records:
            topic = record.get('topic', 'unknown')
            if 'dronetag' in topic or 'owntracks' in topic or 'osd' in topic:
                topic_short = topic.split('/')[-1] if '/' in topic else topic
                topic_counts[topic_short] = topic_counts.get(topic_short, 0) + 1
        
        if topic_counts:
            topics = list(topic_counts.keys())
            counts = list(topic_counts.values())
            colors = plt.cm.Set3(np.linspace(0, 1, len(topics)))
            ax.bar(range(len(topics)), counts, color=colors, alpha=0.7, edgecolor='black')
            ax.set_xticks(range(len(topics)))
            ax.set_xticklabels(topics, rotation=45, ha='right')
            ax.set_ylabel('Number of Messages')
            ax.set_title('Message Count by Topic', fontweight='bold')
            ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        output_path = os.path.join(self.output_dir, '05_link_quality.png')
        plt.savefig(output_path, dpi=self.OUTPUT_DPI, bbox_inches='tight')
        print(f"  ✅ Saved: {output_path}")
        plt.close()
    
    def plot_temporal_distribution(self):
        """Plot temporal distribution of events."""
        print("📊 Generating temporal distribution...")
        
        fig, axes = plt.subplots(2, 1, figsize=(16, 10))
        
        # Plot 1: Message rate over time
        ax = axes[0]
        all_timestamps = [r['ts'] for r in self.records if 'ts' in r]
        if all_timestamps:
            all_timestamps.sort()
            min_ts = min(all_timestamps)
            relative_times = [(ts - min_ts) for ts in all_timestamps]
            
            # Create bins for message rate
            bin_size = self.TEMPORAL_BIN_SIZE_SECONDS
            bins = np.arange(0, max(relative_times) + bin_size, bin_size)
            hist, edges = np.histogram(relative_times, bins=bins)
            centers = (edges[:-1] + edges[1:]) / 2
            
            ax.plot(centers, hist, color='blue', linewidth=2)
            ax.fill_between(centers, hist, alpha=0.3, color='blue')
            ax.set_xlabel('Mission Time (seconds)')
            ax.set_ylabel('Messages per 10s')
            ax.set_title('Message Rate Over Time', fontweight='bold')
            ax.grid(True, alpha=0.3)
        
        # Plot 2: Cumulative messages by source
        ax = axes[1]
        topic_times = {}
        for record in self.records:
            topic = record.get('topic', 'unknown')
            ts = record.get('ts', 0)
            
            # Simplify topic names
            if 'owntracks' in topic:
                topic_key = 'Ground Station'
            elif topic == 'dronetag':
                topic_key = 'RemoteID'
            elif 'osd' in topic:
                topic_key = 'Drone OSD'
            elif 'state' in topic:
                topic_key = 'Drone State'
            else:
                continue
            
            if topic_key not in topic_times:
                topic_times[topic_key] = []
            topic_times[topic_key].append(ts)
        
        colors = plt.cm.Set2(np.linspace(0, 1, len(topic_times)))
        for (topic_key, timestamps), color in zip(topic_times.items(), colors):
            timestamps.sort()
            if timestamps:
                min_ts = min([t for ts_list in topic_times.values() for t in ts_list])
                relative_ts = [(t - min_ts) for t in timestamps]
                cumulative = range(1, len(relative_ts) + 1)
                ax.plot(relative_ts, cumulative, label=topic_key, linewidth=2, color=color)
        
        ax.set_xlabel('Mission Time (seconds)')
        ax.set_ylabel('Cumulative Messages')
        ax.set_title('Cumulative Messages by Source', fontweight='bold')
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        output_path = os.path.join(self.output_dir, '06_temporal_distribution.png')
        plt.savefig(output_path, dpi=self.OUTPUT_DPI, bbox_inches='tight')
        print(f"  ✅ Saved: {output_path}")
        plt.close()
    
    def plot_gnss_accuracy_comparison(self):
        """Plot GNSS accuracy comparison between RTK (Autel) and GPS (Dronetag)."""
        print("📊 Generating GNSS accuracy comparison...")
        
        if self.df_drone_rtk.empty or self.df_dronetag.empty:
            print("  ⚠️  Insufficient data for GNSS accuracy comparison")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 10))
        
        # Plot 1: RTK Fix Status over time
        ax = axes[0, 0]
        if not self.df_drone_rtk.empty:
            rtk_data = self.df_drone_rtk.dropna(subset=['rtk_status'])
            if not rtk_data.empty:
                # Map status to numeric for plotting
                status_map = {'GPS': 0, 'RTK_FLOAT': 1, 'RTK_FIXED': 2}
                rtk_data_plot = rtk_data.copy()
                rtk_data_plot['status_num'] = rtk_data_plot['rtk_status'].map(status_map)
                
                # Create color-coded scatter plot
                colors = {'GPS': 'red', 'RTK_FLOAT': 'orange', 'RTK_FIXED': 'green'}
                for status, color in colors.items():
                    mask = rtk_data_plot['rtk_status'] == status
                    data = rtk_data_plot[mask]
                    if not data.empty:
                        ax.scatter(data['mission_time_s'], data['status_num'], 
                                 c=color, label=status, alpha=0.6, s=20)
                
                ax.set_xlabel('Mission Time (seconds)')
                ax.set_ylabel('Position Fix Status')
                ax.set_yticks([0, 1, 2])
                ax.set_yticklabels(['GPS', 'RTK Float', 'RTK Fixed'])
                ax.set_title('Autel Drone RTK Fix Status Over Time', fontweight='bold')
                ax.legend(loc='best')
                ax.grid(True, alpha=0.3)
        
        # Plot 2: Satellite count comparison
        ax = axes[0, 1]
        if not self.df_drone_rtk.empty:
            rtk_sats = self.df_drone_rtk.dropna(subset=['rtk_number'])
            gps_sats = self.df_drone_rtk.dropna(subset=['gps_number'])
            
            if not rtk_sats.empty:
                ax.plot(rtk_sats['mission_time_s'], rtk_sats['rtk_number'], 
                       label='RTK Satellites', color='green', linewidth=2, alpha=0.7)
            if not gps_sats.empty:
                ax.plot(gps_sats['mission_time_s'], gps_sats['gps_number'], 
                       label='GPS Satellites', color='blue', linewidth=2, alpha=0.7)
            
            ax.set_xlabel('Mission Time (seconds)')
            ax.set_ylabel('Number of Satellites')
            ax.set_title('Satellite Count: Autel Drone', fontweight='bold')
            ax.legend(loc='best')
            ax.grid(True, alpha=0.3)
        
        # Plot 3: Position accuracy comparison (Autel RTK vs Dronetag GPS)
        ax = axes[1, 0]
        
        # Merge Autel RTK and Dronetag data by timestamp
        if not self.df_drone_rtk.empty and not self.df_dronetag.empty:
            autel_clean = self.df_drone_rtk[['timestamp', 'rtk_lat', 'rtk_lon']].dropna()
            dronetag_clean = self.df_dronetag[['timestamp', 'lat', 'lon']].dropna()
            
            if not autel_clean.empty and not dronetag_clean.empty:
                # Merge on timestamp (nearest neighbor within 2 seconds)
                merged = pd.merge_asof(autel_clean.sort_values('timestamp'), 
                                      dronetag_clean.sort_values('timestamp'), 
                                      on='timestamp', direction='nearest', tolerance=2.0)
                merged = merged.dropna(subset=['rtk_lat', 'lat'])
                
                if not merged.empty:
                    # Calculate position error
                    lat_scale = 111320  # meters per degree latitude
                    lon_scale = 111320 * np.cos(np.deg2rad(merged['rtk_lat'].mean()))
                    
                    merged['delta_lat_m'] = (merged['rtk_lat'] - merged['lat']) * lat_scale
                    merged['delta_lon_m'] = (merged['rtk_lon'] - merged['lon']) * lon_scale
                    merged['position_error'] = np.sqrt(merged['delta_lat_m']**2 + merged['delta_lon_m']**2)
                    merged['mission_time_s'] = merged['timestamp'] - merged['timestamp'].min()
                    
                    ax.plot(merged['mission_time_s'], merged['position_error'], 
                           color='purple', linewidth=2, alpha=0.7)
                    ax.axhline(y=merged['position_error'].mean(), color='red', 
                              linestyle='--', label=f'Mean: {merged['position_error'].mean():.2f}m')
                    ax.set_xlabel('Mission Time (seconds)')
                    ax.set_ylabel('Position Difference (meters)')
                    ax.set_title('Position Difference: Autel RTK vs Dronetag GPS', fontweight='bold')
                    ax.legend()
                    ax.grid(True, alpha=0.3)
        
        # Plot 4: Position accuracy histogram
        ax = axes[1, 1]
        
        # Plot Dronetag GPS accuracy
        if not self.df_dronetag.empty:
            dronetag_acc = self.df_dronetag['accuracy'].dropna()
            if not dronetag_acc.empty:
                ax.hist(dronetag_acc, bins=30, alpha=0.6, color='orange', 
                       label=f'Dronetag GPS (mean: {dronetag_acc.mean():.2f}m)', 
                       edgecolor='black')
        
        # Note: Autel RTK doesn't report accuracy in the same way
        ax.set_xlabel('Position Accuracy (meters)')
        ax.set_ylabel('Frequency')
        ax.set_title('GNSS Accuracy Distribution', fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        output_path = os.path.join(self.output_dir, '08_gnss_accuracy_comparison.png')
        plt.savefig(output_path, dpi=self.OUTPUT_DPI, bbox_inches='tight')
        print(f"  ✅ Saved: {output_path}")
        plt.close()
    
    def plot_latency_analysis(self):
        """Plot latency analysis comparing different data sources."""
        print("📊 Generating latency analysis...")
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 10))
        
        # Plot 1: Ground Station Link Latency
        ax = axes[0, 0]
        if not self.df_owntracks.empty and 'link_latency' in self.df_owntracks.columns:
            latency_data = self.df_owntracks.dropna(subset=['link_latency'])
            if not latency_data.empty:
                ax.plot(latency_data['mission_time_s'], latency_data['link_latency'], 
                       color='blue', linewidth=2, alpha=0.7)
                ax.axhline(y=latency_data['link_latency'].mean(), color='red', 
                          linestyle='--', label=f'Mean: {latency_data["link_latency"].mean():.2f}s')
                ax.set_xlabel('Mission Time (seconds)')
                ax.set_ylabel('Link Latency (seconds)')
                ax.set_title('Ground Station Link Latency', fontweight='bold')
                ax.legend()
                ax.grid(True, alpha=0.3)
        
        # Plot 2: Latency Distribution
        ax = axes[0, 1]
        if not self.df_owntracks.empty and 'link_latency' in self.df_owntracks.columns:
            latency_data = self.df_owntracks['link_latency'].dropna()
            if not latency_data.empty:
                ax.hist(latency_data, bins=30, color='skyblue', alpha=0.7, edgecolor='black')
                ax.axvline(latency_data.mean(), color='red', linestyle='--', 
                          label=f'Mean: {latency_data.mean():.2f}s')
                ax.axvline(latency_data.median(), color='green', linestyle='--', 
                          label=f'Median: {latency_data.median():.2f}s')
                ax.set_xlabel('Link Latency (seconds)')
                ax.set_ylabel('Frequency')
                ax.set_title('Ground Station Latency Distribution', fontweight='bold')
                ax.legend()
                ax.grid(True, alpha=0.3)
        
        # Plot 3: Latency vs Position Accuracy (Ground Station)
        ax = axes[1, 0]
        if not self.df_owntracks.empty:
            owntracks_clean = self.df_owntracks.dropna(subset=['link_latency', 'accuracy'])
            if not owntracks_clean.empty:
                scatter = ax.scatter(owntracks_clean['link_latency'], 
                                    owntracks_clean['accuracy'], 
                                    c=owntracks_clean['mission_time_s'], 
                                    cmap='viridis', alpha=0.6, s=30)
                cbar = plt.colorbar(scatter, ax=ax)
                cbar.set_label('Mission Time (s)')
                ax.set_xlabel('Link Latency (seconds)')
                ax.set_ylabel('Position Accuracy (meters)')
                ax.set_title('Latency vs Accuracy: Ground Station', fontweight='bold')
                ax.grid(True, alpha=0.3)
        
        # Plot 4: Data rate and latency metrics
        ax = axes[1, 1]
        
        # Calculate message intervals for different sources
        message_stats = []
        
        if not self.df_owntracks.empty:
            intervals = self.df_owntracks['timestamp'].diff().dropna()
            if not intervals.empty:
                message_stats.append({
                    'source': 'Ground Station',
                    'mean_interval': intervals.mean(),
                    'std_interval': intervals.std()
                })
        
        if not self.df_dronetag.empty:
            intervals = self.df_dronetag['timestamp'].diff().dropna()
            if not intervals.empty:
                message_stats.append({
                    'source': 'Dronetag',
                    'mean_interval': intervals.mean(),
                    'std_interval': intervals.std()
                })
        
        if not self.df_drone_rtk.empty:
            intervals = self.df_drone_rtk['timestamp'].diff().dropna()
            if not intervals.empty:
                message_stats.append({
                    'source': 'Autel RTK',
                    'mean_interval': intervals.mean(),
                    'std_interval': intervals.std()
                })
        
        if message_stats:
            sources = [s['source'] for s in message_stats]
            mean_intervals = [s['mean_interval'] for s in message_stats]
            std_intervals = [s['std_interval'] for s in message_stats]
            
            x = np.arange(len(sources))
            width = 0.35
            
            bars = ax.bar(x, mean_intervals, width, yerr=std_intervals, 
                         alpha=0.7, capsize=5, color=['blue', 'orange', 'green'])
            
            ax.set_xlabel('Data Source')
            ax.set_ylabel('Mean Message Interval (seconds)')
            ax.set_title('Data Rate Comparison (Message Interval)', fontweight='bold')
            ax.set_xticks(x)
            ax.set_xticklabels(sources, rotation=15, ha='right')
            ax.grid(True, alpha=0.3, axis='y')
            
            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.2f}s',
                       ha='center', va='bottom', fontsize=10)
        
        plt.tight_layout()
        output_path = os.path.join(self.output_dir, '09_latency_analysis.png')
        plt.savefig(output_path, dpi=self.OUTPUT_DPI, bbox_inches='tight')
        print(f"  ✅ Saved: {output_path}")
        plt.close()
    
    def generate_summary_statistics(self):
        """Generate and save summary statistics."""
        print("📊 Generating summary statistics...")
        
        fig = plt.figure(figsize=(16, 12))
        gs = fig.add_gridspec(4, 2, hspace=0.4, wspace=0.3)
        
        # Mission Overview
        ax = fig.add_subplot(gs[0, :])
        ax.axis('off')
        
        mission_start = min([r['ts'] for r in self.records if 'ts' in r])
        mission_end = max([r['ts'] for r in self.records if 'ts' in r])
        mission_duration = mission_end - mission_start
        
        summary_text = f"""
        MISSION SUMMARY STATISTICS
        {'='*80}
        
        Mission Duration: {mission_duration:.1f} seconds ({mission_duration/60:.1f} minutes)
        Total Records: {len(self.records)}
        Start Time: {datetime.fromtimestamp(mission_start).strftime('%Y-%m-%d %H:%M:%S')}
        End Time: {datetime.fromtimestamp(mission_end).strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        ax.text(0.05, 0.95, summary_text, transform=ax.transAxes, 
               fontsize=12, verticalalignment='top', fontfamily='monospace',
               bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
        
        # Dronetag Statistics
        if not self.df_dronetag.empty:
            ax = fig.add_subplot(gs[1, 0])
            ax.axis('off')
            
            speed_data = self.df_dronetag['horizontal_speed'].dropna()
            alt_data = self.df_dronetag['altitude_msl'].dropna()
            
            stats_text = f"""
            DRONETAG (Remote ID) STATISTICS
            {'-'*40}
            Records: {len(self.df_dronetag)}
            
            Horizontal Speed:
              Mean: {speed_data.mean():.2f} m/s
              Max: {speed_data.max():.2f} m/s
              Std: {speed_data.std():.2f} m/s
            
            Altitude (MSL):
              Mean: {alt_data.mean():.2f} m
              Max: {alt_data.max():.2f} m
              Min: {alt_data.min():.2f} m
              Range: {alt_data.max() - alt_data.min():.2f} m
            """
            
            ax.text(0.05, 0.95, stats_text, transform=ax.transAxes, 
                   fontsize=10, verticalalignment='top', fontfamily='monospace',
                   bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.5))
        
        # Ground Station Statistics
        if not self.df_owntracks.empty:
            ax = fig.add_subplot(gs[1, 1])
            ax.axis('off')
            
            speed_data = self.df_owntracks['speed'].dropna()
            battery_data = self.df_owntracks['battery'].dropna()
            
            stats_text = f"""
            GROUND STATION STATISTICS
            {'-'*40}
            Records: {len(self.df_owntracks)}
            
            Speed:
              Mean: {speed_data.mean():.2f} m/s
              Max: {speed_data.max():.2f} m/s
            
            Battery:"""
            
            if not battery_data.empty:
                stats_text += f"""
              Start: {battery_data.iloc[0]:.0f}%
              End: {battery_data.iloc[-1]:.0f}%
              Drop: {battery_data.iloc[0] - battery_data.iloc[-1]:.0f}%"""
            else:
                stats_text += """
              No battery data available"""
            
            ax.text(0.05, 0.95, stats_text, transform=ax.transAxes, 
                   fontsize=10, verticalalignment='top', fontfamily='monospace',
                   bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.5))
        
        # Drone OSD Statistics
        if not self.df_drone_osd.empty:
            ax = fig.add_subplot(gs[2, 0])
            ax.axis('off')
            
            battery_data = self.df_drone_osd['battery'].dropna()
            height_data = self.df_drone_osd['height'].dropna()
            
            stats_text = f"""
            DRONE OSD STATISTICS
            {'-'*40}
            Records: {len(self.df_drone_osd)}
            
            Height:
              Mean: {height_data.mean():.2f} m
              Max: {height_data.max():.2f} m
            
            Battery:"""
            
            if not battery_data.empty:
                stats_text += f"""
              Start: {battery_data.iloc[0]:.0f}%
              End: {battery_data.iloc[-1]:.0f}%
              Drop: {battery_data.iloc[0] - battery_data.iloc[-1]:.0f}%"""
            else:
                stats_text += """
              No battery data available"""
            
            ax.text(0.05, 0.95, stats_text, transform=ax.transAxes, 
                   fontsize=10, verticalalignment='top', fontfamily='monospace',
                   bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.5))
        
        # Data Quality Metrics
        ax = fig.add_subplot(gs[2, 1])
        ax.axis('off')
        
        # Count records by topic category
        topic_stats = {}
        for record in self.records:
            topic = record.get('topic', 'unknown')
            if 'owntracks' in topic:
                key = 'Ground Station'
            elif topic == 'dronetag':
                key = 'RemoteID'
            elif 'osd' in topic:
                key = 'Drone OSD'
            elif 'state' in topic:
                key = 'Drone State'
            elif 'events' in topic:
                key = 'Events'
            else:
                key = 'Other'
            topic_stats[key] = topic_stats.get(key, 0) + 1
        
        stats_text = "DATA SOURCE DISTRIBUTION\n" + "-"*40 + "\n"
        for topic, count in sorted(topic_stats.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(self.records)) * 100
            stats_text += f"{topic:20s}: {count:4d} ({percentage:5.1f}%)\n"
        
        ax.text(0.05, 0.95, stats_text, transform=ax.transAxes, 
               fontsize=10, verticalalignment='top', fontfamily='monospace',
               bbox=dict(boxstyle='round', facecolor='lavender', alpha=0.5))
        
        # Operational State Distribution
        if not self.df_dronetag.empty and 'operational_state' in self.df_dronetag.columns:
            ax = fig.add_subplot(gs[3, :])
            
            state_counts = self.df_dronetag['operational_state'].value_counts()
            colors = plt.cm.Set3(np.linspace(0, 1, len(state_counts)))
            
            wedges, texts, autotexts = ax.pie(state_counts.values, labels=state_counts.index,
                                               autopct='%1.1f%%', colors=colors, startangle=90)
            
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
            
            ax.set_title('Drone Operational State Distribution', fontweight='bold', fontsize=12)
        
        plt.tight_layout()
        output_path = os.path.join(self.output_dir, '07_summary_statistics.png')
        plt.savefig(output_path, dpi=self.OUTPUT_DPI, bbox_inches='tight')
        print(f"  ✅ Saved: {output_path}")
        plt.close()
        
        # Also save as CSV
        csv_path = os.path.join(self.output_dir, 'summary_statistics.csv')
        with open(csv_path, 'w') as f:
            f.write("Metric,Value\n")
            f.write(f"Mission Duration (seconds),{mission_duration:.1f}\n")
            f.write(f"Total Records,{len(self.records)}\n")
            f.write(f"Start Time,{datetime.fromtimestamp(mission_start).strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"End Time,{datetime.fromtimestamp(mission_end).strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            if not self.df_dronetag.empty:
                speed_data = self.df_dronetag['horizontal_speed'].dropna()
                alt_data = self.df_dronetag['altitude_msl'].dropna()
                f.write(f"\nDronetag Mean Speed (m/s),{speed_data.mean():.2f}\n")
                f.write(f"Dronetag Max Speed (m/s),{speed_data.max():.2f}\n")
                f.write(f"Dronetag Mean Altitude (m),{alt_data.mean():.2f}\n")
                f.write(f"Dronetag Max Altitude (m),{alt_data.max():.2f}\n")
        
        print(f"  ✅ Saved: {csv_path}")
    
    def run_analysis(self):
        """Run complete EDA analysis."""
        print("\n" + "="*80)
        print("🦅 SECURINGSKIES MISSION EDA ANALYSIS")
        print("="*80 + "\n")
        
        self.load_data()
        self.parse_data()
        
        print("\n📊 Generating visualizations...\n")
        
        self.plot_flight_paths()
        self.plot_altitude_profiles()
        self.plot_speed_analysis()
        self.plot_battery_monitoring()
        self.plot_link_quality()
        self.plot_temporal_distribution()
        self.plot_gnss_accuracy_comparison()  # New: GNSS accuracy analysis
        self.plot_latency_analysis()  # New: Latency analysis
        self.generate_summary_statistics()
        
        print("\n" + "="*80)
        print(f"✅ ANALYSIS COMPLETE! All plots saved to: {self.output_dir}")
        print("="*80 + "\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Exploratory Data Analysis for SecuringSkies Mission Data'
    )
    parser.add_argument(
        '--input', 
        type=str, 
        default='golden_datasets/mission_20260127_172522.jsonl',
        help='Path to input JSONL file'
    )
    parser.add_argument(
        '--output', 
        type=str, 
        default='docs/eda_plots',
        help='Output directory for plots'
    )
    
    args = parser.parse_args()
    
    analyzer = MissionDataAnalyzer(args.input, args.output)
    analyzer.run_analysis()


if __name__ == '__main__':
    main()
