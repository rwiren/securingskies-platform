"""
SecuringSkies Platform - Telemetry Auditor
==========================================
Role: Scientific Logging of AI Performance (Recall/Precision).
"""

import os
import time
import re
from datetime import datetime

class TelemetryAuditor:
    def __init__(self, enabled=True):
        self.enabled = enabled
        self.file_handle = None
        
        if self.enabled:
            self._init_file()

    def _init_file(self):
        if not os.path.exists("logs"): os.makedirs("logs")
        filename = f"logs/metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        self.file_handle = open(filename, "a")
        # Write CSV Header
        self.file_handle.write("Timestamp,Model,Latency_Sec,Word_Count,Recall_Assets,Hallucination_Visual\n")
        self.file_handle.flush()

    def audit(self, model_name, start_time, raw_prompts, llm_response):
        """
        Compares the AI's output against the raw telemetry input.
        """
        if not self.enabled or not self.file_handle: return
        
        latency = time.time() - start_time
        clean_text = llm_response.replace('*', '')
        
        # 1. Hallucination Check (Visuals)
        visuals_in_input = any("VISUAL" in p for p in raw_prompts)
        visuals_in_output = "visual" in clean_text.lower() or "contact" in clean_text.lower()
        hallucination = 1 if (visuals_in_output and not visuals_in_input) else 0
        
        # 2. Asset Recall (Did it mention everyone?)
        assets_in_input = len(raw_prompts)
        assets_in_output = sum(1 for p in raw_prompts if p.split('|')[0].strip() in clean_text)
        recall = assets_in_output / assets_in_input if assets_in_input > 0 else 0

        # Log to CSV
        log_line = f"{datetime.now().isoformat()},{model_name},{latency:.2f},{len(clean_text.split())},{recall:.2f},{hallucination}\n"
        self.file_handle.write(log_line)
        self.file_handle.flush()
