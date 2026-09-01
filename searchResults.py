from geocoding import geocodingLogic
from sorting_scripts.priceSorting import sortFuelPrice, getStationData, FUEL_COLUMNS
from sorting_scripts.distanceSorting import sortDistance
from sorting_scripts.valueSorting import sortValue

def fuelSearch(fuelType, postcode, searchRadius, sortby="price"):

    valid_stations = geocodingLogic(postcode, searchRadius)

    allStationData = getStationData()               

    nearbyStationData = [row for row in allStationData if row[0] in valid_stations]

    if sortby == "price":
        sortedStations = sortFuelPrice(fuelType, nearbyStationData)
        results = [{"brand_name": r[1], "price": r[FUEL_COLUMNS[fuelType]],
                    "distance": valid_stations[r[0]], "id": r[0]} for r in sortedStations]

    elif sortby == "distance":
        sortedStations = sortDistance(nearbyStationData, valid_stations)
        results = [{"brand_name": r[1], "price": r[FUEL_COLUMNS[fuelType]],
                    "distance": valid_stations[r[0]], "id": r[0]} for r in sortedStations]

    elif sortby == "value":
        sortedStations = sortValue(fuelType, valid_stations, nearbyStationData)
        results = [{"brand_name": r[1], "price": r[FUEL_COLUMNS[fuelType]],
                    "distance": valid_stations[r[0]], "id": r[0]} for r in sortedStations]

    else: 
        raise ValueError(f"unknown sortby option: {sortby}")

    return results