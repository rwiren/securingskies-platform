"""
Data Source Comparison Analysis
Version: 1.0.0
Author: SecuringSkies Data Science
Description: Compare MQTT telemetry data with raw flight data files to highlight
             differences in data richness, temporal coverage, and data quality.

Usage:
    python labs/compare_data_sources.py [--mqtt <path>] [--raw-dir <path>]
"""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os
import argparse
from pathlib import Path

# Set style
sns.set_style('whitegrid')
plt.rcParams['figure.figsize'] = (16, 10)
plt.rcParams['figure.dpi'] = 100


class DataSourceComparator:
    """Compares multiple data sources from the same flight session."""
    
    OUTPUT_DPI = 150
    
    def __init__(self, mqtt_path, raw_dir, output_dir='docs/data_comparison'):
        """
        Initialize the comparator.
        
        Args:
            mqtt_path: Path to MQTT JSONL file
            raw_dir: Directory containing raw data files
            output_dir: Directory to save output plots and reports
        """
        self.mqtt_path = mqtt_path
        self.raw_dir = Path(raw_dir)
        self.output_dir = output_dir
        
        # Data containers
        self.mqtt_data = None
        self.airdata_df = None
        self.dronetag_df = None
        self.flight_metadata = None
        
        # Analysis results
        self.comparison_results = {}
        
        os.makedirs(output_dir, exist_ok=True)
    
    def load_mqtt_data(self):
        """Load MQTT telemetry data."""
        print("📂 Loading MQTT data...")
        
        records = []
        with open(self.mqtt_path, 'r') as f:
            for line in f:
                try:
                    records.append(json.loads(line))
                except:
                    pass
        
        # Analyze by topic
        topics = {}
        for r in records:
            topic = r.get('topic', 'unknown')
            if topic not in topics:
                topics[topic] = {'count': 0, 'fields': set()}
            topics[topic]['count'] += 1
            
            # Extract field names
            data = r.get('data', {})
            topics[topic]['fields'].update(data.keys())
        
        self.mqtt_data = {
            'records': records,
            'total_count': len(records),
            'duration': records[-1]['ts'] - records[0]['ts'] if records else 0,
            'topics': topics,
            'start_time': records[0]['ts'] if records else None,
            'end_time': records[-1]['ts'] if records else None
        }
        
        print(f"  ✅ Loaded {len(records)} MQTT records from {len(topics)} topics")
        return self
    
    def load_airdata_csv(self):
        """Load Airdata CSV files."""
        print("📂 Loading Airdata CSV files...")
        
        airdata_files = list(self.raw_dir.glob("*-Flight-Airdata.csv"))
        
        if not airdata_files:
            print("  ⚠️  No Airdata CSV files found")
            return self
        
        dfs = []
        total_records = 0
        
        for file in airdata_files:
            try:
                df = pd.read_csv(file)
                dfs.append(df)
                total_records += len(df)
                print(f"  • {file.name}: {len(df)} records, {len(df.columns)} fields")
            except Exception as e:
                print(f"  ⚠️  Error loading {file.name}: {e}")
        
        if dfs:
            self.airdata_df = pd.concat(dfs, ignore_index=True)
            self.airdata_df['datetime'] = pd.to_datetime(self.airdata_df['datetime(utc)'])
            
            print(f"  ✅ Total Airdata records: {total_records}")
        
        return self
    
    def load_dronetag_exports(self):
        """Load Dronetag export files."""
        print("📂 Loading Dronetag export files...")
        
        # Load CSV files
        csv_files = list(self.raw_dir.glob("flight_export_*.csv"))
        json_files = list(self.raw_dir.glob("flight_export_*.json"))
        
        dfs = []
        json_records = []
        
        for file in csv_files:
            try:
                df = pd.read_csv(file)
                dfs.append(df)
                print(f"  • {file.name}: {len(df)} records, {len(df.columns)} fields")
            except Exception as e:
                print(f"  ⚠️  Error loading {file.name}: {e}")
        
        for file in json_files:
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                    json_records.extend(data)
                print(f"  • {file.name}: {len(data)} records")
            except Exception as e:
                print(f"  ⚠️  Error loading {file.name}: {e}")
        
        if dfs:
            self.dronetag_df = pd.concat(dfs, ignore_index=True)
            self.dronetag_df['datetime'] = pd.to_datetime(self.dronetag_df['time'])
            print(f"  ✅ Total Dronetag CSV records: {len(self.dronetag_df)}")
        
        if json_records:
            print(f"  ✅ Total Dronetag JSON records: {len(json_records)}")
        
        return self
    
    def analyze_data_richness(self):
        """Analyze and compare data richness across sources."""
        print("\n📊 Analyzing data richness...")
        
        results = {}
        
        # MQTT Analysis
        if self.mqtt_data:
            mqtt_topics = self.mqtt_data['topics']
            total_unique_fields = set()
            
            for topic, info in mqtt_topics.items():
                total_unique_fields.update(info['fields'])
            
            results['mqtt'] = {
                'total_records': self.mqtt_data['total_count'],
                'duration_seconds': self.mqtt_data['duration'],
                'update_rate_hz': self.mqtt_data['total_count'] / self.mqtt_data['duration'] if self.mqtt_data['duration'] > 0 else 0,
                'topics': len(mqtt_topics),
                'unique_fields': len(total_unique_fields),
                'fields_by_topic': {topic: len(info['fields']) for topic, info in mqtt_topics.items()}
            }
        
        # Airdata Analysis
        if self.airdata_df is not None and not self.airdata_df.empty:
            duration = (self.airdata_df['datetime'].max() - self.airdata_df['datetime'].min()).total_seconds()
            results['airdata'] = {
                'total_records': len(self.airdata_df),
                'duration_seconds': duration,
                'update_rate_hz': len(self.airdata_df) / duration if duration > 0 else 0,
                'fields': len(self.airdata_df.columns),
                'field_names': list(self.airdata_df.columns)
            }
        
        # Dronetag Analysis
        if self.dronetag_df is not None and not self.dronetag_df.empty:
            duration = (self.dronetag_df['datetime'].max() - self.dronetag_df['datetime'].min()).total_seconds()
            results['dronetag'] = {
                'total_records': len(self.dronetag_df),
                'duration_seconds': duration,
                'update_rate_hz': len(self.dronetag_df) / duration if duration > 0 else 0,
                'fields': len(self.dronetag_df.columns),
                'field_names': list(self.dronetag_df.columns)
            }
        
        self.comparison_results = results
        
        # Print summary
        print("\n" + "="*80)
        print("DATA RICHNESS COMPARISON")
        print("="*80)
        
        for source, data in results.items():
            print(f"\n{source.upper()}:")
            print(f"  Total Records: {data['total_records']:,}")
            print(f"  Duration: {data['duration_seconds']:.1f}s ({data['duration_seconds']/60:.1f} min)")
            print(f"  Update Rate: {data['update_rate_hz']:.2f} Hz")
            
            if source == 'mqtt':
                print(f"  Topics: {data['topics']}")
                print(f"  Unique Fields: {data['unique_fields']}")
            else:
                print(f"  Fields: {data['fields']}")
        
        return self
    
    def plot_comparison(self):
        """Create comprehensive comparison visualizations."""
        print("\n📊 Generating comparison visualizations...")
        
        fig = plt.figure(figsize=(18, 12))
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        
        # Plot 1: Record counts
        ax = fig.add_subplot(gs[0, 0])
        sources = []
        counts = []
        
        if 'mqtt' in self.comparison_results:
            sources.append('MQTT\n(All Topics)')
            counts.append(self.comparison_results['mqtt']['total_records'])
        
        if 'airdata' in self.comparison_results:
            sources.append('Airdata\n(Autel)')
            counts.append(self.comparison_results['airdata']['total_records'])
        
        if 'dronetag' in self.comparison_results:
            sources.append('Dronetag\n(Remote ID)')
            counts.append(self.comparison_results['dronetag']['total_records'])
        
        colors = ['#3498db', '#e74c3c', '#2ecc71']
        bars = ax.bar(sources, counts, color=colors[:len(sources)], alpha=0.7, edgecolor='black')
        ax.set_ylabel('Total Records')
        ax.set_title('Record Count by Source', fontweight='bold', fontsize=12)
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add value labels
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height):,}',
                   ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        # Plot 2: Update rates
        ax = fig.add_subplot(gs[0, 1])
        sources_hz = []
        rates = []
        
        if 'mqtt' in self.comparison_results:
            sources_hz.append('MQTT')
            rates.append(self.comparison_results['mqtt']['update_rate_hz'])
        
        if 'airdata' in self.comparison_results:
            sources_hz.append('Airdata')
            rates.append(self.comparison_results['airdata']['update_rate_hz'])
        
        if 'dronetag' in self.comparison_results:
            sources_hz.append('Dronetag')
            rates.append(self.comparison_results['dronetag']['update_rate_hz'])
        
        bars = ax.bar(sources_hz, rates, color=colors[:len(sources_hz)], alpha=0.7, edgecolor='black')
        ax.set_ylabel('Update Rate (Hz)')
        ax.set_title('Data Update Rate Comparison', fontweight='bold', fontsize=12)
        ax.grid(True, alpha=0.3, axis='y')
        
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.2f} Hz',
                   ha='center', va='bottom', fontsize=9)
        
        # Plot 3: Field count comparison
        ax = fig.add_subplot(gs[0, 2])
        sources_fields = []
        field_counts = []
        
        if 'mqtt' in self.comparison_results:
            sources_fields.append('MQTT')
            field_counts.append(self.comparison_results['mqtt']['unique_fields'])
        
        if 'airdata' in self.comparison_results:
            sources_fields.append('Airdata')
            field_counts.append(self.comparison_results['airdata']['fields'])
        
        if 'dronetag' in self.comparison_results:
            sources_fields.append('Dronetag')
            field_counts.append(self.comparison_results['dronetag']['fields'])
        
        bars = ax.bar(sources_fields, field_counts, color=colors[:len(sources_fields)], alpha=0.7, edgecolor='black')
        ax.set_ylabel('Number of Fields')
        ax.set_title('Data Field Count', fontweight='bold', fontsize=12)
        ax.grid(True, alpha=0.3, axis='y')
        
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height)}',
                   ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        # Plot 4: MQTT topic breakdown
        if 'mqtt' in self.comparison_results:
            ax = fig.add_subplot(gs[1, :])
            
            topics_data = self.mqtt_data['topics']
            topic_names = []
            topic_counts = []
            
            # Sort by count
            sorted_topics = sorted(topics_data.items(), key=lambda x: x[1]['count'], reverse=True)
            
            for topic, info in sorted_topics[:10]:  # Top 10
                # Shorten topic names
                short_name = topic.split('/')[-1] if '/' in topic else topic
                topic_names.append(short_name)
                topic_counts.append(info['count'])
            
            colors_topics = plt.cm.Set3(np.linspace(0, 1, len(topic_names)))
            bars = ax.barh(topic_names, topic_counts, color=colors_topics, alpha=0.7, edgecolor='black')
            ax.set_xlabel('Record Count')
            ax.set_title('MQTT Topic Distribution (Top 10)', fontweight='bold', fontsize=12)
            ax.grid(True, alpha=0.3, axis='x')
            
            for bar in bars:
                width = bar.get_width()
                ax.text(width, bar.get_y() + bar.get_height()/2.,
                       f' {int(width):,}',
                       ha='left', va='center', fontsize=9)
        
        # Plot 5: Temporal coverage comparison
        ax = fig.add_subplot(gs[2, :])
        
        timeline_data = []
        
        if 'mqtt' in self.comparison_results:
            start = self.mqtt_data['start_time']
            end = self.mqtt_data['end_time']
            timeline_data.append({
                'source': 'MQTT (All)',
                'start': start,
                'end': end,
                'duration': end - start
            })
        
        if self.airdata_df is not None and not self.airdata_df.empty:
            start = self.airdata_df['datetime'].min().timestamp()
            end = self.airdata_df['datetime'].max().timestamp()
            timeline_data.append({
                'source': 'Airdata',
                'start': start,
                'end': end,
                'duration': end - start
            })
        
        if self.dronetag_df is not None and not self.dronetag_df.empty:
            start = self.dronetag_df['datetime'].min().timestamp()
            end = self.dronetag_df['datetime'].max().timestamp()
            timeline_data.append({
                'source': 'Dronetag',
                'start': start,
                'end': end,
                'duration': end - start
            })
        
        if timeline_data:
            # Find overall min and max
            all_starts = [d['start'] for d in timeline_data]
            all_ends = [d['end'] for d in timeline_data]
            global_start = min(all_starts)
            global_end = max(all_ends)
            
            # Plot timeline bars
            y_pos = np.arange(len(timeline_data))
            
            for i, data in enumerate(timeline_data):
                start_offset = data['start'] - global_start
                duration = data['duration']
                
                ax.barh(i, duration, left=start_offset, height=0.5, 
                       color=colors[i % len(colors)], alpha=0.7, edgecolor='black')
                
                # Add duration label
                ax.text(start_offset + duration/2, i, 
                       f"{duration:.0f}s",
                       ha='center', va='center', fontsize=10, fontweight='bold', color='white')
            
            ax.set_yticks(y_pos)
            ax.set_yticklabels([d['source'] for d in timeline_data])
            ax.set_xlabel('Time (seconds from start)')
            ax.set_title('Temporal Coverage Comparison', fontweight='bold', fontsize=12)
            ax.grid(True, alpha=0.3, axis='x')
        
        plt.suptitle('Data Source Comparison: MQTT vs Raw Files', 
                    fontsize=16, fontweight='bold', y=0.995)
        
        output_path = os.path.join(self.output_dir, 'data_source_comparison.png')
        plt.savefig(output_path, dpi=self.OUTPUT_DPI, bbox_inches='tight')
        print(f"  ✅ Saved: {output_path}")
        plt.close()
    
    def generate_report(self):
        """Generate detailed comparison report."""
        print("\n📄 Generating comparison report...")
        
        report_path = os.path.join(self.output_dir, 'comparison_report.md')
        
        with open(report_path, 'w') as f:
            f.write("# Data Source Comparison Report\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## Overview\n\n")
            f.write("This report compares MQTT telemetry data with raw flight data files ")
            f.write("from the same flight session to analyze differences in data richness, ")
            f.write("temporal coverage, and data quality.\n\n")
            
            f.write("## Data Sources\n\n")
            
            # MQTT Section
            if 'mqtt' in self.comparison_results:
                mqtt = self.comparison_results['mqtt']
                f.write("### MQTT Telemetry\n\n")
                f.write(f"- **Total Records:** {mqtt['total_records']:,}\n")
                f.write(f"- **Duration:** {mqtt['duration_seconds']:.1f}s ({mqtt['duration_seconds']/60:.1f} minutes)\n")
                f.write(f"- **Update Rate:** {mqtt['update_rate_hz']:.2f} Hz\n")
                f.write(f"- **Topics:** {mqtt['topics']}\n")
                f.write(f"- **Unique Fields:** {mqtt['unique_fields']}\n\n")
                
                f.write("**Topic Breakdown:**\n\n")
                for topic, info in self.mqtt_data['topics'].items():
                    f.write(f"- `{topic}`: {info['count']:,} records, {len(info['fields'])} fields\n")
                f.write("\n")
            
            # Airdata Section
            if 'airdata' in self.comparison_results:
                airdata = self.comparison_results['airdata']
                f.write("### Airdata CSV (Autel Drone)\n\n")
                f.write(f"- **Total Records:** {airdata['total_records']:,}\n")
                f.write(f"- **Duration:** {airdata['duration_seconds']:.1f}s ({airdata['duration_seconds']/60:.1f} minutes)\n")
                f.write(f"- **Update Rate:** {airdata['update_rate_hz']:.2f} Hz\n")
                f.write(f"- **Fields:** {airdata['fields']}\n\n")
                
                f.write("**Available Fields:**\n\n")
                for i, field in enumerate(airdata['field_names'], 1):
                    f.write(f"{i}. `{field}`\n")
                f.write("\n")
            
            # Dronetag Section
            if 'dronetag' in self.comparison_results:
                dronetag = self.comparison_results['dronetag']
                f.write("### Dronetag Export (Remote ID)\n\n")
                f.write(f"- **Total Records:** {dronetag['total_records']:,}\n")
                f.write(f"- **Duration:** {dronetag['duration_seconds']:.1f}s ({dronetag['duration_seconds']/60:.1f} minutes)\n")
                f.write(f"- **Update Rate:** {dronetag['update_rate_hz']:.2f} Hz\n")
                f.write(f"- **Fields:** {dronetag['fields']}\n\n")
                
                f.write("**Available Fields:**\n\n")
                for i, field in enumerate(dronetag['field_names'], 1):
                    f.write(f"{i}. `{field}`\n")
                f.write("\n")
            
            # Key Findings
            f.write("## Key Findings\n\n")
            
            f.write("### Data Richness\n\n")
            
            if 'mqtt' in self.comparison_results and 'airdata' in self.comparison_results:
                mqtt_fields = self.comparison_results['mqtt']['unique_fields']
                airdata_fields = self.comparison_results['airdata']['fields']
                
                f.write(f"- **MQTT** provides {mqtt_fields} unique fields across multiple topics, ")
                f.write("offering heterogeneous sensor fusion from multiple sources ")
                f.write("(ground station, drone OSD, RemoteID, etc.)\n")
                
                f.write(f"- **Airdata** provides {airdata_fields} fields focused on detailed drone ")
                f.write("flight parameters including RC inputs, gimbal angles, battery cells, etc.\n")
            
            f.write("\n### Temporal Coverage\n\n")
            
            if 'mqtt' in self.comparison_results:
                mqtt_dur = self.comparison_results['mqtt']['duration_seconds']
                f.write(f"- **MQTT**: {mqtt_dur:.0f}s coverage with mixed update rates across topics\n")
            
            if 'airdata' in self.comparison_results:
                airdata_dur = self.comparison_results['airdata']['duration_seconds']
                f.write(f"- **Airdata**: {airdata_dur:.0f}s coverage with consistent {self.comparison_results['airdata']['update_rate_hz']:.1f} Hz sampling\n")
            
            if 'dronetag' in self.comparison_results:
                dronetag_dur = self.comparison_results['dronetag']['duration_seconds']
                f.write(f"- **Dronetag**: {dronetag_dur:.0f}s coverage with ~{self.comparison_results['dronetag']['update_rate_hz']:.1f} Hz updates\n")
            
            f.write("\n### Data Quality Advantages\n\n")
            
            f.write("**MQTT Data Advantages:**\n")
            f.write("- Real-time sensor fusion from multiple heterogeneous sources\n")
            f.write("- Ground station telemetry and link latency metrics\n")
            f.write("- RTK positioning data with fix status\n")
            f.write("- Network connectivity and wireless link quality\n")
            f.write("- Comprehensive system state across all components\n\n")
            
            f.write("**Airdata Advantages:**\n")
            f.write("- High-frequency (5 Hz) drone-specific data\n")
            f.write("- Detailed RC control inputs (elevator, aileron, throttle, rudder)\n")
            f.write("- Individual battery cell voltages\n")
            f.write("- Gimbal control angles (pitch, roll, yaw)\n")
            f.write("- Sonar height and flight state information\n")
            f.write("- Photo/video capture states\n\n")
            
            f.write("**Dronetag Advantages:**\n")
            f.write("- Standardized ASTM F3411 Remote ID format\n")
            f.write("- Multiple altitude references (HAE, PA-QNE, ATO, MSL)\n")
            f.write("- Velocity components in 3D space\n")
            f.write("- Explicit accuracy metrics (horizontal, vertical)\n")
            f.write("- Air pressure measurements\n\n")
            
            f.write("## Recommendations\n\n")
            f.write("1. **Use MQTT data** for comprehensive multi-sensor analysis and real-time system monitoring\n")
            f.write("2. **Use Airdata** for detailed drone flight dynamics analysis and RC control validation\n")
            f.write("3. **Use Dronetag** for regulatory compliance verification and standardized reporting\n")
            f.write("4. **Combine sources** for maximum insight: MQTT for context, Airdata for detail, Dronetag for compliance\n")
        
        print(f"  ✅ Saved: {report_path}")
    
    def run_comparison(self):
        """Run complete comparison analysis."""
        print("\n" + "="*80)
        print("🔍 DATA SOURCE COMPARISON ANALYSIS")
        print("="*80 + "\n")
        
        self.load_mqtt_data()
        self.load_airdata_csv()
        self.load_dronetag_exports()
        self.analyze_data_richness()
        self.plot_comparison()
        self.generate_report()
        
        print("\n" + "="*80)
        print(f"✅ COMPARISON COMPLETE! Results saved to: {self.output_dir}")
        print("="*80 + "\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Compare MQTT telemetry with raw flight data files'
    )
    parser.add_argument(
        '--mqtt',
        type=str,
        default='golden_datasets/mission_20260127_172522.jsonl',
        help='Path to MQTT JSONL file'
    )
    parser.add_argument(
        '--raw-dir',
        type=str,
        default='data/raw',
        help='Directory containing raw data files'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='docs/data_comparison',
        help='Output directory for results'
    )
    
    args = parser.parse_args()
    
    comparator = DataSourceComparator(args.mqtt, args.raw_dir, args.output)
    comparator.run_comparison()


if __name__ == '__main__':
    main()
