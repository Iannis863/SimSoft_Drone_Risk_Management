import requests
import time
import os
from threat_engine import assess_risk, get_heading
from config import SENSOR_URL, TOKEN_IANNIS
import csv


def start_monitor():
    token = TOKEN_IANNIS
    if not token: return

    headers = {"Authorization": f"Bearer {token}"}
    endpoint = f"{SENSOR_URL}/api/fused-data/map/10000/0"

    print("\n--- FLUX.AERO ROGUE DRONE RADAR ---")
    try:
        while True:
            resp = requests.get(endpoint, headers=headers)
            if resp.status_code == 200:
                drones = resp.json()
                os.system('cls' if os.name == 'nt' else 'clear')  # Refresh screen
                print(f"Active Drones: {len(drones)} | Refreshed: {time.strftime('%H:%M:%S')}")
                print(f"{'ID':<10} | {'STATUS':<12} | {'DIST':<8} | {'TREND':<8} | {'HEADING':<8} | {'ALTITUDE':<8}")
                print("-" * 50)

                for d in drones:
                    status, dist, trend, reason, altitude = assess_risk(d)
                    heading = get_heading(d.get('history', []))

                    # Log if it's not 'CLEAR'
                    if status != "🟢 CLEAR":
                        log_incident(d['id'], status, dist, trend, reason)

                    print(f"{d['id']:<10} | {status:<12} | {int(dist)}m | {trend:<12} | {heading:<12} | {altitude:<8}")

            time.sleep(2)
    except KeyboardInterrupt:
        print("\nRadar shut down.")

def log_incident(drone_id, status, dist, trend, reason):
    file_exists = os.path.isfile('incidents.csv')
    with open('incidents.csv', 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Timestamp', 'Drone_ID', 'Status', 'Distance', 'Trend', 'Reason'])

        writer.writerow([time.strftime('%Y-%m-%d %H:%M:%S'), drone_id, status, f"{int(dist)}m", trend, reason])


if __name__ == "__main__":
    start_monitor()