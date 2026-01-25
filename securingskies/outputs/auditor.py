"""
SecuringSkies Platform - Telemetry Auditor
==========================================
Version: 0.9.9 (Nightly)
Date: 2026-01-25
Author: Ghost Commander

Role:
  Scientific Logging of AI Performance.
  Calculates 'Hallucination Rate' (False Positives) and 'Recall' (Asset Coverage).
  Prevents 'Negative Hallucinations' (Blindness) from being penalized.
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
        """Initializes the CSV log file with standard scientific headers."""
        if not os.path.exists("logs"):
            os.makedirs("logs")
            
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"logs/metrics_{timestamp}.csv"
        
        try:
            self.file_handle = open(filename, "a", encoding="utf-8")
            # CSV Schema: Time, Model, Latency, Verbosity, Coverage, Error_Rate
            header = "Timestamp,Model,Latency_Sec,Word_Count,Recall_Assets,Hallucination_Visual\n"
            self.file_handle.write(header)
            self.file_handle.flush()
            print(f"📊 METRICS ENGINE ACTIVE: {filename} (v{self.version})")
        except IOError as e:
            print(f"❌ METRICS ERROR: Could not open log file. {e}")
            self.enabled = False

    def _detect_hallucination(self, text: str, telemetry_has_visuals: bool) -> int:
        """
        Determines if the AI is 'imagining' objects.
        
        Logic v0.9.9:
        - If input has data -> AI is allowed to discuss visuals.
        - If input is EMPTY -> AI must NOT make positive claims.
        - CRITICAL FIX: Saying "No visual contact" is NOT a hallucination.
        """
        text = text.lower()
        
        # 1. If we actually have data, the AI is free to speak.
        if telemetry_has_visuals:
            return 0
            
        # 2. If we are BLIND, check for POSITIVE ASSERTIONS only.
        # These phrases imply the AI "sees" something that isn't there.
        positive_triggers = [
            "visual contact", 
            "contact confirmed", 
            "human detected", 
            "vehicle detected", 
            "positive id",
            " sighting"
        ]
        
        for trigger in positive_triggers:
            if trigger in text:
                # FAIL: Claimed to see something when blind.
                return 1 
                
        # PASS: AI correctly reported blindness or stayed silent.
        return 0

    def _calculate_recall(self, text: str, prompts: List[str]) -> float:
        """Calculates percentage of assets mentioned in the SITREP."""
        if not prompts: return 0.0
        
        assets_mentioned = 0
        total_assets = len(prompts)
        
        for p in prompts:
            # Extract Asset ID (Assumes format "Asset: ID | ...")
            try:
                asset_id = p.split('|')[0].replace("Asset:", "").strip()
                if asset_id in text:
                    assets_mentioned += 1
            except IndexError:
                continue
                
        return assets_mentioned / total_assets if total_assets > 0 else 0.0

    def audit(self, model_name: str, start_time: float, raw_prompts: List[str], llm_response: str) -> str:
        """
        Main Execution Block.
        Compares the AI's output against the raw telemetry input.
        """
        if not self.enabled or not self.file_handle:
            return None
        
        # 1. Calculate Latency
        latency = time.time() - start_time
        clean_text = llm_response.replace('*', '').strip()
        
        # 2. Check for Visual Data in Input
        # (Naive check: does the raw data contain the word VISUAL from the driver?)
        visuals_in_input = any("VISUAL" in p for p in raw_prompts)
        
        # 3. Run Metrics
        hallucination_score = self._detect_hallucination(clean_text, visuals_in_input)
        recall_score = self._calculate_recall(clean_text, raw_prompts)

        # 4. Log to CSV
        log_line = (
            f"{datetime.now().isoformat()},"
            f"{model_name},"
            f"{latency:.2f},"
            f"{len(clean_text.split())},"
            f"{recall_score:.2f},"
            f"{hallucination_score}\n"
        )
        
        try:
            self.file_handle.write(log_line)
            self.file_handle.flush()
        except IOError:
            pass
        
        # 5. Return Human-Readable Summary
        return (
            f"[METRICS] Latency: {latency:.2f}s | "
            f"Recall: {recall_score:.0%} | "
            f"Hallucination: {hallucination_score}"
        )

    def close(self):
        if self.file_handle:
            self.file_handle.close()
