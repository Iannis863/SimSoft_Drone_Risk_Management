import numpy as np
from training_utils import normalize_sequence
import tensorflow as tf


class AIDronePredictor:
    def __init__(self, model_path='drone_model.h5'):
        self.model = tf.keras.models.load_model(model_path, compile=False)

    def predict_path(self, history):
        seq, origin = normalize_sequence(history)
        if seq is None: return None

        # Add batch dimension and predict
        prediction = self.model.predict(seq[np.newaxis, ...], verbose=0)[0]

        # Denormalize back to Lat/Lng
        prediction[:, 0] /= 111139
        prediction[:, 1] /= 77000
        real_coords = prediction + origin

        return real_coords