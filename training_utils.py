import numpy as np


def normalize_sequence(history):
    if len(history) < 10: return None, None, None

    last_p = history[-1]
    last_d = last_p.get('droneData', {})

    origin = np.array([last_p['lat'], last_p['lng'], last_d.get('altitudes', {}).get('agl', 0)])
    origin_heading = last_p.get('heading') if last_p.get('heading') is not None else last_d.get('heading', 0)

    seq = []
    prev_hdg = None

    theta = np.radians(origin_heading)
    c, s = np.cos(theta), np.sin(theta)

    for i, p in enumerate(history[-10:]):
        d = p.get('droneData', {})

        lat_rel = (p['lat'] - origin[0]) * 111139
        lng_rel = (p['lng'] - origin[1]) * 77000

        local_lng = lng_rel * c - lat_rel * s
        local_lat = lng_rel * s + lat_rel * c

        alt_abs = d.get('altitudes', {}).get('agl', 0)
        alt_rel = alt_abs - origin[2]

        hdg = p.get('heading') if p.get('heading') is not None else d.get('heading', 0)

        rel_hdg = (hdg - origin_heading) % 360
        hdg_rad = np.radians(rel_hdg)
        hdg_sin = np.sin(hdg_rad)
        hdg_cos = np.cos(hdg_rad)

        if prev_hdg is None:
            turn_rate = 0.0
        else:
            diff = hdg - prev_hdg
            diff = (diff + 180) % 360 - 180
            turn_rate = diff / 180.0

        prev_hdg = hdg

        gs = d.get('groundSpeed', 0) / 30.0
        vs = d.get('verticalSpeed', 0) / 10.0

        seq.append([local_lat, local_lng, alt_rel, hdg_sin, hdg_cos, turn_rate, gs, vs])

    return np.array(seq, dtype=np.float32), origin, origin_heading