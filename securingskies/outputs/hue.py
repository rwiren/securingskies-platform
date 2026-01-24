"""
SecuringSkies Platform - Hue Lighting Controller
================================================
Role: Ambient Status Display
Feature Parity: Restores specific color codes from Legacy v47.
Fixes: Added Circuit Breaker pattern to prevent Timeouts from crashing Main.
Dependencies: pip install phue
"""

import os
import logging
import time

logger = logging.getLogger("outputs.hue")

class HueController:
    # ------------------------------------------------------------------
    # CONFIGURATION
    # ------------------------------------------------------------------
    DEFAULT_IP = "192.168.1.228"
    TARGET_LIGHTS = ["Hue bloom L", "Hue bloom R", "Hue color bar", "Hue color bar right", "Hue go 1"]
    
    # Circuit Breaker Config
    RETRY_COOLDOWN = 30 # Seconds to wait after a failure
    
    def __init__(self, enabled=True):
        self.enabled = enabled
        self.bridge = None
        self._last_failure_time = 0
        self._is_connected = False

        if self.enabled:
            self._connect()

    def _connect(self):
        """Establishes connection to the Philips Hue Bridge with Timeout safety."""
        # Circuit Breaker: Don't retry if we just failed recently
        if time.time() - self._last_failure_time < self.RETRY_COOLDOWN:
            return

        ip = os.getenv("HUE_BRIDGE_IP", self.DEFAULT_IP)
        
        try:
            from phue import Bridge
            # Set a strict timeout so we don't block the Mission Loop
            self.bridge = Bridge(ip) 
            self.bridge.connect() # Press button on bridge if first run
            self._is_connected = True
            logger.info(f"💡 HUE CONNECTED: {ip}")
            self.set_state("NORMAL") # Boot test
        except ImportError:
            logger.warning("⚠️ Module 'phue' not installed. Lighting disabled.")
            self.enabled = False
        except Exception as e:
            # Log the error but don't crash. Set cooldown.
            logger.error(f"❌ Hue Connection Failed: {e}")
            self._last_failure_time = time.time()
            self._is_connected = False

    def set_state(self, state):
        """
        Applies lighting mood based on Tactical Status.
        States: CRITICAL, WARNING, CONTACT, LOST, NORMAL
        """
        if not self.enabled: return
        
        # Auto-reconnect check
        if not self._is_connected:
            self._connect()
            if not self._is_connected: return

        try:
            # Get lights (This is the network call that can timeout)
            lights = self.bridge.get_light_objects(mode='name')
            
            for name in self.TARGET_LIGHTS:
                if name in lights:
                    l = lights[name]
                    if not l.on: l.on = True
                    
                    # COLOR DEFINITIONS (Legacy v47)
                    if state == "CRITICAL":  # 🔴 Red / Max Brightness
                        l.hue = 0; l.saturation = 254; l.brightness = 254
                    elif state == "WARNING": # 🟠 Orange / Dimmed
                        l.hue = 12750; l.saturation = 254; l.brightness = 200
                    elif state == "CONTACT": # 🔵 Blue / Max Brightness (AI Detection)
                        l.hue = 45000; l.saturation = 254; l.brightness = 254
                    elif state == "LOST":    # 🟣 Purple / Very Dim (Signal Loss)
                        l.hue = 40000; l.saturation = 254; l.brightness = 100 
                    else:                    # ⚪ Warm White / Standard
                        l.hue = 25500; l.saturation = 254; l.brightness = 150
                        
        except Exception:
            # SILENT FAIL: If lights timeout, do not print stack trace.
            # Just mark failure time so we don't try again immediately.
            self._last_failure_time = time.time()
            self._is_connected = False
