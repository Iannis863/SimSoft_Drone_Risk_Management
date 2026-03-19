import math

def project_future_position(lat, lng, heading, speed_mps, seconds_ahead=20):
    """
    Predicts future Lat/Lng based on current position, heading, and speed.
    Uses Dead Reckoning math.
    """
    R = 6371000  # Earth's radius in meters
    distance = speed_mps * seconds_ahead

    # Convert to radians
    lat_rad = math.radians(lat)
    lng_rad = math.radians(lng)
    bearing_rad = math.radians(heading)

    # Calculate future latitude
    future_lat = math.asin(
        math.sin(lat_rad) * math.cos(distance / R) +
        math.cos(lat_rad) * math.sin(distance / R) * math.cos(bearing_rad)
    )

    # Calculate future longitude
    future_lng = lng_rad + math.atan2(
        math.sin(bearing_rad) * math.sin(distance / R) * math.cos(lat_rad),
        math.cos(distance / R) - math.sin(lat_rad) * math.sin(future_lat)
    )

    return math.degrees(future_lat), math.degrees(future_lng)