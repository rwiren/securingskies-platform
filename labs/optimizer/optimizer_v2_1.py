#!/usr/bin/env python3
"""
SecuringSkies DSPy Optimizer v2.1 (Seeded Learning)
---------------------------------------------------
- Fixes "Bootstrapped 0 traces" by providing a Golden Example.
- Teaches: Class 30 (Human) -> "CONTACT: Human detected"
- Teaches: RTK Status -> "GPS: GOOD (RTK)"
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

# 2. LOAD DATA (Mixed Real + Synthetic)
def load_training_data(limit=12):
    dataset = []
    
    # A. The "Golden Seed" (The Answer Key)
    # This teaches the model EXACTLY what we want, breaking the zero-shot cycle.
    dataset.append(dspy.Example(
        raw_telemetry="UAV-1479 | Type: AIR | Status: Active | BATT: 59% | GPS: RTK-FIX (0.1m) | 👁️ VISUAL: {'Human': 1}",
        report="Asset: UAV-1479 | GPS: GOOD (RTK) | CONTACT: Human detected (1)"
    ).with_inputs('raw_telemetry'))

    # B. The "Real World" Logs (Unlabeled - for generalization)
    target_logs = glob.glob("logs/mission_20260124_183305.jsonl") 
    print(f"📂 Scanning logs: {target_logs}")
    
    for logf in target_logs:
        with open(logf, 'r') as f:
            for line in f:
                if len(dataset) >= limit: break
                try:
                    rec = json.loads(line)
                    data = rec.get('data', {})
                    
                    if 'tid' in data:
                        # Synthetic Parser Logic (Simulating v47)
                        visual_tag = ""
                        if "30" in str(data) or "Human" in str(data): 
                            visual_tag = " | 👁️ VISUAL: {'Human': 1}"
                        
                        rtk_tag = "GPS"
                        pos = data.get('position_state', {})
                        if pos.get('rtk_used') == 1 or pos.get('is_fixed') == 3:
                            rtk_tag = "RTK-FIX"

                        sim_input = f"{data['tid']} | Type: AIR | Status: Active | BATT: {data.get('batt', 55)}% | GPS: {rtk_tag} (0.1m) {visual_tag}"
                        
                        dataset.append(dspy.Example(raw_telemetry=sim_input).with_inputs('raw_telemetry'))
                except: continue
    
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
    
    # Reward 1: Human Detection
    if "Human" in truth:
        if "Human" in pred_text and "CONTACT" in pred_text: score += 2
    else:
        score += 1 
    
    # Reward 2: RTK Respect
    if "RTK" in truth:
        if "GOOD" in pred_text or "RTK" in pred_text: score += 1
    
    # Reward 3: Formatting
    if "|" in pred_text: score += 1
    
    return score >= 3

# 5. MAIN
def main():
    print("🦅 Training Analyst v2.1 (Seeded Optimizer)...")
    trainset = load_training_data()
    print(f"🧪 Loaded {len(trainset)} examples (including Golden Seed).")
    
    module = dspy.ChainOfThought(AnalystSitrep)
    
    print("🧠 Optimizing...")
    # NOTE: max_labeled_demos=1 uses our Golden Seed to teach the others
    teleprompter = BootstrapFewShot(metric=validate_sitrep, max_bootstrapped_demos=2, max_labeled_demos=1)
    
    try:
        opt = teleprompter.compile(module, trainset=trainset)
        print("\n✅ OPTIMIZATION SUCCESS!")
        print("💾 Saving to: config/personas_v2.json")
        opt.save("config/personas_v2.json")
        
        print("\n🔍 The AI has Learned:")
        for i, demo in enumerate(opt.demos):
            print(f"Example {i+1}:\n   Input: {demo.raw_telemetry}\n   Output: {demo.report}\n")
            
    except Exception as e:
        print(f"❌ Training Failed: {e}")

if __name__ == "__main__":
    main()
