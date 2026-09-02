from geocoding import geocodingLogic, geocodingLogicFromCoords
from sorting_scripts.priceSorting import sortFuelPrice, getStationData, FUEL_COLUMNS
from sorting_scripts.distanceSorting import sortDistance
from sorting_scripts.valueSorting import sortValue
import re

def isValidPostcode(postcode):
    pattern = r"^[A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2}$"
    return bool(re.match(pattern, postcode.strip().upper()))

def fuelSearch(fuelType, searchRadius, sortby="price", postcode=None, lat=None, lon=None):

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
        sortedStations = sortValue(fuelType, valid_stations, nearbyStationData)
        results = [{"brand_name": r[1], "price": r[FUEL_COLUMNS[fuelType]],
                    "distance": valid_stations[r[0]], "id": r[0]} for r in sortedStations]

    else: 
        raise ValueError(f"unknown sortby option: {sortby}")

    if len(results) == 0:
        raise LookupError(f"No Petrol Stations Within Search Radius.")

    return results