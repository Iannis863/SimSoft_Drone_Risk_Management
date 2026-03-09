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


def start_monitor():
    token = TOKEN_IANNIS
    if not token:
        print("Failed to authenticate. Check config.py.")
        return

    headers = {"Authorization": f"Bearer {token}"}
    endpoint = f"{SENSOR_URL}/api/fused-data/map/10000/0"

    print("--- RADAR INITIALIZING: SECTOR CLUJ ---")

    try:
        while True:
            resp = requests.get(endpoint, headers=headers)
            if resp.status_code == 200:
                drones = resp.json()
                os.system('cls' if os.name == 'nt' else 'clear')

                print(f"--- FLUX.AERO ROGUE DRONE RADAR | {time.strftime('%H:%M:%S')} ---")
                print(f"{'ID':<10} | {'STATUS':<12} | {' DISTANCE TO ZONE':<10} | {'CLOSEST ZONE':<20}")
                print("-" * 65)

                current_loop_serials = []

                for d in drones:
                    status, dist, trend, heading, alt, reason, zone_name = assess_risk(d)

                    # Filter for local sector (50km)
                    if dist < 50000:
                        # Anchor to Serial, then TrackId, then ID
                        sn = d.get('serial') or d.get('trackId') or d.get('id')
                        current_loop_serials.append(sn)

                        # Mission Tracking Logic
                        if sn not in active_missions:
                            active_missions[sn] = {
                                'start_time': time.time(),
                                'max_alt': alt
                            }
                        if alt > active_missions[sn]['max_alt']:
                            active_missions[sn]['max_alt'] = alt

                        # Log Alerts
                        if status != "🟢 CLEAR":
                            log_incident(sn, status, dist, trend, reason)

                        # Console Display
                        print(f"{str(sn)[:15]:<15} | {status:<12} | {int(dist):<6}m | {trend:<10} | {int(heading):<3}° | {alt}m")

                # Check for Landings/Exits
                for sn in list(active_missions.keys()):
                    if sn not in current_loop_serials:
                        process_flight_summary(sn, active_missions[sn])
                        del active_missions[sn]

            else:
                print(f"API Error: {resp.status_code}")

            time.sleep(3)  # Optimized refresh for SimSoft latency

    except KeyboardInterrupt:
        print("\nSession saved. Radar offline.")