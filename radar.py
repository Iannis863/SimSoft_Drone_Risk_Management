import requests
import time
import os
import csv
from risk_calculator import assess_risk
from config import SENSOR_URL, TOKEN_IANNIS

# --- PERSISTENCE FIX ---
# This ensures dictionaries survive Streamlit's frequent re-imports
if 'active_missions' not in globals():
    active_missions = {}

if 'drone_alert_states' not in globals():
    drone_alert_states = {}

def log_incident(drone_id, status, dist, trend, reason):
    """
    Logs EVERY drone once when first seen.
    Logs again ONLY if the status changes (e.g., Clear -> Warning).
    """
    global drone_alert_states

    # 1. Determine if this is a new drone or a status change
    last_status = drone_alert_states.get(drone_id)

    if last_status == status:
        # No change in status, and we've already logged it once. Skip.
        return

    # 2. Update the state tracker to the new status
    drone_alert_states[drone_id] = status

    # 3. Write the event to the CSV
    file_path = 'drone_incidents.csv'
    file_exists = os.path.isfile(file_path)

    try:
        with open(file_path, 'a', newline='', encoding='utf-8') as f:
            # QUOTE_MINIMAL prevents the "7 fields vs 6" ParserError by wrapping text in " "
            writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)

            if not file_exists:
                writer.writerow(['Date', 'Timestamp', 'ID', 'Status', 'Dist', 'Trend', 'Reason'])

            current_date = time.strftime('%Y-%m-%d')
            current_time = time.strftime('%H:%M:%S')

            writer.writerow([
                current_date,
                current_time,
                drone_id,
                status,
                f"{int(dist)}m",
                trend,
                reason
            ])

            # Console feedback for the "Boss"
            action = "INITIAL CONTACT" if last_status is None else "STATUS CHANGE"
            print(f"📝 LOGGED [{action}]: {drone_id} is now {status}")

    except Exception as e:
        print(f"❌ logging error: {e}")

def reset_radar_state():
    """Resets the internal memory so active drones are re-logged as new events."""
    global drone_alert_states
    drone_alert_states.clear()
    print("🧹 Radar internal state cleared. Re-logging active drones...")

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

    headers = {"Authorization": f"Bearer {token}"}
    endpoint = f"{SENSOR_URL}/api/fused-data/map/50000/0"

    resp = requests.get(endpoint, headers=headers, timeout=180)
    resp.raise_for_status()

    drones = resp.json()
    if not isinstance(drones, list):
        return []

    return drones

def process_drones_for_ui():
    """Fetches and de-duplicates drone data."""
    raw_drones = get_live_drones_raw()
    current_loop_serials = []

    # Use a dictionary to store unique drones (Key = Drone ID)
    unique_drones = {}

    for d in raw_drones:
        status, dist, trend, hdg, alt, reason, name = assess_risk(d)

        sn = d.get('serial') or d.get('trackId') or d.get('id')
        if not sn: continue

        # Local filtering (within 50km)
        if dist < 50000:
            current_loop_serials.append(sn)

            location = d.get('droneData', {}).get('location', {}) or {}
            pilot = d.get('pilotData', {}).get('id') or "Unknown"

            # Mission tracking
            if sn not in active_missions:
                active_missions[sn] = {'start_time': time.time(), 'max_alt': alt}
            if alt > active_missions[sn]['max_alt']:
                active_missions[sn]['max_alt'] = alt

            # Log incidents
            log_incident(sn, status, dist, trend, reason)

            risk_score = 90 if "CRITICAL" in status.upper() else 60 if "WARNING" in status.upper() else 20

            unique_drones[sn] = {
                "Drone ID": sn,
                "Pilot ID": pilot,
                "Status": status,
                "Risk Score": risk_score,
                "Distance (m)": int(dist),
                "Trend": trend,
                "Heading (°)": int(hdg),
                "Altitude AGL": alt,
                "Latitude": location.get('lat'),
                "Longitude": location.get('lng'),
                "Reasons": reason,
                "raw": d
            }

    # Handle mission completion for drones that disappeared
    for sn in list(active_missions.keys()):
        if sn not in current_loop_serials:
            process_flight_summary(sn, active_missions[sn])
            del active_missions[sn]
            if sn in drone_alert_states:
                del drone_alert_states[sn]

    return list(unique_drones.values())

def start_monitor():
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