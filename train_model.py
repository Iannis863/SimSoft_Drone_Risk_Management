import numpy as np
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from drone_model import build_drone_predictor

def train():
    X = np.load('X_train.npy')
    Y = np.load('Y_train.npy')
    W = np.load('W_train.npy')

    W = np.expand_dims(W, axis=-1)

    model = build_drone_predictor()

    early_stop = EarlyStopping(monitor='val_loss', patience=10, min_delta=0.005, restore_best_weights=True)
    reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5, min_lr=1e-5)

    print("🧠 Starting Weighted High-Stakes AI Training...")
    model.fit(
        X, Y,
        sample_weight=W,
        epochs=150,
        batch_size=64,
        validation_split=0.2,
        callbacks=[early_stop, reduce_lr],
        verbose=1
    )

    model.save('drone_model.h5')
    print("🏆 Training Complete! Model saved as drone_model.h5")

if __name__ == "__main__":
    train()