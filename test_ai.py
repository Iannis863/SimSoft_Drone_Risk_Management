import os
import math
import random
import numpy as np

# Suppress the TF logs
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
from ai_predictor import AIDronePredictor

# Load the brain
predictor = AIDronePredictor('drone_model.h5')


def generate_behavioral_history(drone_id, maneuver="straight"):
    """
    Generates 10 steps of history based on specific flight physics.
    """
    history = []
    # Starting base point near Cluj-Napoca
    start_lat = 46.77 + random.uniform(-0.01, 0.01)
    start_lng = 23.60 + random.uniform(-0.01, 0.01)

    current_lat, current_lng = start_lat, start_lng
    heading = random.uniform(0, 360)
    speed = random.uniform(8, 15)  # Meters per second
    alt = random.uniform(50, 150)

    for i in range(10):
        # Apply Maneuver Logic
        if maneuver == "curve":
            heading = (heading + 5.0) % 360  # Steady 5-degree turn per step
        elif maneuver == "zigzag":
            if i % 3 == 0:
                heading = (heading + 45.0) % 360  # Sharp snap every 3 steps

        # Calculate next step (Compass Math)
        rad = math.radians(heading)
        # 0.00001 is roughly 1.1 meters
        current_lat += (speed * math.cos(rad)) / 111139
        current_lng += (speed * math.sin(rad)) / 77000

        history.append({
            'lat': current_lat,
            'lng': current_lng,
            'droneData': {
                'altitudes': {'agl': alt},
                'groundSpeed': speed,
                'verticalSpeed': random.uniform(-0.1, 0.1),
                'heading': heading
            },
            'heading': heading  # Root fallback
        })
    return history, maneuver


# --- 🛰️ MAIN TEST LOOP (50 DRONES) ---
behaviors = ["straight", "curve", "zigzag"]
results = {"straight": [], "curve": [], "zigzag": []}

print(f"{'Drone ID':<15} | {'Behavior':<10} | {'Prediction':<10} | {'Status'}")
print("-" * 55)

for i in range(50):
    m_type = random.choice(behaviors)
    history, m_name = generate_behavioral_history(f"DRONE-{i:02d}", m_type)

    prediction = predictor.predict_path(history)

    drone_id = f"DRONE-{i:02d}"
    if prediction is not None:
        # Simple Logic: Did the AI actually move the drone at least 5 meters?
        # (Difference between last history point and last predicted point)
        dist_moved = math.sqrt(
            (prediction[-1][0] - history[-1]['lat']) ** 2 +
            (prediction[-1][1] - history[-1]['lng']) ** 2
        ) * 111139

        status = "✅ STABLE" if dist_moved > 5 else "⚠️ STATIC/STUCK"
        results[m_name].append(dist_moved)
        print(f"{drone_id:<15} | {m_name:<10} | {dist_moved:>6.1f}m | {status}")
    else:
        print(f"{drone_id:<15} | {m_name:<10} | {'FAILED':<10} | ❌ ERROR")

# --- 📊 FINAL ANALYSIS ---
print("\n" + "=" * 30)
print("🧠 MODEL PERFORMANCE SUMMARY")
print("=" * 30)
for b, dists in results.items():
    avg = sum(dists) / len(dists) if dists else 0
    print(f"{b.upper():<10} : Avg Prediction reach {avg:.1f} meters")