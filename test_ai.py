import os

# Suppress the TF logs for a clean output
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
from ai_predictor import AIDronePredictor

# Load the brain
predictor = AIDronePredictor('drone_model.h5')

# Simulate a drone flying North-East (increasing Lat and Lng)
fake_history = []
for i in range(10):
    fake_history.append({
        'lat': 46.77 + (i * 0.0001),
        'lng': 23.60 + (i * 0.0001),
        'alt': 100
    })

prediction = predictor.predict_path(fake_history)

print("\n--- 🧠 AI TRAJECTORY VERIFICATION ---")
if prediction is not None:
    print(f"Current Position: {fake_history[-1]['lat']}, {fake_history[-1]['lng']}")
    print(f"Predicted end point (in 10 steps): {prediction[-1][0]:.5f}, {prediction[-1][1]:.5f}")

    # Check if the predicted points are actually moving in the right direction
    if prediction[-1][0] > fake_history[-1]['lat']:
        print("✅ Directional Logic: Valid (Drone is projected forward)")
else:
    print("❌ Prediction failed.")