import numpy as np
import os


def generate_flight_path(points=20, maneuver_type="straight"):
    path = np.zeros((points, 6))

    current_lat, current_lng = 46.77, 23.60
    current_alt = np.random.uniform(20, 100)
    heading = np.random.uniform(0, 360)
    g_speed = np.random.uniform(5, 15)
    v_speed = np.random.uniform(-0.2, 0.2)

    path[0] = [current_lat, current_lng, current_alt, heading, g_speed, v_speed]

    zigzag_turn = np.random.choice([60, -60, 90, -90, 120, -120])
    zigzag_interval = np.random.randint(3, 6)

    for i in range(1, points):
        if maneuver_type == "curve":
            heading = (heading + np.random.uniform(2, 5)) % 360
        elif maneuver_type == "zigzag":
            if i % zigzag_interval == 0:
                heading = (heading + zigzag_turn) % 360
                zigzag_turn *= -1
        else:
            heading += np.random.normal(0, 0.5)

        rad = np.radians(heading)
        current_lat += (g_speed * np.cos(rad)) / 111139
        current_lng += (g_speed * np.sin(rad)) / 77000
        current_alt += v_speed

        g_speed = max(2, g_speed + np.random.normal(0, 0.1))
        v_speed += np.random.normal(0, 0.05)

        path[i] = [current_lat, current_lng, current_alt, heading % 360, g_speed, v_speed]

    return path


def create_dataset(samples=10000):
    X, Y, W = [], [], []
    types = ["straight"] * 70 + ["curve"] * 20 + ["zigzag"] * 10

    print(f"🛰️ Generating {samples} Rotated 8-feature paths...")
    for _ in range(samples):
        m_type = np.random.choice(types)
        full_path = generate_flight_path(points=20, maneuver_type=m_type)

        origin = full_path[9, :3].copy()
        origin_heading = full_path[9, 3]

        norm_path = full_path.copy()
        norm_path[:, :3] -= origin
        norm_path[:, 0] *= 111139
        norm_path[:, 1] *= 77000

        theta = np.radians(origin_heading)
        c, s = np.cos(theta), np.sin(theta)

        for j in range(20):
            lat, lng = norm_path[j, 0], norm_path[j, 1]
            norm_path[j, 1] = lng * c - lat * s
            norm_path[j, 0] = lng * s + lat * c

        x_seq = []
        prev_hdg = full_path[0, 3]

        for i in range(10):
            lat = norm_path[i, 0]
            lng = norm_path[i, 1]
            alt = norm_path[i, 2]

            hdg = full_path[i, 3]

            rel_hdg = (hdg - origin_heading) % 360
            hdg_rad = np.radians(rel_hdg)
            hdg_sin = np.sin(hdg_rad)
            hdg_cos = np.cos(hdg_rad)

            if i == 0:
                turn_rate = 0.0
            else:
                diff = hdg - prev_hdg
                diff = (diff + 180) % 360 - 180
                turn_rate = diff / 180.0

            prev_hdg = hdg

            gs = full_path[i, 4] / 30.0
            vs = full_path[i, 5] / 10.0

            x_seq.append([lat, lng, alt, hdg_sin, hdg_cos, turn_rate, gs, vs])

        X.append(x_seq)
        Y.append(norm_path[10:, :3])
        W.append(5.0 if m_type == "zigzag" else 1.0)

    return np.array(X, dtype=np.float32), np.array(Y, dtype=np.float32), np.array(W, dtype=np.float32)


if __name__ == "__main__":
    X_train, Y_train, W_train = create_dataset(25000)
    np.save('X_train.npy', X_train)
    np.save('Y_train.npy', Y_train)
    np.save('W_train.npy', W_train)
    print("✅ Rotated Training data and weights saved.")