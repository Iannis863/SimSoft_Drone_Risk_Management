from tensorflow.keras import layers, models


def build_drone_predictor():
    """
    Creates an LSTM model designed to learn 3D flight trajectories.
    Input: (10 timesteps, 3 features: Lat, Lng, Alt)
    Output: (10 timesteps, 3 features: Predicted Lat, Lng, Alt)
    """
    model = models.Sequential([
        # Layer 1: LSTM to capture temporal movement patterns
        layers.Input(shape=(10, 3)),
        layers.LSTM(64, return_sequences=True),
        layers.Dropout(0.2),  # Prevents overfitting to specific flight paths

        # Layer 2: Deeper LSTM for complex maneuvering
        layers.LSTM(32, return_sequences=True),

        # Layer 3: Dense output to predict coordinates
        # TimeDistributed applies the prediction to each of the 10 future steps
        layers.TimeDistributed(layers.Dense(3)),
    ])

    model.compile(
        optimizer='adam',
        loss='mse',  # Mean Squared Error is best for coordinate regression
        metrics=['mae']
    )

    return model


if __name__ == "__main__":
    model = build_drone_predictor()
    model.summary()