
import requests
import time
import os
import csv
import math
from risk_calculator import assess_risk
from config import (
    SENSOR_URL,
    TOKEN_IANNIS,
    DRONE_BODY_RADIUS_M,
    ARROW_TIP_M,
    ARROW_WIDTH_M,
    ARROW_BACK_M
)
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
    if "CRITICAL" in s:
        return 3
    if "WARNING" in s:
        return 2
    return 1



def build_heading_arrow_polygon(lat, lng, heading_deg, tip_m=180, width_m=120, back_m=40):
    """
    Builds a small triangular arrow polygon connected to the drone point.
    The drone sits near the back/base of the triangle.
    0 = North, 90 = East.
    Returns coordinates in [lng, lat] format for Pydeck PolygonLayer.
    """
    if lat is None or lng is None:
        return []

    try:
        heading = float(heading_deg or 0)
    except Exception:
        heading = 0.0

    def project(lat0, lng0, bearing_deg, dist_m):
        rad = math.radians(bearing_deg)
        dlat = (dist_m * math.cos(rad)) / 111320.0
        dlng = (dist_m * math.sin(rad)) / (111320.0 * math.cos(math.radians(lat0)))
        return [lng0 + dlng, lat0 + dlat]

    # Tip in front
    tip = project(lat, lng, heading, tip_m)

    # Two rear corners behind and to the sides
    left_base = project(lat, lng, heading + 140, width_m)
    right_base = project(lat, lng, heading - 140, width_m)

    # Slight tail point behind center so it visually connects to the drone
    tail = project(lat, lng, heading + 180, back_m)

    return [tip, left_base, tail, right_base]

def process_drones_for_ui():
    headers = {"Authorization": f"Bearer {TOKEN_IANNIS}"}
    try:
        resp = requests.get(f"{SENSOR_URL}/api/fused-data/map/50000/0", headers=headers, timeout=5)
        raw_data = resp.json()
    except Exception:
        return []

    unique_drones = {}
    if not isinstance(raw_data, list):
        return []

    for d in raw_data:
        sn = d.get('serial') or d.get('trackId') or d.get('id')
        if not sn:
            continue

        drone_id = d.get('droneId') or sn

        status, dist, trend, hdg, alt, reason, zone, speed = assess_risk(d)

        log_incident(drone_id, status, dist, trend, reason)

        curr_lat = d.get('droneData', {}).get('location', {}).get('lat')
        curr_lng = d.get('droneData', {}).get('location', {}).get('lng')
        heading_arrow = build_heading_arrow_polygon(
            curr_lat,
            curr_lng,
            hdg,
            tip_m=ARROW_TIP_M,
            width_m=ARROW_WIDTH_M,
            back_m=ARROW_BACK_M
        )
        pilot_lat = d.get('pilotData', {}).get('location', {}).get('lat')
        pilot_lng = d.get('pilotData', {}).get('location', {}).get('lng')




        unique_drones[sn] = {
            "Drone ID": drone_id,
            "Pilot ID": d.get('pilotId') or d.get('pilotData', {}).get('id', 'Unknown'),
            "Status": status,
            "Distance (m)": int(dist),
            "Trend": trend,
            "Heading (°)": int(hdg) if hdg is not None else 0,
            "Altitude AGL": alt,
            "Latitude": curr_lat,
            "Longitude": curr_lng,
            "Pilot_Lat": pilot_lat,
            "Pilot_Lng": pilot_lng,
            "heading_arrow": heading_arrow,
            "Speed": speed,
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