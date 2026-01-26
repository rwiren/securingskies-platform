"""
SecuringSkies DSPy Optimizer (v1.0 Academic)
============================================
MODULE: labs.optimizer
ROLE: The "Academy" (Multi-Persona Trainer)
ACADEMIC REF: Stanford DSPy - BootstrapFewShot
DESCRIPTION:
  Optimizes specific AI personas by selecting the best Few-Shot examples
  from historical logs.
  
  FEATURES:
  - Smart Filtering (v1.0): Correctly identifies Raw Autel Telemetry (obj_cnt, pos_type).
  - Multi-Persona: Supports Analyst, Pilot, and Commander signatures.
  - Metric-Driven: Grades on Safety (Recall), Precision (Factuality), and Logic.

USAGE:
  python3 labs/optimizer.py --help
  python3 labs/optimizer.py --persona analyst --limit 30 --log logs/mission_20260125_163706.jsonl
"""

import dspy
import json
import os
import re
import argparse
import sys
from dspy.teleprompt import BootstrapFewShot

# ------------------------------------------------------------------
# 1. PERSONA SIGNATURES (The "Job Descriptions")
# ------------------------------------------------------------------

class AnalystSitrep(dspy.Signature):
    """
    You are a Forensic Data Scientist (Analyst). 
    Input is raw JSON. Output is a detailed assessment of Data Quality, 
    RTK Accuracy, and Battery Precision. Report any anomalies.
    """
    raw_telemetry = dspy.InputField(desc="Raw JSON flattened to string")
    report = dspy.OutputField(desc="Forensic Report (Max 30 words)")

class PilotSitrep(dspy.Signature):
    """
    You are a Drone Co-Pilot. 
    Input is raw JSON. Output is an IMMEDIATE, CONCISE status update.
    Focus on Warning Flags, Battery Criticality, and Obstacles.
    """
    raw_telemetry = dspy.InputField(desc="Raw JSON flattened to string")
    report = dspy.OutputField(desc="Cockpit Callout (Max 15 words)")

class CommanderSitrep(dspy.Signature):
    """
    You are a Tactical Commander. 
    Input is raw JSON. Output is a Strategic Summary.
    Focus on Mission Progress, ETA, and Asset Separation.
    """
    raw_telemetry = dspy.InputField(desc="Raw JSON flattened to string")
    report = dspy.OutputField(desc="Strategic Update (Max 40 words)")

PERSONA_MAP = {
    "analyst": AnalystSitrep,
    "pilot": PilotSitrep,
    "commander": CommanderSitrep
}

# ------------------------------------------------------------------
# 2. METRIC FUNCTION (The "Grader")
# ------------------------------------------------------------------
def validate_sitrep(example, pred, trace=None):
    """
    Universal Grading Logic (Safety & Factuality).
    """
    score = 0
    truth = example.raw_telemetry
    pred_text = pred.report
    
    # CRITERION 1: Human Safety (Recall) - UNIVERSAL RULE
    # Logic: If raw JSON has 'cls_id': 30 (Human) or 4, we MUST see "Human" or "CONTACT"
    if "'cls_id': 30" in truth or "'cls_id': 4" in truth or "Human" in truth:
        if "Human" in pred_text or "CONTACT" in pred_text: 
            score += 2
        else:
            score -= 10 # Critical Safety Failure (Immediate Fail)
            
    # CRITERION 2: Factuality (Battery Check)
    truth_batt_match = re.search(r"'batt': (\d+)", truth) # Check Normalized
    if not truth_batt_match:
         truth_batt_match = re.search(r"'capacity_percent': (\d+)", truth) # Check Raw Autel
         
    if truth_batt_match:
        truth_batt = truth_batt_match.group(1)
        if truth_batt in pred_text:
            score += 1 
            
    # CRITERION 3: Hallucination Check
    # If no objects in truth, but prediction says VISUAL/CONTACT -> Penalty
    if "obj_cnt" in truth and "'obj_cnt': 0" in truth:
        if "VISUAL" in pred_text or "CONTACT" in pred_text:
            score -= 1
            
    # THRESHOLD: Must achieve a baseline score to pass
    return score >= 1

