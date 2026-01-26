# In optimizer_v2_1.py

def validate_sitrep(example, pred, trace=None):
    score = 0
    truth = example.raw_telemetry
    pred_text = pred.report
    
    # --- EXISTING REWARDS ---
    # 1. Human Detection (Recall)
    if "Human" in truth:
        if "Human" in pred_text and "CONTACT" in pred_text: score += 2
    else:
        score += 1 
    
    # 2. RTK Respect (Hallucination Check)
    if "RTK" in truth:
        if "GOOD" in pred_text or "RTK" in pred_text: score += 1
        
    # --- NEW REWARD (Factuality) ---
    # 3. Battery Accuracy (The "Auditor Match")
    import re
    # Extract battery from Truth string (e.g., "BATT: 59%")
    truth_batt_match = re.search(r'BATT: (\d+)%', truth)
    
    if truth_batt_match:
        truth_batt = truth_batt_match.group(1)
        # Check if the exact number appears in Prediction
        if truth_batt in pred_text:
            score += 2 # High reward for getting facts right
        else:
            score -= 1 # Penalty for hallucinating numbers
            
    return score >= 4 # Increased threshold due to new points
