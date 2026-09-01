from geocoding import geocodingLogic
from sorting import sortFuelPrice, getStationData, FUEL_COLUMNS

def fuelSearch(fuelType, postcode, searchRadius):
    valid_stations = geocodingLogic(postcode, searchRadius)   # {pfs_id: distance}

    allStationData = getStationData()                          # (pfs_id, brand_name, e5_price, e10_price, b7s_price, b7p_price)

    nearbyStationData = [row for row in allStationData if row[0] in valid_stations]

    sortedStations = sortFuelPrice(fuelType, nearbyStationData)

    col_index = FUEL_COLUMNS[fuelType]

    results = []
    for row in sortedStations:
        station_id = row[0]
        brand_name = row[1]
        price = row[col_index]
        distance = valid_stations[station_id]

        results.append({
            "brand_name": brand_name,
            "price": price,
            "distance": distance
        })

    print(results)
    return results