import random

import requests
import time
import os
import csv
import math
from risk_calculator import assess_risk
from ai_predictor import AIDronePredictor

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
if 'ai_predictor' not in globals():
    try:
        ai_predictor = AIDronePredictor('drone_model.h5')
        print("✅ AI predictor loaded.")
    except Exception as e:
        ai_predictor = None
        print(f"⚠️ AI predictor could not load: {e}")

def build_prediction_history(drone_obj, current_alt):
    """
    Builds exactly the structure expected by normalize_sequence():
    [{"lat": ..., "lng": ..., "alt": ...}, ...]
    """
    history = drone_obj.get("history", [])
    coords = []

    for p in history:
        lat = p.get("lat")
        lng = p.get("lng")
        if lat is not None and lng is not None:
            coords.append({
                "lat": lat,
                "lng": lng,
                "alt": current_alt
            })

    curr_lat = drone_obj.get("droneData", {}).get("location", {}).get("lat")
    curr_lng = drone_obj.get("droneData", {}).get("location", {}).get("lng")

    if curr_lat is not None and curr_lng is not None:
        coords.append({
            "lat": curr_lat,
            "lng": curr_lng,
            "alt": current_alt
        })

    if len(coords) < 10:
        return None

    return coords[-10:]




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

def generate_synthetic_data():
    """Generates artificial drones with the same schema as the live API."""
    synthetic_drones = []
    base_lat, base_lng = 46.7700, 23.6000  # Cluj-Napoca

    for i in range(3):
        sn = f"TEST-DRONE-{i:03d}"
        lat = base_lat + random.uniform(-0.03, 0.03)
        lng = base_lng + random.uniform(-0.03, 0.03)

        pilot_lat = lat + random.uniform(-0.01, 0.01)
        pilot_lng = lng + random.uniform(-0.01, 0.01)

        speed = random.choice([5, 12, 25, 40])
        heading = random.uniform(0, 360)
        altitude = random.randint(40, 200)
        history = []
        for step in range(10, 0, -1):
            history.append({
                "lat": lat - step * 0.0008 * math.cos(math.radians(heading)),
                "lng": lng - step * 0.0008 * math.sin(math.radians(heading))
            })
        synthetic_drones.append({
            "id": 10000 + i,
            "trackId": f"track-{i}",
            "serial": sn,
            "droneId": f"ALPHA-{i}",
            "pilotId": f"PILOT-{random.randint(100, 999)}",
            "manufacturer": "DJI",
            "model": "Synthetic",
            "history": history,
            "droneData": {
                "location": {"lat": lat, "lng": lng},
                "altitudes": {
                    "agl": altitude,
                    "ato": altitude,
                    "amsl": None,
                    "geodetic": altitude + 120
                },
                "groundSpeed": speed,
                "verticalSpeed": random.choice([-2, 0, 3]),
                "orientation": heading,   # IMPORTANT: orientation, not heading
                "likelihood": None,
                "uncertainty": None,
                "state": {
                    "id": 2,
                    "name": "Airborne"
                }
            },
            "pilotData": {
                "id": 20000 + i,
                "location": {
                    "lat": pilot_lat,
                    "lng": pilot_lng
                },
                "likelihood": None,
                "uncertainty": None
            },
            "timestamp": {
                "date": time.strftime("%Y-%m-%d %H:%M:%S.000000"),
                "timezone_type": 3,
                "timezone": "Europe/Bucharest"
            }
        })

    return synthetic_drones


def process_drones_for_ui():
    headers = {"Authorization": f"Bearer {TOKEN_IANNIS}"}
    try:
        resp = requests.get(f"{SENSOR_URL}/api/fused-data/map/50000/0", headers=headers, timeout=5)
        raw_data = resp.json()
        if not raw_data or not isinstance(raw_data, list):
            raw_data = []
    except Exception:
        raw_data = []
    raw_data.extend(generate_synthetic_data())

    unique_drones = {}

    for d in raw_data:
        sn = d.get('serial') or d.get('trackId') or d.get('id')
        if not sn:
            continue

        drone_id = d.get('droneId') or sn

        status, dist, trend, hdg, alt, reason, zone, speed = assess_risk(d)

        log_incident(drone_id, status, dist, trend, reason)

        curr_lat = d.get('droneData', {}).get('location', {}).get('lat')
        curr_lng = d.get('droneData', {}).get('location', {}).get('lng')
        predicted_path = []

        if ai_predictor is not None:
            try:
                pred_history = build_prediction_history(d, alt)
                print(f"{drone_id} history_length: {len(pred_history) if pred_history is not None else 0}")
                if pred_history is not None:
                    pred_coords = ai_predictor.predict_path(pred_history)
                    print(f"{drone_id} pred_coords: {pred_coords}")

                    if pred_coords is not None:
                        # Convert model output to [lng, lat] for Pydeck
                        predicted_path = [[float(p[1]), float(p[0])] for p in pred_coords]
                        print(f"{drone_id} predicted_path points: {len(predicted_path)}")
            except Exception as e:
                print(f"Prediction failed for {drone_id}: {e}")
                predicted_path = []
        else:
            print("ai_predictor is None")
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
            "predicted_path": predicted_path,
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