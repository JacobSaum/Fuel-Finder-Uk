import requests
from math import radians, asin, cos, sin, sqrt

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

def getDistBetweenTwoLocations(lat1, lon1, lat2, lon2):
    R = 3958.8
    
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    lat1 = radians(lat1)
    lat2 = radians(lat2)
    
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * asin(sqrt(a))
    
    return R * c

def getNearbyStations():
