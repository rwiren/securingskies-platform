"""
SecuringSkies Platform - Telemetry Auditor
==========================================
Version: 0.9.9
Role: Metrics logging.
"""

import os
import time
from datetime import datetime
from typing import List

class TelemetryAuditor:
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.file_handle = None
        self.version = "0.9.9"
        
        if self.enabled:
            self._init_file()

    def _init_file(self):
        if not os.path.exists("logs"): os.makedirs("logs")
        filename = f"logs/metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        try:
            self.file_handle = open(filename, "a", encoding="utf-8")
            self.file_handle.write("Timestamp,Model,Latency_Sec,Word_Count,Recall_Assets,Hallucination_Visual\n")
            self.file_handle.flush()
            print(f"📊 METRICS ENGINE ACTIVE: {filename} (v{self.version})")
        except IOError:
            self.enabled = False

    def _detect_hallucination(self, text: str, telemetry_has_visuals: bool) -> int:
        """Determines if the AI is 'imagining' objects."""
        text = text.lower()
        
        # 1. If we have data, AI can speak.
        if telemetry_has_visuals: return 0
            
        # 2. If BLIND, check for POSITIVE ASSERTIONS only.
        positive_triggers = ["visual contact", "contact confirmed", "human detected", "vehicle detected"]
        for trigger in positive_triggers:
            if trigger in text: return 1 # FAIL
                
        return 0 # PASS

    def _calculate_recall(self, text: str, prompts: List[str]) -> float:
        if not prompts: return 0.0
        assets_mentioned = 0
        for p in prompts:
            try:
                asset_id = p.split('|')[0].replace("Asset:", "").strip()
                if asset_id in text: assets_mentioned += 1
            except: continue
        return assets_mentioned / len(prompts) if len(prompts) > 0 else 0.0

    def audit(self, model_name: str, start_time: float, raw_prompts: List[str], llm_response: str) -> str:
        if not self.enabled or not self.file_handle: return None
        
        latency = time.time() - start_time
        clean_text = llm_response.replace('*', '').strip()
        visuals_in_input = any("VISUAL" in p for p in raw_prompts)
        
        hallucination_score = self._detect_hallucination(clean_text, visuals_in_input)
        recall_score = self._calculate_recall(clean_text, raw_prompts)

        try:
            self.file_handle.write(f"{datetime.now().isoformat()},{model_name},{latency:.2f},{len(clean_text.split())},{recall_score:.2f},{hallucination_score}\n")
            self.file_handle.flush()
        except: pass
        
        return f"[METRICS] Latency: {latency:.2f}s | Recall: {recall_score:.0%} | Hallucination: {hallucination_score}"
