import requests
import time
import os
import csv
from risk_calculator import assess_risk
from config import SENSOR_URL, TOKEN_IANNIS
from utils import get_status_color

# Persistence for state tracking
if 'drone_history_buffer' not in globals():
    drone_history_buffer = {}
if 'drone_alert_states' not in globals():
    drone_alert_states = {}


def log_incident(drone_id, status, dist, reason):
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
                writer.writerow(['Date', 'Time', 'ID', 'Status', 'Dist', 'Reason'])
            writer.writerow([
                time.strftime('%Y-%m-%d'), time.strftime('%H:%M:%S'),
                drone_id, status, dist, reason
            ])
    except Exception as e:
        print(f"Log Error: {e}")


def status_priority(status):
    """
    Assigns a numerical rank to statuses for sorting and UI prominence.
    Higher number = Higher urgency.
    """
    s = str(status).upper()

    # 1. Active Emergency (Red)
    if "CRITICAL" in s or "BREACH" in s:
        return 4

        # 2. AI Intercept (Purple) - High Stakes Proactive Alert
    if "PREDICTIVE" in s:
        return 3

        # 3. Proximity Caution (Yellow)
    if "WARNING" in s:
        return 2

        # 4. Routine Operations (Green)
    return 1


def process_drones_for_ui():
    global drone_history_buffer
    headers = {"Authorization": f"Bearer {TOKEN_IANNIS}"}

    try:
        resp = requests.get(f"{SENSOR_URL}/api/fused-data/map/50000/0", headers=headers, timeout=5)
        raw_data = resp.json()
    except:
        return []

    unique_drones = {}
    if not isinstance(raw_data, list): return []

    for d in raw_data:
        sn = d.get('serial') or d.get('trackId') or d.get('id')
        if not sn: continue

        if sn not in drone_history_buffer:
            drone_history_buffer[sn] = []

        curr_lat = d.get('droneData', {}).get('location', {}).get('lat')
        curr_lng = d.get('droneData', {}).get('location', {}).get('lng')

        drone_history_buffer[sn].append({
            'lat': curr_lat,
            'lng': curr_lng,
            'droneData': d.get('droneData', {})
        })

        if len(drone_history_buffer[sn]) > 10:
            drone_history_buffer[sn].pop(0)

        status, dist, trend, hdg, alt, reason, zone, speed, ai_path = assess_risk(d, drone_history_buffer[sn])

        log_incident(sn, status, int(dist), reason)

        if ai_path is not None:
            f_lat, f_lng = ai_path[-1][0], ai_path[-1][1]
        else:
            f_lat, f_lng = None, None

        unique_drones[sn] = {
            "Drone ID": sn,
            "Status": status,
            "Distance (m)": int(dist),
            "Heading (°)": int(hdg),
            "Altitude AGL": alt,
            "Latitude": curr_lat,
            "Longitude": curr_lng,
            "Future_Lat": f_lat,
            "Future_Lng": f_lng,
            "Zone": zone,
            "Reasons": reason,
            "color": get_status_color(status),
            "elevation": alt,
            "raw": d
        }

    return list(unique_drones.values())


def reset_radar_state():
    global drone_history_buffer, drone_alert_states
    drone_history_buffer.clear()
    drone_alert_states.clear()