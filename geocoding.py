import requests
import sqlite3
from math import radians, asin, cos, sin, sqrt

conn = sqlite3.connect("pfs_data.db")
cur = conn.cursor()

def getLocationFromPostcode(postcode):
    response = requests.get(f"https://api.postcodes.io/postcodes/{postcode}",)
    if response.status_code== 200:
        pfs_data = response.json()
        return getLongAndLat(pfs_data), pfs_data

def getLongAndLat(pfs_data):
    longitude = pfs_data["longitude"]
    latitude = pfs_data["latitude"]
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
    cur.execute("SELECT pfs_id, latitude, longitude FROM pfs_data WHERE perm_closure == 1 AND temp_closure == 1")
    row = cur.fetchall()
    return row

# loop through stations and check if they are within the search radius
def getNearbyStations(searchDistance, searchLongitude, searchLatitude, data_pfs):
    validStations = []
    for x in range (0, len(data_pfs)):
        dist = getDistBetweenTwoLocations(searchLatitude, searchLongitude, float(data_pfs[x][1]), float(data_pfs[x][2]))
        if dist <= searchDistance:
            validStations.append(data_pfs[x][0])

    return validStations

def geocodingLogic(postcode, searchRadius):
    searchLatitude, searchLongitude, pfs_data = getLocationFromPostcode(postcode)
    getStationData()
    return getNearbyStations(searchRadius, searchLatitude, searchLongitude, pfs_data)


def geocodingTest():
    validStations = geocodingLogic("AB12 4RL", 15)

    cur.execute(f"SELECT * FROM pfs_data WHERE pfs_id == {validStations}")
    row = cur.fetchall()
    print(row)
