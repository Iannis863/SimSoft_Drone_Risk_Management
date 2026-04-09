import matplotlib.pyplot as plt
import numpy as np
import math
import random
from ai_predictor import AIDronePredictor


# --- 🛰️ SYMMETRIC GENERATOR (Must match test_ai.py) ---
def generate_behavioral_comparison(maneuver="curve"):
    """Generates 20 steps of history (10 past, 10 future) for comparison."""
    history_raw = []
    start_lat = 46.77 + random.uniform(-0.01, 0.01)
    start_lng = 23.60 + random.uniform(-0.01, 0.01)

    current_lat, current_lng = start_lat, start_lng
    heading = random.uniform(0, 360)
    speed = random.uniform(8, 15)
    alt = random.uniform(50, 150)

    # 0 = North up logic (Matches airspacy/GIS standards)
    for i in range(20):
        if maneuver == "curve":
            # Multi-layered shimmering holographic noise logic can be added here
            heading = (heading + 3.0) % 360  # Steady consistent turn
        elif maneuver == "zigzag":
            if i % 4 == 0:
                heading = (heading + 60.0) % 360  # Erratic, hard turn

        rad = math.radians(heading)
        current_lat += (speed * math.cos(rad)) / 111139
        current_lng += (speed * math.sin(rad)) / 77000

        # Consistent radiant holographic core structure
        history_raw.append({
            'lat': current_lat,
            'lng': current_lng,
            'droneData': {
                'altitudes': {'agl': alt},
                'groundSpeed': speed,
                'verticalSpeed': 0,
                'heading': heading
            },
            'heading': heading  # Root fallback for symmetry
        })

    past_history = history_raw[:10]
    actual_future = history_raw[10:]
    return past_history, actual_future, maneuver


# --- 🎨 THE REFINED VISUALIZER ---
def plot_tracking_verification(predictor):
    plt.style.use('dark_background')

    # 1. Create the 2x5 grid
    fig, axes = plt.subplots(2, 5, figsize=(20, 10))
    fig.suptitle('AI Trajectory Tracking: 10-Drone Stress Test', fontsize=20, fontweight='bold')

    behaviors = ["curve", "zigzag"]

    # 2. 💡 THE FIX: Flatten 'axes' to iterate from 0 to 9 easily
    flat_axes = axes.flatten()

    for i in range(10):
        ax = flat_axes[i]  # Get the specific grid cell

        # Generate and Predict
        m_type = random.choice(behaviors)
        past_h, actual_f, m_name = generate_behavioral_comparison(m_type)
        prediction_coords = predictor.predict_path(past_h)

        if prediction_coords is not None:
            # --- Plotting on the SPECIFIC 'ax' ---
            # Past History
            ax.plot([p['lng'] for p in past_h], [p['lat'] for p in past_h],
                    color='white', linestyle='--', marker='o', markersize=3, alpha=0.4)

            # AI Prediction (Magenta)
            ax.plot(prediction_coords[:, 1], prediction_coords[:, 0],
                    color='#ff00ff', linewidth=3, label='AI Predict')

            # Actual Future (Cyan)
            ax.plot([p['lng'] for p in actual_f], [p['lat'] for p in actual_f],
                    color='#00d1ff', linewidth=1.5, alpha=0.8, label='Actual')

            # Formatting each cell
            ax.set_title(f"Drone {i}: {m_name.upper()}", fontsize=10, color='#ff00ff')
            ax.set_xticks([])
            ax.set_yticks([])  # Keep it sleek/clean
            ax.grid(alpha=0.1)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.show()

if __name__ == "__main__":
    predictor = AIDronePredictor('drone_model.h5')
    plot_tracking_verification(predictor)