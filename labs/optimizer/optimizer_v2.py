#!/usr/bin/env python3
"""
SecuringSkies DSPy Optimizer v2 (The "Human" Update)
----------------------------------------------------
TARGET: Train the Analyst to recognize:
1. Class 30 (Human) -> Report "Visual: Human"
2. RTK Status -> Report "GPS: GOOD (RTK)"
"""

import dspy
import json
import glob
import random
from dspy.teleprompt import BootstrapFewShot

# 1. SETUP
try:
    lm = dspy.LM(model='ollama/llama3.1', api_base='http://localhost:11434', api_key='ollama')
except Exception as e:
    print(f"⚠️ Error: {e}")
    exit(1)
dspy.settings.configure(lm=lm)

# 2. LOAD NEW LOGS (Prioritizing the latest mission)
def load_training_data(limit=12):
    dataset = []
    # Target the specific log file you just created
    target_logs = glob.glob("logs/mission_20260124_183305.jsonl") 
    
    print(f"📂 Scanning specific log: {target_logs}")
    
    for logf in target_logs:
        with open(logf, 'r') as f:
            for line in f:
                if len(dataset) >= limit: break
                try:
                    rec = json.loads(line)
                    data = rec.get('data', {})
                    
                    # Construct Input String (Simulating v47 format)
                    if 'tid' in data:
                        # Logic to inject the "Human" finding if Class 30 exists
                        sightings = []
                        if 'sightings' in rec: # If parsed previously
                            sightings = rec['sightings']
                        
                        # Mocking the Visual Tag for training
                        visual_tag = ""
                        # In v47, Class 30 is mapped to Human, so we simulate that output
                        if "30" in str(data) or "Human" in str(data): 
                            visual_tag = " | 👁️ VISUAL: {'Human': 1}"
                        
                        rtk_tag = "GPS"
                        # Detecting RTK usage in raw data
                        pos_state = data.get('position_state', {})
                        if pos_state.get('rtk_used') == 1 or pos_state.get('is_fixed') == 3:
                            rtk_tag = "RTK-FIX"

                        sim_input = f"{data['tid']} | Type: AIR | Status: Active | BATT: {data.get('batt', 55)}% | GPS: {rtk_tag} (0.1m) {visual_tag}"
                        
                        dataset.append(dspy.Example(raw_telemetry=sim_input).with_inputs('raw_telemetry'))
                except: continue
    
    # Add manual edge cases to ensure it learns difficult scenarios
    dataset.append(dspy.Example(raw_telemetry="UAV-1479 | Type: AIR | GPS: RTK-FIX (0.1m) | 👁️ VISUAL: {'Human': 3}").with_inputs('raw_telemetry'))
    dataset.append(dspy.Example(raw_telemetry="UAV-9999 | Type: AIR | GPS: GPS (12m) | 👁️ VISUAL: None").with_inputs('raw_telemetry'))
    
    return dataset

# 3. SIGNATURE
class AnalystSitrep(dspy.Signature):
    """
    You are a Defense Data Scientist.
    Analyze telemetry. Priority: VISUALS > GPS ACCURACY > BATTERY.
    
    RULES:
    - If "RTK-FIX" or <1m Accuracy -> GPS: GOOD (RTK)
    - If "VISUAL: Human" -> Report "CONTACT: Human detected"
    - If Accuracy > 10m -> GPS: POOR
    """
    raw_telemetry = dspy.InputField(desc="Raw MQTT data")
    report = dspy.OutputField(desc="Forensic SITREP")

# 4. METRIC (The Teacher)
def validate_sitrep(example, pred, trace=None):
    score = 0
    truth = example.raw_telemetry
    pred_text = pred.report
    
    # Reward 1: Did it spot the Human?
    if "Human" in truth:
        if "Human" in pred_text: score += 2
    else:
        score += 1 # Bonus for not hallucinating humans when none exist
    
    # Reward 2: Did it respect RTK?
    if "RTK" in truth:
        if "GOOD" in pred_text or "RTK" in pred_text: score += 1
    
    # Reward 3: Formatting check
    if "|" in pred_text: score += 1
    
    return score >= 3

# 5. MAIN
def main():
    print("🦅 Training Analyst v2 (Human/RTK Focused)...")
    trainset = load_training_data()
    print(f"🧪 Loaded {len(trainset)} examples.")
    
    module = dspy.ChainOfThought(AnalystSitrep)
    
    print("🧠 Optimizing (BootstrapFewShot)...")
    # Using labeled demos to force correct behavior
    teleprompter = BootstrapFewShot(metric=validate_sitrep, max_bootstrapped_demos=3, max_labeled_demos=3)
    
    try:
        opt = teleprompter.compile(module, trainset=trainset)
    except Exception as e:
        print(f"❌ Training Failed: {e}")
        return
    
    print("\n✅ OPTIMIZATION COMPLETE.")
    print("💾 Saving to: config/personas_v2.json")
    opt.save("config/personas_v2.json")
    
    # Show results
    print("\n🔍 What it learned (The Golden Prompts):")
    if hasattr(opt, 'demos'):
        for i, demo in enumerate(opt.demos):
            print(f"Example {i+1}:\n   Input: {demo.raw_telemetry}\n   Output: {demo.report}\n")

if __name__ == "__main__":
    main()
