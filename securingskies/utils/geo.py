"""
SecuringSkies Platform - Geospatial Utilities
=============================================
Version: 0.9.9
Role: Haversine math and 3D distance calculations for telemetry.
"""

import math

def calculate_distance(lat1, lon1, lat2, lon2):
    """Legacy 2D Distance (Surface only). Returns meters."""
    return calculate_distance_3d(lat1, lon1, 0, lat2, lon2, 0)

def calculate_distance_3d(lat1, lon1, alt1, lat2, lon2, alt2):
    """
    Calculate 3D distance between two points (incorporating altitude delta).
    Returns: Distance in meters (float).
    """
    if lat1 is None or lat2 is None:
        return 0.0

    R = 6371000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    # Haversine formula (Surface Distance)
    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    surface_dist = R * c

    # 3D Hypotenuse (incorporating Altitude)
    alt_diff = (alt2 or 0) - (alt1 or 0)
    
    return math.sqrt(surface_dist**2 + alt_diff**2)
