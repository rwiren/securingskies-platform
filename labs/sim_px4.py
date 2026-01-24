"""
Simple PX4 Simulator (Fixed)
============================
Generates fake MAVLink packets (UDP) to test the Bridge.
Flies a circle around Vantaa.
"""
import time
import math
import sys

try:
    from pymavlink import mavutil
except ImportError:
    print("❌ MISSING DEPS: pip install pymavlink")
    sys.exit(1)

# TARGET: Where the Bridge is listening
TARGET_IP = "127.0.0.1"
TARGET_PORT = 14550

# CENTER POINT (Vantaa)
LAT_0 = 60.3195
LON_0 = 24.8310

def run():
    print(f"🎮 PX4 SIMULATOR: Sending to {TARGET_IP}:{TARGET_PORT}")
    
    master = mavutil.mavlink_connection(f'udpout:{TARGET_IP}:{TARGET_PORT}', source_system=1)
    boot_time = time.time()
    
    angle = 0
    try:
        while True:
            # 1. Time Calculation
            time_boot_ms = int((time.time() - boot_time) * 1000)

            # 2. Position Calculation (Circle)
            lat = LAT_0 + 0.002 * math.cos(angle)
            lon = LON_0 + 0.002 * math.sin(angle)
            alt = 120 
            
            # 3. Heading Calculation (CRITICAL FIX)
            # Convert radians to degrees, wrap mod 360, convert to centidegrees
            heading_deg = (angle * 57.2958) % 360
            heading_cdeg = int(heading_deg * 100)

            # 4. Send Heartbeat
            master.mav.heartbeat_send(
                mavutil.mavlink.MAV_TYPE_QUADROTOR,
                mavutil.mavlink.MAV_AUTOPILOT_PX4,
                0, 0, 0
            )

            # 5. Send Position
            master.mav.global_position_int_send(
                time_boot_ms,
                int(lat * 1e7),
                int(lon * 1e7),
                int(alt * 1000),
                int(alt * 1000),
                0, 0, 0, 
                heading_cdeg # Now safely defined
            )

            print(f"📡 PX4 Sending: {lat:.5f}, {lon:.5f} | Hdg: {heading_deg:.1f}°", end="\r")
            
            angle += 0.05
            time.sleep(0.5) 
            
    except KeyboardInterrupt:
        print("\n🛑 Sim Stopped.")

if __name__ == "__main__":
    run()
