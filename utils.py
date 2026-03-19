import re

def parse_altitude(alt_str):
    """Converts altitude strings (GND, 120M AGL, 2500FT) to float meters."""
    if not alt_str:
        return 0.0
    s = str(alt_str).upper().strip()
    if s == "GND" or s.startswith("0"):
        return 0.0
    match = re.search(r"(\d+)", s)
    if not match:
        return 0.0
    value = float(match.group(1))
    if "FT" in s:
        return value * 0.3048
    return value

def get_status_color(status):
    s = str(status).upper()
    if "CRITICAL" in s:
        return [255, 0, 0, 220]      # Red
    if "PREDICTIVE" in s:
        return [255, 0, 255, 220]    # Magenta/Purple
    if "WARNING" in s:
        return [214, 158, 46, 220]   # Orange
    return [31, 157, 85, 220]        # Green