import matplotlib.pyplot as plt
from ai_predictor import AIDronePredictor

predictor = AIDronePredictor('drone_model.h5')

# Create a test history (e.g., a curve)
history = []
for i in range(10):
    history.append({'lat': 46.77 + (i * 0.0001), 'lng': 23.60 + (i**1.2 * 0.00005), 'alt': 100})

pred = predictor.predict_path(history)

# Plotting
plt.figure(figsize=(10, 6))
plt.plot([p['lng'] for p in history], [p['lat'] for p in history], 'go-', label='Input History')
plt.plot(pred[:, 1], pred[:, 0], 'rx--', label='AI Prediction')
plt.title("Drone Trajectory: Input vs AI Projection")
plt.legend()
plt.show()