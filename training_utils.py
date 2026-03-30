import numpy as np

def normalize_sequence(history):
    """
    Converts a list of history points into a normalized
    numpy array for the AI model.
    """
    if len(history) < 10: return None, None

    # Take the last 10 points
    coords = np.array([[p['lat'], p['lng'], p.get('alt', 0)] for p in history[-10:]])

    # Zero-center the data (Relative coordinates)
    origin = coords[-1]
    relative_coords = coords - origin

    # Scaling (Meters-ish approximation for better gradients)
    relative_coords[:, 0] *= 111139
    relative_coords[:, 1] *= 77000

    return relative_coords, origin