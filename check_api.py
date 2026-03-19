import requests
import json
from config import SENSOR_URL, TOKEN_IANNIS


def get_all_keys(data, prefix=''):
    """
    Recursively finds every unique key path in a JSON object.
    Example: 'droneData.location.lat'
    """
    keys = set()
    if isinstance(data, dict):
        for k, v in data.items():
            full_key = f"{prefix}.{k}" if prefix else k
            keys.add(full_key)
            keys.update(get_all_keys(v, full_key))
    elif isinstance(data, list) and len(data) > 0:
        # Check the first item in a list to see its structure
        keys.update(get_all_keys(data[0], prefix))
    return keys


def check_drone_count():
    print("--- 📡 API DIAGNOSTIC TOOL ---")

    headers = {
        "Authorization": f"Bearer {TOKEN_IANNIS}",
        "Accept": "application/json"
    }

    try:
        # Using the fused-data endpoint
        url = f"{SENSOR_URL}/api/fused-data/map/50000/0"
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()

            if isinstance(data, list):
                print(f"✅ Success! Drones detected: {len(data)}")

                if len(data) > 0:
                    print("\n--- 🔍 DISCOVERED DATA SCHEMA ---")
                    # Get all unique nested keys from the first drone
                    all_keys = sorted(list(get_all_keys(data[0])))
                    for key in all_keys:
                        print(f"🔑 {key}")

                    print("\n--- 🛸 SAMPLE DRONE (FIRST IN LIST) ---")
                    print(json.dumps(data[0], indent=4))
                else:
                    print("📊 Connection successful, but the sky is currently empty (0 drones).")
            else:
                print("⚠️ API returned a non-list object.")
        else:
            print(f"❌ API Error: {response.status_code}")

    except Exception as e:
        print(f"💥 Connection Failed: {e}")


if __name__ == "__main__":
    check_drone_count()