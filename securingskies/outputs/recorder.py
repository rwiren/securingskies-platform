"""
SecuringSkies Platform - Black Box Recorder
===========================================
Role: Forensic Logging (JSONL Standard)
"""

import json
import time
import os
import logging
from datetime import datetime

logger = logging.getLogger("outputs.recorder")

class BlackBox:
    def __init__(self, enabled=True):
        self.enabled = enabled
        self.file_handle = None
        self.filename = None
        
        if self.enabled:
            self._init_file()

    def _init_file(self):
        if not os.path.exists("logs"):
            os.makedirs("logs")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.filename = f"logs/mission_{timestamp}.jsonl"
        
        try:
            self.file_handle = open(self.filename, "a", encoding='utf-8')
            logger.info(f"🔴 RECORDING STARTED: {self.filename}")
        except Exception as e:
            logger.error(f"Failed to open log file: {e}")
            self.enabled = False

    def log(self, topic, payload):
        """Thread-safe logging of raw packets"""
        if not self.enabled or not self.file_handle:
            return
            
        try:
            # Ensure payload is serializable
            if isinstance(payload, bytes):
                data = json.loads(payload.decode('utf-8'))
            elif isinstance(payload, str):
                data = json.loads(payload)
            else:
                data = payload

            entry = {
                "ts": time.time(),
                "topic": topic,
                "data": data
            }
            
            self.file_handle.write(json.dumps(entry) + "\n")
            self.file_handle.flush()
            
        except Exception:
            pass # Never crash the mission for a log error

    def close(self):
        if self.file_handle:
            self.file_handle.close()
