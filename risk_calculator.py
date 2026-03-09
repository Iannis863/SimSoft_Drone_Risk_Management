import math
from config import AIRPORT_COORDS, MAX_SAFE_ALTITUDE


def get_distance(lat1, lon1):
    lat2, lon2 = AIRPORT_COORDS
    R = 6371000  # Meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def get_heading(history):
    if len(history) < 2: return 0
    p1, p2 = history[-2], history[-1]
    lat1, lon1 = math.radians(p1['lat']), math.radians(p1['lng'])
    lat2, lon2 = math.radians(p2['lat']), math.radians(p2['lng'])
    y = math.sin(lon2 - lon1) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(lon2 - lon1)
    return (math.degrees(math.atan2(y, x)) + 360) % 360


def get_proximity_trend(history, current_alt):
    if current_alt <= 0:
        return "🛑 STATIONARY"

    if len(history) < 10:  # Need enough data points for a stable trend
        return "STABLE"

    # Compare current distance vs distance 10 points ago
    current_pos = history[-1]
    past_pos = history[-10]

    current_dist = get_distance(current_pos['lat'], current_pos['lng'])
    past_dist = get_distance(past_pos['lat'], past_pos['lng'])

    diff = current_dist - past_dist

    if diff < -5: return "🔻 CLOSING"  # Distance is decreasing
    if diff > 5:  return "🔹 RECEDING"  # Distance is increasing
    return "↔️ HOVERING"


def assess_risk(drone):
    pos = drone.get('droneData', {}).get('location', {})

    # SAFETY FIX: Use .get() with a default of 0 if altitudes or agl is missing/None
    altitudes = drone.get('droneData', {}).get('altitudes') or {}
    alt = altitudes.get('agl')
    if alt is None:
        alt = 0  # Default to 0 if the sensor is silent
    alt = max(alt, 0)

    pilot = drone.get('pilotData', {}).get('id')
    dist = get_distance(pos['lat'], pos['lng'])

    # Tactical Trend
    trend = get_proximity_trend(drone.get('history', []), alt)

    # Classification Logic
    reason = "None"
    if dist < 1000 and not pilot:
        status, reason = "🔴 CRITICAL", "Unauthorized in Perimeter"
    elif dist < 2000 or alt > MAX_SAFE_ALTITUDE:
        status = "🟡 WARNING"
        if alt > MAX_SAFE_ALTITUDE:
            reason = f"Altitude Violation ({int(alt)}m > {MAX_SAFE_ALTITUDE}m)"
        else:
            reason = "Perimeter Proximity Violation"
    else:
        status, reason = "🟢 CLEAR", "Normal Ops"

    return status, dist, trend, reason, alt