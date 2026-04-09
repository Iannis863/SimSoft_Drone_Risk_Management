from tensorflow.keras import layers, models


def build_drone_predictor():
    model = models.Sequential([
        layers.Input(shape=(10, 8)),
        layers.LSTM(128, return_sequences=False),
        layers.RepeatVector(10),
        layers.LSTM(128, return_sequences=True),
        layers.LSTM(64, return_sequences=True),
        layers.TimeDistributed(layers.Dense(64, activation='relu')),
        layers.TimeDistributed(layers.Dense(3))
    ])
    model.compile(optimizer='adam', loss='huber')
    return model


if __name__ == "__main__":
    model = build_drone_predictor()
    model.summary()