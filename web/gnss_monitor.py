#!/usr/bin/env python3
"""
gnss_monitor.py — GNSS Health & Anomaly Detection Service
==========================================================
Subscribes to +/gnss and +/gnss-sky, computes rolling anomaly detection
for jamming/spoofing, publishes results to sensor-core/gnss-health.

Part of SecuringSkies platform. Does NOT modify any existing services.
"""
import json
import time
import math
import os
import ssl
import logging
from collections import deque, defaultdict
import paho.mqtt.client as mqtt

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("gnss-monitor")

# --- Config ---
MQTT_HOST = os.getenv("MQTT_HOST", "mqtt.securingskies.eu")
MQTT_PORT = int(os.getenv("MQTT_PORT", "8883"))
MQTT_USER = os.getenv("MQTT_USER", "team9")
PUBLISH_TOPIC = "sensor-core/gnss-health"
PUBLISH_INTERVAL = 2.0
BUFFER_SIZE = 300  # ~5 min at 1Hz

# Known true positions
TRUE_POS = {
    "sensor-north": {"lat": 60.319555, "lon": 24.830816, "alt": 95.0},
    "sensor-east":  {"lat": 60.374053, "lon": 25.249058, "alt": 68.0},
    "sensor-west":  {"lat": 60.130850, "lon": 24.512939, "alt": 21.0},
}

# --- Helpers ---
def haversine_m(lat1, lon1, lat2, lon2):
    R = 6371000
    rlat1, rlat2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(rlat1)*math.cos(rlat2)*math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))


