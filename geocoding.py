import requests
from math import radians, degrees, cos

def getLocationFromPostcode(post):
    response = requests.get(f"https://api.postcodes.io/postcodes/{post}",)
    if response.status_code== 200:
        pfs_data = response.json()
        return pfs_data
    else:
        return

def getLongAndLat(pfs_data):
    longitude = pfs_data["longitude"]
    latitude = pfs_data["latitude"]
    return longitude, latitude

def getMaxBounds(lat, lon, radius_miles):
    EARTH_RADIUS_MILES = 3958.8
    
    angular_radius = radius_miles / EARTH_RADIUS_MILES
    
    delta_lat = degrees(angular_radius)
    
    lat_rad = radians(lat)
    delta_lon = degrees(angular_radius / max(cos(lat_rad), 1e-7))
    
    min_lat = lat - delta_lat
    max_lat = lat + delta_lat
    min_lon = lon - delta_lon
    max_lon = lon + delta_lon
    
    return {
        "min_latitude": round(min_lat, 6),
        "max_latitude": round(max_lat, 6),
        "min_longitude": round(min_lon, 6),
        "max_longitude": round(max_lon, 6)
    }


def getNearbyStations():
