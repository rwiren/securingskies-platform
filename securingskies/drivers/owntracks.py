"""
SecuringSkies Platform - OwnTracks Driver
=========================================
Tracks Ground Assets (Pilots, Vehicles) via standard HTTP/MQTT JSON.
"""

import json
import logging

logger = logging.getLogger("driver.owntracks")

class OwnTracksDriver:
    def __init__(self):
        self.packet_count = 0

    def parse(self, topic, payload):
        """
        Ingests OwnTracks JSON.
        Returns Standardized Tactical Object.
        """
        try:
            if isinstance(payload, bytes):
                payload = payload.decode('utf-8')
            
            data = json.loads(payload)
            self.packet_count += 1
            
            # Filter for Location Updates only
            if data.get('_type') == 'location':
                return self._normalize_ground_asset(data)
                
        except Exception as e:
            # logger.error(f"OwnTracks Parse Error: {e}")
            pass
        return None

    def _normalize_ground_asset(self, raw):
        """Standardizes phone telemetry"""
        tid = raw.get('tid', 'RW') # Default to RW if missing
        
        # Battery conversion (OwnTracks sends integer 0-100)
        batt = raw.get('batt', -1)
        
        # Speed conversion (km/h)
        # OwnTracks usually sends km/h directly, but let's ensure it's a float
        speed = float(raw.get('vel', 0))
        
        # Accuracy (Meters)
        acc = raw.get('acc', 0)
        
        return {
            'tid': tid,
            'type': 'GROUND',
            'lat': raw.get('lat'),
            'lon': raw.get('lon'),
            'alt': raw.get('alt', 0),
            'batt': batt,
            'speed': speed,
            'course': raw.get('cog', 0),
            'acc': acc,
            'nav': 'GPS', # Phones are always GPS
            'mode': 'Active'
        }
