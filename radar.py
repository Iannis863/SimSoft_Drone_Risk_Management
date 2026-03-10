import requests
import time
import os
import csv
from risk_calculator import assess_risk, get_heading
from config import SENSOR_URL, TOKEN_IANNIS

# Tracking for Flight Summaries
active_missions = {}


def log_incident(drone_id, status, dist, trend, reason):
    """Saves high-risk events to a CSV file with UTF-8 support."""
    file_exists = os.path.isfile('drone_incidents.csv')
    with open('drone_incidents.csv', 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Timestamp', 'ID', 'Status', 'Dist', 'Trend', 'Reason'])
        writer.writerow([time.strftime('%H:%M:%S'), drone_id, status, f"{int(dist)}m", trend, reason])


def process_flight_summary(serial, mission_data):
    """Prints a sleek summary once a drone hardware leaves the radar."""
    duration = int(time.time() - mission_data['start_time'])
    max_alt = mission_data['max_alt']

    print("\n" + "=" * 50)
    print(f"🛬 MISSION COMPLETE | Serial/ID: {serial}")
    print(f"Peak Altitude: {max_alt}m")
    print(f"Total Mission Time: {duration}s")
    print("=" * 50 + "\n")

def get_live_drones_raw():
    """Fetches one raw scan from the API."""
    token = TOKEN_IANNIS
    if not token:
        raise RuntimeError("Missing TOKEN_IANNIS in config.py")

    history_offset = 36000

    headers = {"Authorization": f"Bearer {token}"}
    endpoint = f"{SENSOR_URL}/api/fused-data/map/50000/0"

    resp = requests.get(endpoint, headers=headers, timeout=10)
    resp.raise_for_status()

    drones = resp.json()
    if not isinstance(drones, list):
        return []

    return drones
def process_drones_for_ui():
    """Fetches one scan and returns processed drone data for the UI."""
    drones = get_live_drones_raw()
    current_loop_serials = []
    processed = []

    for d in drones:
        status, dist, trend, hdg, alt, reason, name = assess_risk(d)

        # same local filtering as radar console
        if dist < 50000:
            sn = d.get('serial') or d.get('trackId') or d.get('id')
            current_loop_serials.append(sn)

            location = d.get('droneData', {}).get('location', {}) or {}
            pilot = d.get('pilotData', {}).get('id') or "Unknown"

            lat = location.get('lat')
            lng = location.get('lng')

            # Mission tracking logic
            if sn not in active_missions:
                active_missions[sn] = {
                    'start_time': time.time(),
                    'max_alt': alt
                }
            if alt > active_missions[sn]['max_alt']:
                active_missions[sn]['max_alt'] = alt

            # Log alerts
            if status != "🟢 CLEAR":
                log_incident(sn, status, dist, trend, reason)

            # Risk score for UI
            if "CRITICAL" in status.upper():
                risk_score = 90
            elif "WARNING" in status.upper():
                risk_score = 60
            elif "CLEAR" in status.upper():
                risk_score = 20
            else:
                risk_score = 0

            processed.append({
                "Drone ID": sn,
                "Pilot ID": pilot,
                "Status": status,
                "Risk Score": risk_score,
                "Distance (m)": int(dist),
                "Trend": trend,
                "Heading (°)": int(hdg),
                "Altitude AGL": alt,
                "Latitude": lat,
                "Longitude": lng,
                "Reasons": reason,
                "raw": d
            })


    for sn in list(active_missions.keys()):
        if sn not in current_loop_serials:
            process_flight_summary(sn, active_missions[sn])
            del active_missions[sn]

    return processed

def start_monitor():
    token = TOKEN_IANNIS
    if not token:
        print("Failed to authenticate. Check config.py.")
        return

    print("--- RADAR INITIALIZING: SECTOR CLUJ ---")

    try:
        while True:
            drones = process_drones_for_ui()
            os.system('cls' if os.name == 'nt' else 'clear')

            print(f"--- FLUX.AERO ROGUE DRONE RADAR | {time.strftime('%H:%M:%S')} ---")
            print(f"{'SERIAL/ID':<15} | {'STATUS':<12} | {'DIST':<8} | {'TREND':<10} | {'HDG':<5} | {'ALT'}")
            print("-" * 75)

            for d in drones:
                print(
                    f"{str(d['Drone ID'])[:15]:<15} | {d['Status']:<12} | {d['Distance (m)']:<6}m | "
                    f"{d['Trend']:<10} | {d['Heading (°)']:<3}° | {d['Altitude AGL']}m"
                )

            time.sleep(3)

    except KeyboardInterrupt:
        print("\nSession saved. Radar offline.")