import requests
import time
import os
from threat_engine import assess_risk, get_heading
from config import SENSOR_URL, TOKEN_IANNIS


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
                print(f"{'ID':<10} | {'STATUS':<12} | {'DIST':<8} | {'HEADING':<8}")
                print("-" * 50)

                for d in drones:
                    status, dist = assess_risk(d)
                    heading = get_heading(d.get('history', []))
                    print(f"{d['id']:<10} | {status:<12} | {int(dist)}m | {int(heading)}°")

            time.sleep(2)
    except KeyboardInterrupt:
        print("\nRadar shut down.")


if __name__ == "__main__":
    start_monitor()