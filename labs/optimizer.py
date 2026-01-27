"""
SecuringSkies DSPy Optimizer (v1.2 Academic)
============================================
MODULE: labs.optimizer
VERSION: 1.2.0 (Role-Specific Grading)
DESCRIPTION:
  Optimizes AI personas using distinct grading metrics for each role.
  
  IMPROVEMENTS v1.2:
  - Analyst: Rewards 'Technical Vocabulary' (RTK, Latency, Delta).
  - Commander: Rewards 'Spatial Awareness' (Distance, Speed, Direction).
  - Pilot: Rewards 'Extreme Brevity' (Under 20 words).
  - Factuality: Strict Battery % checking for all.

USAGE:
  python3 labs/optimizer.py --persona analyst --log golden_datasets/mission_20260127_172522.jsonl
"""

import dspy
import json
import os
import re
import argparse
from dspy.teleprompt import BootstrapFewShot

# ------------------------------------------------------------------
# 1. PERSONA SIGNATURES
# ------------------------------------------------------------------

class AnalystSitrep(dspy.Signature):
    """
    You are a Forensic Data Scientist.
    Input: Raw Telemetry (JSON).
    Output: Technical Assessment (40-50 words).
    INSTRUCTIONS:
    - Compare Autel RTK vs Dronetag GPS.
    - Report Latency and Altitude Deltas.
    - Use technical terms: 'Delta', 'Offset', 'Latency', 'RTK'.
    """
    raw_telemetry = dspy.InputField(desc="Raw JSON flattened to string")
    report = dspy.OutputField(desc="Forensic Report. Mathematical & Precise.")

class PilotSitrep(dspy.Signature):
    """
    You are a Drone Co-Pilot. 
    Input: Raw Telemetry (JSON).
    Output: Immediate Action (10-20 words).
    INSTRUCTIONS:
    - Safety Critical only (Battery, Obstacles).
    - If status is nominal, be brief.
    """
    raw_telemetry = dspy.InputField(desc="Raw JSON flattened to string")
    report = dspy.OutputField(desc="Cockpit Callout. Urgent & Direct.")

class CommanderSitrep(dspy.Signature):
    """
    You are a Strategic Mission Commander.
    Input: Raw Telemetry (JSON).
    Output: Situational Awareness (20-40 words).
    INSTRUCTIONS:
    - Report Asset Status (UAV, GCS).
    - Report Vectors (Speed, Heading) and Relative Distances.
    """
    raw_telemetry = dspy.InputField(desc="Raw JSON flattened to string")
    report = dspy.OutputField(desc="Strategic Update. Big Picture.")

PERSONA_MAP = {
    "analyst": AnalystSitrep,
    "pilot": PilotSitrep,
    "commander": CommanderSitrep
}

# ------------------------------------------------------------------
# 2. ROLE-SPECIFIC METRICS (The "Specialists")
# ------------------------------------------------------------------

def check_factuality(truth, pred_text):
    """Universal Check: Do not hallucinate battery numbers."""
    truth_batt_match = re.search(r"'batt': (\d+)", truth)
    if not truth_batt_match: truth_batt_match = re.search(r"'capacity_percent': (\d+)", truth)
    
    if truth_batt_match:
        if truth_batt_match.group(1) in pred_text:
            return 1
        else:
            return -1 # Lying about battery is a sin
    return 0

def validate_analyst(example, pred, trace=None):
    """Grading for the SCIENTIST."""
    score = 0
    truth = example.raw_telemetry
    pred_text = pred.report
    
    # 1. Factuality
    score += check_factuality(truth, pred_text)
    
    # 2. Vocabulary (The PhD Check)
    tech_terms = ["Latency", "RTK", "Delta", "Offset", "Accuracy", "Fused", "ms", "s"]
    term_count = sum(1 for term in tech_terms if term in pred_text)
    if term_count >= 2: score += 2
    
    # 3. Length (Must be detailed)
    if len(pred_text.split()) < 20: score -= 1
    
    return score >= 2

