import numpy as np


def generate_flight_path(points=20, maneuver_type="straight"):
    """Generates a single 3D flight trajectory."""
    path = np.zeros((points, 3))

    # Random starting velocity and direction
    vx = np.random.uniform(-5, 5)
    vy = np.random.uniform(-5, 5)
    vz = np.random.uniform(-0.5, 0.5)

    for i in range(1, points):
        if maneuver_type == "straight":
            # Constant velocity + slight noise
            noise = np.random.normal(0, 0.1, 3)
            path[i] = path[i - 1] + [vx, vy, vz] + noise

        elif maneuver_type == "curve":
            # Change direction slightly every step (banking turn)
            angle = 0.1 * i
            path[i, 0] = path[i - 1, 0] + vx * np.cos(angle)
            path[i, 1] = path[i - 1, 1] + vy * np.sin(angle)
            path[i, 2] = path[i - 1, 2] + vz

        elif maneuver_type == "zigzag":
            # Sudden velocity shifts
            if i % 5 == 0:
                vx, vy = -vy, vx  # 90-degree snap turn
            path[i] = path[i - 1] + [vx, vy, vz] + np.random.normal(0, 0.2, 3)

    return path


def create_dataset(samples=5000):
    X, Y = [], []
    types = ["straight"] * 70 + ["curve"] * 20 + ["zigzag"] * 10

    print(f"🛰️ Generating {samples} synthetic flight paths...")

    for _ in range(samples):
        m_type = np.random.choice(types)
        full_path = generate_flight_path(points=20, maneuver_type=m_type)

        origin = full_path[9]
        normalized_path = full_path - origin

        # X is the first 10 points (Input)
        # Y is the next 10 points (What we want to predict)
        X.append(normalized_path[:10])
        Y.append(normalized_path[10:])

    return np.array(X), np.array(Y)


if __name__ == "__main__":
    X_train, Y_train = create_dataset(10000)
    np.save('X_train.npy', X_train)
    np.save('Y_train.npy', Y_train)
    print("✅ Training data saved to X_train.npy and Y_train.npy")