def median(values):
    if not values:
        return 0
    s = sorted(values)
    n = len(s)
    return s[n//2] if n % 2 else (s[n//2-1] + s[n//2]) / 2


def std_dev(values):
    if len(values) < 2:
        return 0.0
    m = sum(values) / len(values)
    return math.sqrt(sum((v - m)**2 for v in values) / (len(values) - 1))


# --- State ---
buffers = defaultdict(lambda: deque(maxlen=BUFFER_SIZE))
sky_data = {}  # latest satellite info per sensor


def load_mqtt_password():
    p = os.getenv("MQTT_PASS")
    if p:
        return p
    try:
        with open("/etc/securing-skies/mqtt_secret") as f:
            return f.read().strip()
    except OSError:
        log.error("No MQTT password available")
        return ""


def detect_alerts(sensor, buf, all_deviations):
    """Detect jamming/spoofing for a single sensor."""
    alerts = []
    if not buf:
        return alerts

    latest = buf[-1]
    mode = latest.get("mode", 0)
    eph = latest.get("eph_m", 0)
    speed = latest.get("speed_mps", 0)
    dev = latest.get("_deviation_m", 0)

    # Fix lost
    if mode < 2:
        alerts.append({"type": "fix_lost", "severity": "red", "reason": f"No GNSS fix (mode={mode})"})
        return alerts

    # Rolling eph median (baseline)
    eph_values = [s.get("eph_m", 0) for s in buf if s.get("eph_m", 0) > 0]
    eph_median = median(eph_values) if eph_values else 10.0

    # Mode drop detection
    recent_modes = [s.get("mode", 0) for s in list(buf)[-10:]]
    older_modes = [s.get("mode", 0) for s in list(buf)[-30:-10]]
    if older_modes and recent_modes:
        if max(older_modes) >= 3 and max(recent_modes) < 3:
            alerts.append({"type": "jamming_suspected", "severity": "orange",
                           "reason": "Fix mode degraded from 3D to 2D"})

    # Satellite drop (if sky data available)
    sky = sky_data.get(sensor)
    if sky:
        sats_now = sky.get("sats_used", 0)
        sats_prev = sky.get("_prev_sats_used", sats_now)
        if sats_prev > 4 and sats_now < sats_prev * 0.5:
            alerts.append({"type": "jamming_suspected", "severity": "orange",
                           "reason": f"Satellite count dropped {sats_prev}→{sats_now}"})

    # Spoofing: good eph but large deviation
    if dev > 50 and eph < 10 and mode >= 3:
        alerts.append({"type": "spoofing_suspected", "severity": "red",
                       "reason": f"Position {dev:.0f}m from truth with eph={eph:.1f}m"})

    # Spoofing: speed on stationary receiver
    if speed > 2.0 and mode >= 3:
        alerts.append({"type": "spoofing_suspected", "severity": "red",
                       "reason": f"Speed {speed:.1f} m/s on stationary receiver"})

    # Jamming: eph spike
    if eph_median > 0 and eph > 3 * eph_median and len(eph_values) > 30:
        alerts.append({"type": "jamming_suspected", "severity": "orange",
                       "reason": f"EPH {eph:.1f}m > 3× baseline {eph_median:.1f}m"})

    # Degraded
    if not alerts:
        if eph_median > 0 and eph > 2 * eph_median and len(eph_values) > 30:
            alerts.append({"type": "degraded", "severity": "yellow",
                           "reason": f"EPH elevated: {eph:.1f}m (baseline {eph_median:.1f}m)"})
        h_std = std_dev([s.get("_deviation_m", 0) for s in list(buf)[-60:]])
        if h_std > 5.0:
            alerts.append({"type": "degraded", "severity": "yellow",
                           "reason": f"Position std {h_std:.1f}m"})

    # Cross-sensor consistency
    other_devs = [d for s, d in all_deviations.items() if s != sensor and d > 0]
    if other_devs and dev > 0:
        other_max = max(other_devs) if other_devs else 0
        if other_max > 0 and dev > 10 * other_max and dev > 20 and dev > buf[-1].get("eph_m", 999) * 2:
            alerts.append({"type": "spoofing_suspected", "severity": "red",
                           "reason": f"Deviation {dev:.0f}m while others <{other_max:.0f}m"})

    return alerts


def compute_health():
    """Compute health metrics for all sensors."""
    result = {"ts": time.time(), "sensors": {}}
    all_deviations = {}

    # First pass: compute deviations
    for sensor, buf in buffers.items():
        if not buf:
            continue
        latest = buf[-1]
        true = TRUE_POS.get(sensor)
        if true:
            dev = haversine_m(latest["lat"], latest["lon"], true["lat"], true["lon"])
            latest["_deviation_m"] = dev
            all_deviations[sensor] = dev

    # Second pass: full metrics + alerts
    for sensor in TRUE_POS:
        buf = buffers.get(sensor)
        if not buf:
            result["sensors"][sensor] = {"status": "offline", "alerts": []}
            continue

        latest = buf[-1]
        true = TRUE_POS[sensor]
        dev = all_deviations.get(sensor, 0)
        alt_dev = abs(latest.get("alt_m", true["alt"]) - true["alt"])

        # Rolling horizontal std
        devs = [s.get("_deviation_m", 0) for s in buf if "_deviation_m" in s]
        h_std = std_dev(devs[-60:]) if len(devs) > 1 else 0

        sky = sky_data.get(sensor, {})

        sensor_data = {
            "lat": latest.get("lat"),
            "lon": latest.get("lon"),
            "alt_m": latest.get("alt_m"),
            "horizontal_deviation_m": round(dev, 2),
            "alt_deviation_m": round(alt_dev, 2),
            "horizontal_std_m": round(h_std, 2),
            "eph_m": latest.get("eph_m", 0),
            "epv_m": latest.get("epv_m", 0),
            "speed_mps": latest.get("speed_mps", 0),
            "fix_mode": latest.get("mode", 0),
            "samples": len(buf),
            "sats_used": sky.get("sats_used"),
            "sats_visible": sky.get("sats_visible"),
            "snr_mean": sky.get("snr_mean"),
            "status": "ok",
            "alerts": [],
        }

        alerts = detect_alerts(sensor, buf, all_deviations)
        sensor_data["alerts"] = alerts
        if any(a["severity"] == "red" for a in alerts):
            sensor_data["status"] = "alert"
        elif any(a["severity"] == "orange" for a in alerts):
            sensor_data["status"] = "warning"
        elif any(a["severity"] == "yellow" for a in alerts):
            sensor_data["status"] = "degraded"

        result["sensors"][sensor] = sensor_data

    return result


# --- MQTT Callbacks ---
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        log.info("MQTT connected, subscribing...")
        client.subscribe("+/gnss")
        client.subscribe("+/gnss-sky")
    else:
        log.error("MQTT connect failed rc=%s", rc)


def on_message(client, userdata, msg):
    try:
        parts = msg.topic.split("/")
        sensor, dtype = parts[0], parts[1]
        payload = json.loads(msg.payload)

        if dtype == "gnss":
            true = TRUE_POS.get(sensor)
            if true:
                dev = haversine_m(payload["lat"], payload["lon"], true["lat"], true["lon"])
                payload["_deviation_m"] = dev
            buffers[sensor].append(payload)

        elif dtype == "gnss-sky":
            old_sats = sky_data.get(sensor, {}).get("sats_used", 0)
            sky_data[sensor] = payload
            sky_data[sensor]["_prev_sats_used"] = old_sats

    except Exception as e:
        log.debug("Parse error on %s: %s", msg.topic, e)


# --- Main ---
if __name__ == "__main__":
    log.info("GNSS Monitor starting — publishing to %s every %.0fs", PUBLISH_TOPIC, PUBLISH_INTERVAL)

    mqtt_pass = load_mqtt_password()
    client = mqtt.Client(client_id="gnss-monitor-v1")
    client.username_pw_set(MQTT_USER, mqtt_pass)
    client.tls_set(cert_reqs=ssl.CERT_REQUIRED)
    client.on_connect = on_connect
    client.on_message = on_message
    client.reconnect_delay_set(1, 60)

    client.connect(MQTT_HOST, MQTT_PORT, 60)
    client.loop_start()

    log.info("Connected to %s:%d", MQTT_HOST, MQTT_PORT)

    try:
        while True:
            time.sleep(PUBLISH_INTERVAL)
            health = compute_health()
            client.publish(PUBLISH_TOPIC, json.dumps(health), qos=0)
    except KeyboardInterrupt:
        log.info("Shutting down")
    finally:
        client.loop_stop()
        client.disconnect()
