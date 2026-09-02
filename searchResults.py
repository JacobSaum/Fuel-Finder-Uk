import sqlite3
from geocoding import geocodingLogic, geocodingLogicFromCoords
from sorting_scripts.priceSorting import sortFuelPrice, getStationData, FUEL_COLUMNS
from sorting_scripts.distanceSorting import sortDistance
from sorting_scripts.valueSorting import sortValue
import re

conn = sqlite3.connect("pfs_data.db", check_same_thread=False)
cur = conn.cursor()

def isValidPostcode(postcode):
    pattern = r"^[A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2}$"
    return bool(re.match(pattern, postcode.strip().upper()))

# full details for a single station, for the "station details" view
def getStationDetails(pfs_id):
    cur.execute("""
        SELECT pfs_id, brand_name, is24hr, postcode, address_line_1, address_line_2, city, county,
               latitude, longitude, isToilets, isCarWash, isAdBlue, isScreenwash, isWater,
               e5_price, e10_price, b7s_price, b7p_price
        FROM pfs_data
        WHERE pfs_id = ? AND perm_closure == 0 AND temp_closure == 0
    """, (pfs_id,))
    row = cur.fetchone()
    if row is None:
        return None

    return {
        "id": row[0], "brand_name": row[1], "is24hr": bool(row[2]), "postcode": row[3],
        "address_line_1": row[4], "address_line_2": row[5], "city": row[6], "county": row[7],
        "latitude": row[8], "longitude": row[9],
        "amenities": {
            "toilets": bool(row[10]), "car_wash": bool(row[11]), "adblue": bool(row[12]),
            "screenwash": bool(row[13]), "water": bool(row[14]),
        },
        "prices": {"e5": row[15], "e10": row[16], "b7s": row[17], "b7p": row[18]},
    }

def fuelSearch(fuelType, searchRadius, sortby="price", postcode=None, lat=None, lon=None, avg_mpg=40, fill_litres=40):

    if postcode is not None:
        if isValidPostcode(postcode) == False:
            raise ValueError(f"{postcode} is not a valid postcode.")
        valid_stations = geocodingLogic(postcode, searchRadius)
    elif lat is not None and lon is not None:
        valid_stations = geocodingLogicFromCoords(lat, lon, searchRadius)
    else:
        raise ValueError("A postcode or current location is required.")

    allStationData = getStationData()               

    nearbyStationData = [row for row in allStationData if row[0] in valid_stations]

    if sortby == "price":
        sortedStations = sortFuelPrice(fuelType, nearbyStationData)
        results = [{"brand_name": r[1], "price": r[FUEL_COLUMNS[fuelType]],
                    "distance": valid_stations[r[0]], "id": r[0]} for r in sortedStations]

    elif sortby == "distance":
        sortedStations = sortDistance(nearbyStationData, valid_stations, fuelType)
        results = [{"brand_name": r[1], "price": r[FUEL_COLUMNS[fuelType]],
                    "distance": valid_stations[r[0]], "id": r[0]} for r in sortedStations]

    elif sortby == "value":
        sortedStations = sortValue(fuelType, valid_stations, nearbyStationData, avg_mpg=avg_mpg, fill_litres=fill_litres)
        results = [{"brand_name": r[1], "price": r[FUEL_COLUMNS[fuelType]],
                    "distance": valid_stations[r[0]], "id": r[0],
                    "fill_cost": round(r[-1] * fill_litres / 100, 2)} for r in sortedStations]

    else: 
        raise ValueError(f"unknown sortby option: {sortby}")

    if len(results) == 0:
        raise LookupError(f"No Petrol Stations Within Search Radius.")

    return results