"""
SecuringSkies Platform - Autel Enterprise Driver (v2.1)
=======================================================
COMPATIBILITY: Autel Smart Controller V3 / Evo Max 4T
SCHEMA: Full Telemetry + RTH Safety Metrics
"""

import json
import logging

# Configure Module Logger
logger = logging.getLogger("driver.autel")

class AutelDriver:
    # ------------------------------------------------------------------
    # 1. HARDWARE DEFINITIONS
    # ------------------------------------------------------------------
    AI_CLASSES = {
        3: "Car", 4: "Human", 5: "Cyclist", 6: "Truck", 
        30: "Human",  # CONFIRMED: Evo Max 4T Human Class
        34: "Drone", 35: "Smoke", 36: "Fire"
    }

    HIGH_VALUE_TARGETS = [4, 30, 34, 36]

    def __init__(self):
        self.packet_count = 0

    # ------------------------------------------------------------------
    # 2. MAIN PARSER
    # ------------------------------------------------------------------
    def parse(self, topic, payload):
        """Ingests raw MQTT payload and returns a Standardized Tactical Object."""
        try:
            if isinstance(payload, bytes): payload = payload.decode('utf-8')
            data = json.loads(payload)
            self.packet_count += 1
            
            if 'osd' in topic and 'data' in data:
                return self._parse_osd(topic, data['data'])
            elif 'state' in topic and data.get('method') == 'target_detect_result_report':
                return self._parse_vision(data)
            elif topic.endswith('/sn'):
                return self._parse_heartbeat(data)
        except Exception: pass
        return None

    # ------------------------------------------------------------------
    # 3. INTERNAL DECODERS
    # ------------------------------------------------------------------
    def _parse_osd(self, topic, osd_data):
        results = []
        
        # 1. Parse Controller
        if osd_data.get('capacity_percent', 0) > 0 and 'drone_list' in osd_data:
            sn = topic.split('/')[2] if len(topic.split('/')) > 2 else "UNK"
            results.append({
                'tid': f"CTRL-{sn[-4:]}",
                'type': 'GND_STATION',
                'lat': osd_data.get('latitude'),
                'lon': osd_data.get('longitude'),
                'batt': osd_data.get('capacity_percent'),
                'mode': 'Active',
                'storage': self._parse_storage(osd_data.get('storage', {}))
            })

        # 2. Parse Drone(s)
        if 'drone_list' in osd_data:
            for drone_raw in osd_data['drone_list']:
                # Merge Sibling Data (Gimbal/Battery Stats) if available in root
                full_drone_data = {**drone_raw, **self._find_sibling_data(osd_data)}
                parsed_uav = self._normalize_uav(full_drone_data)
                if parsed_uav: results.append(parsed_uav)
        
        # 3. Parse Direct Drone OSD
        elif ('height' in osd_data or 'battery' in osd_data) and 'drone_list' not in osd_data:
             sn = topic.split('/')[2] if len(topic.split('/')) > 2 else "UNK"
             if 'sn' not in osd_data: osd_data['sn'] = sn
             parsed_uav = self._normalize_uav(osd_data)
             if parsed_uav: results.append(parsed_uav)

        return results

    def _normalize_uav(self, raw):
        """Converts Autel proprietary fields to SecuringSkies Standard"""
        sn = raw.get('sn', 'UNK')
        
        # Battery & Safety
        batt = raw.get('battery', {})
        pct = batt.get('capacity_percent', raw.get('capacity_percent', 0))
        
        # RTK / GPS Logic
        pos_state = raw.get('position_state', {})
        rtk_used = pos_state.get('rtk_used', 0)
        is_fixed = pos_state.get('is_fixed', 0)
        sats = pos_state.get('gps_number', 0)
        
        nav_status = "GPS"
        accuracy_m = 10.0

        if rtk_used == 1:
            accuracy_m = 0.1
            nav_status = "RTK-FIX" if is_fixed == 3 else ("RTK-FLOAT" if is_fixed == 2 else "RTK")
        elif sats > 12:
            accuracy_m = 3.0
            nav_status = "GPS-3D"

        # Extended Telemetry
        gimbal = raw.get('gimbal_payload', {})
        link = raw.get('wireless_link', {})
        
        return {
            'tid': f"UAV-{sn[-4:]}",
            'type': 'AIR',
            'lat': raw.get('latitude'),
            'lon': raw.get('longitude'),
            'alt': raw.get('height', 0),
            'batt': pct,
            'batt_rth': batt.get('return_home_power', 0), # Power needed to RTH
            'batt_land': batt.get('landing_power', 0),    # Power needed to Land
            'home_dist': raw.get('home_distance', 0),
            'speed': float(raw.get('horizontal_speed', 0)) * 3.6,
            'heading': float(raw.get('attitude_head', 0)),
            'nav': nav_status,
            'acc': accuracy_m, 
            'sats': sats,
            'link_quality': link.get('sdr_quality', 0),
            'gimbal_pitch': gimbal.get('gimbal_pitch', 0)
        }

    def _find_sibling_data(self, osd_root):
        """Locates scattered data keys"""
        data = {}
        # Gimbal
        for key, val in osd_root.items():
            if isinstance(val, dict) and 'gimbal_pitch' in val:
                data['gimbal_payload'] = val
        # Battery Stats (sometimes at root data -> battery)
        if 'data' in osd_root and 'battery' in osd_root['data']:
             data['battery'] = osd_root['data']['battery']
        return data

    def _parse_storage(self, storage_data):
        if not storage_data: return "N/A"
        return f"{int((storage_data.get('used',0)/storage_data.get('total',1))*100)}%"

    def _parse_vision(self, data):
        sightings = {}
        for obj in data.get('data', {}).get('objs', []):
            if obj.get('cls_id') in self.HIGH_VALUE_TARGETS:
                name = self.AI_CLASSES.get(obj.get('cls_id'), "UNK")
                sightings[name] = sightings.get(name, 0) + 1
        return {'type': 'AI_EVENT', 'sightings': sightings} if sightings else None

    def _parse_heartbeat(self, data):
        return None
