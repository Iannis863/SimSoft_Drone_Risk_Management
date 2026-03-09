from shapely.geometry import shape, Point
from shapely.ops import nearest_points
import json
import math

class AirspaceManager:
    def __init__(self, file_path='zone_restriction_uav.json'):
        self.file_path = file_path
        self.restricted_features = []
        self.load_zones()

    def load_zones(self):
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.restricted_features = [
                {
                    "polygon": shape(feat["geometry"]),
                    "name": feat.get("properties", {}).get("name", "Unknown Zone")
                }
                for feat in data.get("features", [])
            ]
            print(f"✅ Loaded {len(self.restricted_features)} polygons.")
        except Exception as e:
            print(f"❌ Error: {e}")

    def get_distance_to_closest_zone(self, lat, lng):
        """Calculates distance in meters to the boundary of the nearest restricted zone."""
        drone_point = Point(lng, lat)
        min_dist_deg = float('inf')
        closest_zone_name = "None"

        for zone in self.restricted_features:
            if zone["polygon"].contains(drone_point):
                return 0, zone["name"]

            d = drone_point.distance(zone["polygon"])
            if d < min_dist_deg:
                min_dist_deg = d
                closest_zone_name = zone["name"]

        dist_meters = min_dist_deg * 111139
        return int(dist_meters), closest_zone_name