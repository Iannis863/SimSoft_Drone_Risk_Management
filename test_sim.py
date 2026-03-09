import time
from risk_calculator import assess_risk, get_heading
from radar import log_incident


# Mocking the Drone Data Structure from your previous JSON
def simulate_drone_flight():
    print("--- STARTING RADAR SIMULATION TEST ---")

    # Simulate a drone moving from 1.5km to 800m
    mock_history = []
    start_lat, start_lng = 44.5800, 26.0900  # Starting outside perimeter

    for i in range(15):
        # Slowly move closer to the Airport (44.5722, 26.0841)
        current_lat = start_lat - (i * 0.001)
        current_lng = start_lng - (i * 0.0005)

        mock_history.append({'lat': current_lat, 'lng': current_lng})

        # Create the mock drone object
        mock_drone = {
            'id': 99999,
            'history': mock_history,
            'droneData': {
                'location': {'lat': current_lat, 'lng': current_lng},
                'altitudes': {'agl': 150},  # Violating 120m limit
                'groundSpeed': 10
            },
            'pilotData': {'id': None}  # Unauthorized / Rogue
        }

        # Run your logic
        status, dist, trend, reason = assess_risk(mock_drone)
        heading = get_heading(mock_history)

        # Log to your CSV
        if status != "🟢 CLEAR":
            log_incident(mock_drone['id'], status, dist, trend, reason)

        print(f"Step {i + 1}: Dist {int(dist)}m | Status: {status} | Trend: {trend} | Heading: {int(heading)}°")
        time.sleep(0.5)

    print("\n✅ Simulation Complete. Check 'drone_incidents.csv' for the logs.")


if __name__ == "__main__":
    simulate_drone_flight()