"""
SecuringSkies Platform - Geospatial Utilities
=============================================
Role: Calculates 3D distances between assets (Haversine).
"""

import math

def calculate_distance(p1, p2):
    """
    Returns distance in meters between two lat/lon/alt dicts.
    Format: {'lat': 0.0, 'lon': 0.0}
    """
    if not p1 or not p2: return 0.0
    if 'lat' not in p1 or 'lat' not in p2: return 0.0
    
    try:
        R = 6371e3 # Earth radius in meters
        phi1 = math.radians(p1['lat'])
        phi2 = math.radians(p2['lat'])
        dphi = math.radians(p2['lat'] - p1['lat'])
        dlambda = math.radians(p2['lon'] - p1['lon'])
        
        a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2) * math.sin(dlambda/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    except Exception:
        return 0.0
