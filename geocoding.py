import requests
import sqlite3
from math import radians, asin, cos, sin, sqrt

conn = sqlite3.connect("pfs_data.db")
cur = conn.cursor()

# returns lat and lon from postcode if valid postcode
def getLocationFromPostcode(postcode):
    response = requests.get(f"https://api.postcodes.io/postcodes/{postcode}",)
    if response.status_code== 200:
        pfs_data = response.json()
        lat, lon = getLongAndLat(pfs_data)
        return lat, lon
    
    return None, None, None

# gets lon and lat from postcode
def getLongAndLat(pfs_data):
    result = pfs_data["result"]
    longitude = result["longitude"]
    latitude = result["latitude"]
    return latitude, longitude

#Gets distance between 2 lon and lats
def getDistBetweenTwoLocations(lat1, lon1, lat2, lon2):
    R = 3958.8
    
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    lat1 = radians(lat1)
    lat2 = radians(lat2)
    
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * asin(sqrt(a))

    return R * c

# get simplified list of stations data
def getStationData():
    cur.execute("SELECT pfs_id, latitude, longitude FROM pfs_data WHERE perm_closure == 0 AND temp_closure == 0")
    row = cur.fetchall()
    return row

# loop through stations and check if they are within the search radius
def getNearbyStations(searchDistance, searchLatitude, searchLongitude, data_pfs):
    validStations = {}
    for x in range (0, len(data_pfs)):
        dist = getDistBetweenTwoLocations(searchLatitude, searchLongitude, float(data_pfs[x][1]), float(data_pfs[x][2]))
        if dist <= searchDistance:
            validStations[data_pfs[x][0]] = dist

    return validStations

def geocodingLogic(postcode, searchRadius):
    searchLatitude, searchLongitude = getLocationFromPostcode(postcode)
    stationData = getStationData()
    return getNearbyStations(searchRadius, searchLatitude, searchLongitude, stationData)

# used for testing geocoding logic
def geocodingTest():
    validStations = geocodingLogic("AB12 4RL", 15)

    if not validStations:
        print("No stations found")
        return

    placeholders = ",".join("?" for _ in validStations)
    cur.execute(f"SELECT * FROM pfs_data WHERE pfs_id IN ({placeholders})", validStations)
    row = cur.fetchall()
    print(row)
