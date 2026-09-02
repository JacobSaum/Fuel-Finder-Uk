import requests
import sqlite3
from math import radians, asin, cos, sin, sqrt

conn = sqlite3.connect("pfs_data.db", check_same_thread=False)
cur = conn.cursor()

MILES_PER_METRE = 1 / 1609.344
OSRM_TABLE_URL = "https://router.project-osrm.org/table/v1/driving/"
OSRM_BATCH_SIZE = 200
# straight-line distance is always <= road distance, so this fudge factor widens the
# straight-line pre-filter enough to not miss stations that are close as the crow flies
# but further by road (bends, rivers, one-ways etc.)
STRAIGHT_LINE_BUFFER = 1.6
ROUTING_CANDIDATE_CAP = 200

# returns lat and lon from postcode if valid postcode
def getLocationFromPostcode(postcode):
    response = requests.get(f"https://api.postcodes.io/postcodes/{postcode}",)
    if response.status_code== 200:
        pfs_data = response.json()
        lat, lon = getLongAndLat(pfs_data)
        return lat, lon
    
    return None, None

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

# real road distance (miles) from one origin to many destinations, via OSRM's table service.
# candidates is a list of (pfs_id, lat, lon); returns {pfs_id: miles}. Requests are batched
# since routing services cap how many destinations one request can carry.
def getRoadDistances(searchLatitude, searchLongitude, candidates):
    distances = {}
    for i in range(0, len(candidates), OSRM_BATCH_SIZE):
        batch = candidates[i:i + OSRM_BATCH_SIZE]
        coords = f"{searchLongitude},{searchLatitude};" + ";".join(f"{lon},{lat}" for _, lat, lon in batch)

        response = requests.get(
            f"{OSRM_TABLE_URL}{coords}",
            params={"sources": 0, "annotations": "distance"},
            timeout=8,
        )
        response.raise_for_status()
        data = response.json()
        if data.get("code") != "Ok":
            raise ValueError(f"Routing service error: {data.get('code')}")

        metres = data["distances"][0][1:]
        for (pfs_id, _, _), dist_m in zip(batch, metres):
            if dist_m is not None:
                distances[pfs_id] = dist_m * MILES_PER_METRE

    return distances

# loop through stations and check if they are within the search radius, using real road
# distance. Falls back to straight-line distance if the routing service is unavailable.
def getNearbyStations(searchDistance, searchLatitude, searchLongitude, data_pfs):
    straightLineCandidates = []
    for pfs_id, lat, lon in data_pfs:
        lat, lon = float(lat), float(lon)
        dist = getDistBetweenTwoLocations(searchLatitude, searchLongitude, lat, lon)
        if dist <= searchDistance * STRAIGHT_LINE_BUFFER + 3:
            straightLineCandidates.append((dist, pfs_id, lat, lon))

    straightLineCandidates.sort(key=lambda c: c[0])
    nearestCandidates = straightLineCandidates[:ROUTING_CANDIDATE_CAP]

    if not nearestCandidates:
        return {}

    try:
        roadDistances = getRoadDistances(
            searchLatitude, searchLongitude,
            [(pfs_id, lat, lon) for _, pfs_id, lat, lon in nearestCandidates],
        )
    except (requests.RequestException, ValueError, KeyError, IndexError):
        roadDistances = {pfs_id: dist for dist, pfs_id, _, _ in nearestCandidates}

    return {pfs_id: dist for pfs_id, dist in roadDistances.items() if dist <= searchDistance}

def geocodingLogic(postcode, searchRadius):
    searchLatitude, searchLongitude = getLocationFromPostcode(postcode)
    if searchLatitude is None or searchLongitude is None:
        raise LookupError(f"Could not find location for postcode {postcode}.")
    stationData = getStationData()
    return getNearbyStations(searchRadius, searchLatitude, searchLongitude, stationData)

# same as geocodingLogic but using coordinates directly (eg. browser geolocation)
def geocodingLogicFromCoords(searchLatitude, searchLongitude, searchRadius):
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
