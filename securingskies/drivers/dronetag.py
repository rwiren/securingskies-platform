"""
SecuringSkies Platform - Dronetag Driver (Remote ID)
====================================================
Standard: ASTM F3411 / ASD-STAN
Role: Tracks Remote ID broadcasts from Dronetag sensors.
"""

import json
import logging
import math

logger = logging.getLogger("driver.dronetag")

class DronetagDriver:
    def __init__(self):
        self.packet_count = 0

    def parse(self, topic, payload):
        """Ingests Dronetag MQTT JSON."""
        try:
            if isinstance(payload, bytes): payload = payload.decode('utf-8')
            data = json.loads(payload)
            self.packet_count += 1
            
            # Extract ID (Sensor ID or UAS ID)
            raw_id = data.get('sensor_id', data.get('uas_id', 'UNK'))
            tid = f"TAG-{raw_id[-4:]}"
            
            # Location & Altitude Logic
            loc = data.get('location', {})
            lat = loc.get('latitude')
            lon = loc.get('longitude')
            
            # Altitude Priority: MSL > HAE > Baro
            alt = 0.0
            if 'altitudes' in data:
                for a in data['altitudes']:
                    if a.get('type') == 'MSL': 
                        alt = a.get('value', 0)
                        break
                if alt == 0 and data['altitudes']:
                    alt = data['altitudes'][0].get('value', 0)
            elif 'altitude' in data:
                alt = float(data.get('altitude', 0))

            # Velocity
            speed = 0.0
            vel = data.get('velocity', {})
            if 'horizontal_speed' in vel:
                speed = vel.get('horizontal_speed', 0)
            elif 'x' in vel: # Vector calculation
                speed = math.sqrt(vel['x']**2 + vel['y']**2)

            return {
                'tid': tid,
                'type': 'AIR',
                'lat': lat,
                'lon': lon,
                'alt': alt,
                'speed': speed,
                'batt': -1, # Remote ID rarely sends battery
                'acc': loc.get('accuracy', 0),
                'nav': 'Remote ID',
                'mode': 'AIRBORNE'
            }
            
        except Exception:
            pass
        return None
