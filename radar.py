import requests
import time
import os
import csv
from risk_calculator import assess_risk
from config import SENSOR_URL, TOKEN_IANNIS
from utils import get_status_color

# Persistence for state tracking
if 'active_missions' not in globals():
    active_missions = {}
if 'drone_alert_states' not in globals():
    drone_alert_states = {}


def log_incident(drone_id, status, dist, trend, reason):
    global drone_alert_states
    if drone_alert_states.get(drone_id) == status:
        return
    drone_alert_states[drone_id] = status
    file_path = 'drone_incidents.csv'
    try:
        file_exists = os.path.isfile(file_path)
        with open(file_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
            if not file_exists:
                writer.writerow(['Date', 'Timestamp', 'Drone ID', 'Status', 'Distance', 'Trend', 'Reason'])
            writer.writerow(
                [time.strftime('%Y-%m-%d'), time.strftime('%H:%M:%S'), drone_id, status, dist, trend, reason])
    except Exception as e:
        print(f"Log Error: {e}")


def status_priority(status):
    s = str(status).upper()
    if "CRITICAL" in s: return 3
    if "WARNING" in s: return 2
    return 1


def process_drones_for_ui():
    headers = {"Authorization": f"Bearer {TOKEN_IANNIS}"}
    try:
        # Using your updated fused-data endpoint
        resp = requests.get(f"{SENSOR_URL}/api/fused-data/map/50000/0", headers=headers, timeout=5)
        raw_data = resp.json()
    except Exception:
        return []

    unique_drones = {}
    if not isinstance(raw_data, list):
        return []

    for d in raw_data:
        sn = d.get('serial') or d.get('trackId') or d.get('id')
        if not sn: continue
        drone_id = d.get('droneId') or sn

        status, dist, trend, hdg, alt, reason, zone, speed = assess_risk(d)

        log_incident(drone_id, status, dist, trend, reason)

        from predictor import project_future_position
        curr_lat = d.get('droneData', {}).get('location', {}).get('lat')
        curr_lng = d.get('droneData', {}).get('location', {}).get('lng')

        f_lat, f_lng = project_future_position(curr_lat, curr_lng, hdg, speed, 20)

        # Build the "Map-Ready" dictionary immediately
        unique_drones[sn] = {
            "Drone ID": drone_id,
            "Pilot ID": d.get('pilotId', 'Unknown'),
            "Status": status,
            "Distance (m)": int(dist),
            "Trend": trend,
            "Heading (°)": int(hdg),
            "Altitude AGL": alt,
            "Latitude": d.get('droneData', {}).get('location', {}).get('lat'),
            "Longitude": d.get('droneData', {}).get('location', {}).get('lng'),
            "Future_Lat": f_lat,
            "Future_Lng": f_lng,
            "Reasons": reason,
            "Zone": zone,
            "Label": f"{drone_id} ({alt}m)",
            "color": get_status_color(status),
            "elevation": alt,
            "raw": d
        }
    return list(unique_drones.values())


def reset_radar_state():
    global active_missions, drone_alert_states
    active_missions.clear()
    drone_alert_states.clear()