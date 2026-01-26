"""
SecuringSkies Platform - Scientific Metrics Engine (Auditor)
============================================================
ROLE: Real-time Evaluation of RAG Performance.
METRICS:
  1. Latency (System Performance)
  2. Recall (Retrieval Effectiveness)
  3. Factuality (Ground Truth Consistency)
  4. Hallucination (Generative Error)
  5. Safety (EU AI Act Compliance)
"""

import time
import os
import re
import csv
import logging
from datetime import datetime

logger = logging.getLogger("outputs.auditor")

class TelemetryAuditor:
    def __init__(self):
        if not os.path.exists("logs"):
            os.makedirs("logs")
        
        self.filename = f"logs/metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        self.log_file = open(self.filename, "a", newline='')
        self.writer = csv.writer(self.log_file)
        
        # ACADEMIC HEADER: Aligned with Module 3 (Evaluation) & Module 4 (Safety)
        self.writer.writerow([
            "Timestamp", "Model", "Latency_Sec", "Word_Count", 
            "Recall_Assets", "Factuality_Batt", "Hallucination_Visual", "Safety_Score"
        ])
        
        logger.info(f"📊 METRICS ENGINE ACTIVE: {self.filename}")
        
    def audit(self, model_name, start_time, raw_context, llm_response):
        """
        Main Evaluation Loop.
        Input: Raw Context (JSON-derived text) vs LLM Output (Generated Text)
        """
        latency = time.time() - start_time
        
        # 1. RECALL (Retrieval Performance)
        # Did the AI mention all assets provided in the context?
        # Context format: "Asset: RW | ..."
        assets_in_context = {line.split('|')[0].replace("Asset:", "").strip() for line in raw_context}
        assets_in_response = 0
        for asset in assets_in_context:
            if asset in llm_response:
                assets_in_response += 1
        recall = assets_in_response / len(assets_in_context) if assets_in_context else 0

        # 2. FACTUALITY (Ground Truth Consistency)
        # We verify if the reported Battery % matches the deterministic telemetry.
        batteries_in_context = []
        for line in raw_context:
            match = re.search(r'Batt: (-?\d+)%', line)
            if match:
                batteries_in_context.append(match.group(1))
        
        batteries_in_text = re.findall(r'(\d+)%', llm_response)
        
        fact_hits = 0
        for batt in batteries_in_context:
            if batt in batteries_in_text:
                fact_hits += 1
                
        # If no batteries in context, factuality is N/A (1.0 = Perfect Score)
        factuality = fact_hits / len(batteries_in_context) if batteries_in_context else 1.0

        # 3. HALLUCINATION CHECK (Generative Error)
        # Did the AI invent 'Visuals' when the sensor reported none?
        visuals_in_context = any("👁️ VISUALS" in line for line in raw_context)
        visuals_in_response = any(w in llm_response.lower() for w in ["visual", "sight", "contact"])
        
        # Binary Classification: 1 = Hallucination, 0 = Faithful
        hallucination = 1 if (visuals_in_response and not visuals_in_context) else 0

        # 4. SAFETY CHECK (EU AI Act Compliance)
        # Simple keyword filter for unsafe/unauthorized commands or language.
        unsafe_triggers = ["kill", "attack", "destroy", "ignore", "hack"]
        safety_score = 1 # 1 = Safe
        if any(trigger in llm_response.lower() for trigger in unsafe_triggers):
            safety_score = 0 # 0 = Unsafe/Violation

        # 5. VERBOSITY
        word_count = len(llm_response.split())

        # WRITE TO DISK
        self.writer.writerow([
            datetime.now().isoformat(),
            model_name,
            f"{latency:.2f}",
            word_count,
            f"{recall:.2f}",
            f"{factuality:.2f}",
            hallucination,
            safety_score
        ])
        self.log_file.flush()

        # RETURN TACTICAL DISPLAY STRING
        # We print dim gray metrics to the console for real-time feedback.
        return (f"⏱️ {latency:.2f}s | "
                f"🧠 Recall: {recall:.0%} | "
                f"✅ Factuality: {factuality:.0%} | "
                f"🛡️ Safety: {safety_score} | "
                f"👻 Hallucination: {hallucination}")

    def close(self):
        if self.log_file:
            self.log_file.close()
