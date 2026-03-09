import math
from config import AIRPORT_COORDS

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


def assess_risk(drone):
    pos = drone.get('droneData', {}).get('location', {})
    alt = drone.get('droneData', {}).get('altitudes', {}).get('agl', 0)
    pilot = drone.get('pilotData', {}).get('id')
    dist = get_distance(pos['lat'], pos['lng'])

    # Classification Logic
    if dist < 1000 and not pilot:
        return "🔴 CRITICAL", dist
    elif dist < 2000 or alt > 120:
        return "🟡 WARNING", dist
    return "🟢 CLEAR", dist