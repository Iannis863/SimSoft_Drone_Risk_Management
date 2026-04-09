import numpy as np
from training_utils import normalize_sequence
import tensorflow as tf


class AIDronePredictor:
    def __init__(self, model_path='drone_model.h5'):
        self.model = tf.keras.models.load_model(model_path, compile=False)

    def predict_path(self, history):
        res = normalize_sequence(history)
        if res[0] is None: return None

        seq, origin, origin_heading = res

        prediction = self.model.predict(seq[np.newaxis, ...], verbose=0)[0]

        theta = np.radians(-origin_heading)
        c, s = np.cos(theta), np.sin(theta)

        for j in range(len(prediction)):
            local_lat, local_lng = prediction[j, 0], prediction[j, 1]

            global_lng = local_lng * c - local_lat * s
            global_lat = local_lng * s + local_lat * c

            prediction[j, 0] = global_lat
            prediction[j, 1] = global_lng

        prediction[:, 0] /= 111139
        prediction[:, 1] /= 77000

        real_coords = prediction + origin

        return real_coords