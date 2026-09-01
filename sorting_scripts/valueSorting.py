# sorts the pfs' into order by how much money you will save by going there.

import sqlite3

conn = sqlite3.connect("pfs_data.db", check_same_thread=False)
cur = conn.cursor()

LITRES_PER_GALLON = 4.54609
avg_mpg = 40 
fill_litres = 40

FUEL_COLUMNS = {
    "e5": 2,
    "e10": 3,
    "b7s": 4,
    "b7p": 5
}

# gets simplified version of data with relevant feilds

def getStationData():
    cur.execute("""
        SELECT pfs_id, brand_name, e5_price, e10_price, b7s_price, b7p_price
        FROM pfs_data
        WHERE perm_closure == 0 AND temp_closure == 0
    """)
    return cur.fetchall()

# sorts by effective price after travel is taken into account
def sortValue(fuelType, distances, stationData, avg_mpg=40, fill_litres=40):

    if fuelType not in FUEL_COLUMNS:
        raise ValueError(f"Unknown fuel type: {fuelType}")

    column = FUEL_COLUMNS[fuelType]

    mpl = avg_mpg/LITRES_PER_GALLON

    print(f"stationData length: {len(stationData)}")
    print(f"distances length: {len(distances)}")
    if stationData:
        print(f"sample row: {stationData[0]}")
    if distances:
        sample_key = next(iter(distances))
        print(f"sample distance key: {sample_key}, value: {distances[sample_key]}")

    scored = []
    for row in stationData:
        station_id = row[0]
        price = row[column]

        if not isinstance(price, (int, float)):
            continue 

        distance = distances.get(station_id)
        if distance is None:
            continue

        trip_miles = distance * 2
        litres_used = trip_miles / mpl
        travel_cost = litres_used * price

        cost_per_litre_travel = travel_cost / fill_litres
        effective_price = price + cost_per_litre_travel

        scored.append((*row, effective_price))

    print(f"scored length: {len(scored)}")
    return sorted(scored, key=lambda r: r[-1])





    
