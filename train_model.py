import numpy as np
from drone_model import build_drone_predictor

def train():
    # 1. Load the synthetic data
    X = np.load('X_train.npy')
    Y = np.load('Y_train.npy')

    # 2. Build the model
    model = build_drone_predictor()

    # 3. Train
    print("🧠 Starting AI Training...")
    model.fit(
        X, Y,
        epochs=50,
        batch_size=32,
        validation_split=0.2,
        verbose=1
    )

    # 4. Save the "Brain"
    model.save('drone_model.h5')
    print("🏆 Training Complete! Model saved as drone_model.h5")


if __name__ == "__main__":
    train()