def validate_commander(example, pred, trace=None):
    """Grading for the STRATEGIST."""
    score = 0
    truth = example.raw_telemetry
    pred_text = pred.report
    
    # 1. Factuality
    score += check_factuality(truth, pred_text)
    
    # 2. Spatial Awareness
    spatial_terms = ["Speed", "Distance", "North", "South", "East", "West", "GCS", "UAV", "km/h"]
    term_count = sum(1 for term in spatial_terms if term in pred_text)
    if term_count >= 2: score += 2
    
    # 3. Length (Medium)
    if len(pred_text.split()) > 50: score -= 1
    
    return score >= 2

def validate_pilot(example, pred, trace=None):
    """Grading for the WATCHDOG."""
    score = 0
    truth = example.raw_telemetry
    pred_text = pred.report
    
    # 1. Factuality
    score += check_factuality(truth, pred_text)
    
    # 2. Safety (Recall)
    if "Human" in truth and "Human" not in pred_text: score -= 10
    
    # 3. Brevity (The main goal)
    word_count = len(pred_text.split())
    if word_count <= 20: score += 2
    if word_count > 30: score -= 2
    
    return score >= 1

METRIC_MAP = {
    "analyst": validate_analyst,
    "commander": validate_commander,
    "pilot": validate_pilot
}

# ------------------------------------------------------------------
# 3. DATA LOADER
# ------------------------------------------------------------------
def load_training_data(log_path, limit=25):
    dataset = []
    
    # Seed to ensure format compliance
    dataset.append(dspy.Example(
        raw_telemetry="{'tid': 'UAV-1', 'batt': 55, 'pos_type': 50, 'link_latency': '1.2s', 'alt': 120, 'height': 45}",
        report="DATA INTEGRITY: RTK Fixed (Type 50). Latency 1.2s. Vertical Delta: 75m (MSL vs AGL). Battery 55%."
    ).with_inputs('raw_telemetry'))

    if not os.path.exists(log_path):
        print(f"❌ ERROR: Log file not found at {log_path}")
        return dataset 
        
    print(f"📂 Scanning {log_path}...")
    with open(log_path, 'r', encoding='utf-8') as f:
        for line in f:
            if len(dataset) >= limit: break
            try:
                rec = json.loads(line)
                data = rec.get('data', {})
                data_str = str(data)
                
                # Filter for useful data
                if 'lat' in data_str or 'obj_cnt' in data_str:
                    if 'tid' not in data: data['tid'] = "TRAINING_UNIT"
                    dataset.append(dspy.Example(raw_telemetry=str(data)).with_inputs('raw_telemetry'))
            except: continue
            
    print(f"💎 Found {len(dataset)} Training Examples.")
    return dataset

# ------------------------------------------------------------------
# 4. EXECUTION LOOP
# ------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", type=str, required=True)
    parser.add_argument("--persona", type=str, required=True, choices=["analyst", "pilot", "commander"])
    parser.add_argument("--model", type=str, default="ollama/llama3.1")
    args = parser.parse_args()

    output_path = f"config/optimized_{args.persona}.json"
    print(f"🦅 ACADEMY v1.2: Training '{args.persona.upper()}' using Specialized Metric...")
    
    try:
        lm = dspy.LM(model=args.model, api_base='http://localhost:11434', api_key='ollama')
        dspy.settings.configure(lm=lm)
    except Exception as e:
        print(f"⚠️ INTELLIGENCE FAILURE: {e}")
        return
    
    signature_class = PERSONA_MAP[args.persona]
    metric_func = METRIC_MAP[args.persona]
    
    module = dspy.ChainOfThought(signature_class)
    trainset = load_training_data(args.log)

    # Bootstrap
    teleprompter = BootstrapFewShot(metric=metric_func, max_bootstrapped_demos=3, max_labeled_demos=1)
    
    try:
        optimized_program = teleprompter.compile(module, trainset=trainset)
        optimized_program.save(output_path)
        print(f"\n✅ OPTIMIZATION SUCCESS: {output_path}")
        if hasattr(optimized_program, 'demos'):
            print(f"   Learned {len(optimized_program.demos)} high-quality patterns.")
            
    except Exception as e:
        print(f"❌ Training Failed: {e}")

if __name__ == "__main__":
    main()