# ------------------------------------------------------------------
# 3. DATA LOADER (With FIXED Smart Filtering)
# ------------------------------------------------------------------
def load_training_data(log_path, limit=10):
    """Ingests logs but FILTERS for High-Value Data (Autel/RTK/AI)."""
    dataset = []
    
    # A. GOLDEN SEED (Guarantees the model knows the format)
    # This prevents "0 traces" if the log is empty or incompatible.
    dataset.append(dspy.Example(
        raw_telemetry="{'tid': 'UAV-1479', 'batt': 59, 'pos_type': 50, 'obj_cnt': 1, 'objs': [{'cls_id': 30}]}",
        report="Asset: UAV-1479 | GPS: GOOD (RTK-FIX) | BATT: 59% | ⚠️ CONTACT: Human detected (Class 30)"
    ).with_inputs('raw_telemetry'))

    if not os.path.exists(log_path):
        print(f"❌ ERROR: Log file not found at {log_path}")
        return dataset # Return seed only
        
    print(f"📂 Scanning {log_path} for High-Value Events...")
    
    with open(log_path, 'r', encoding='utf-8') as f:
        for line in f:
            if len(dataset) >= limit: break
            try:
                rec = json.loads(line)
                topic = rec.get('topic', '')
                data = rec.get('data', {})
                data_str = str(data)
                
                # --- SMART FILTER v1.0 (FIXED) ---
                # 1. Reject OwnTracks (Phones) -> Too simple
                if "owntracks" in topic: continue
                
                # 2. Reject boring heartbeats (Must have GPS fix OR Objects)
                # We look for RAW keys: 'pos_type' (RTK) or 'obj_cnt' (Vision)
                has_rtk = 'pos_type' in data_str
                has_objs = 'obj_cnt' in data_str
                
                if not (has_rtk or has_objs): 
                    continue
                # ---------------------------

                # Add a synthetic TID for Autel logs if missing (for consistency)
                if 'tid' not in data: data['tid'] = "AUTEL_TRAINING_UNIT"
                
                raw_str = str(data)
                dataset.append(dspy.Example(raw_telemetry=raw_str).with_inputs('raw_telemetry'))
            except: continue
            
    print(f"💎 Found {len(dataset)} High-Value Examples (Filtered from noise).")
    return dataset

# ------------------------------------------------------------------
# 4. EXECUTION LOOP
# ------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="🦅 SecuringSkies Multi-Persona Optimizer")
    
    # ARGUMENTS with DEFAULTS
    parser.add_argument("--log", type=str, default="logs/mission_20260125_163706.jsonl", 
                        help="Path to training logs (Recommended: 163706 for Human Data)")
    parser.add_argument("--model", type=str, default="ollama/llama3.1", 
                        help="Target LLM (Default: llama3.1)")
    parser.add_argument("--persona", type=str, default="analyst", choices=["analyst", "pilot", "commander"], 
                        help="Target Persona to train")
    parser.add_argument("--limit", type=int, default=20, 
                        help="Training set size (Higher is better for complex logs)")
    parser.add_argument("--output", type=str, default=None, help="Custom output path")
    
    args = parser.parse_args()

    # Dynamic Output Path
    if args.output is None:
        args.output = f"config/optimized_{args.persona}.json"

    print(f"🦅 ACADEMY v1.0: Training '{args.persona.upper()}' on {args.model}...")
    
    # 1. Configure LM
    try:
        lm = dspy.LM(model=args.model, api_base='http://localhost:11434', api_key='ollama')
        dspy.settings.configure(lm=lm)
    except Exception as e:
        print(f"⚠️ INTELLIGENCE FAILURE: {e}")
        return
    
    # 2. Select Persona
    signature_class = PERSONA_MAP[args.persona]
    module = dspy.ChainOfThought(signature_class)
    
    # 3. Load Data
    trainset = load_training_data(args.log, args.limit)

    # 4. Optimize
    print(f"🧠 Optimizing {args.persona.upper()} logic...")
    teleprompter = BootstrapFewShot(metric=validate_sitrep, max_bootstrapped_demos=3, max_labeled_demos=1)
    
    try:
        optimized_program = teleprompter.compile(module, trainset=trainset)
        
        print("\n✅ GRADUATION DAY! Optimization Success.")
        print("-" * 60)
        optimized_program.save(args.output)
        print(f"💾 Trained Brain saved to: {args.output}")
        print(f"💡 ACTION: Run Officer with: --persona {args.persona}")
        
    except Exception as e:
        print(f"❌ Training Failed: {e}")

if __name__ == "__main__":
    main()
