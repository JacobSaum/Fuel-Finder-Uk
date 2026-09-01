import sqlite3

conn = sqlite3.connect("pfs_data.db")
cur = conn.cursor()

# gets simplified version of data with only fuel prices and id
def getStationData():
    cur.execute("""
        SELECT pfs_id, e5_price, e10_price, b7s_price, b7p_price
        FROM pfs_data
        WHERE perm_closure == 0 AND temp_closure == 0
    """)
    return cur.fetchall()

# maps column number to fuel type
FUEL_COLUMNS = {
    "e5": 1,
    "e10": 2,
    "b7s": 3,
    "b7p": 4
}

# sorts price by fuel type
def sortFuelPrice(fuelSortType, stationData):
    if fuelSortType not in FUEL_COLUMNS:
        raise ValueError(f"Unknown fuel type: {fuelSortType}")

    col_index = FUEL_COLUMNS[fuelSortType]

    priced = []
    for row in stationData:
        value = row[col_index]
        if isinstance(value, (int, float)):
            priced.append(row)
        elif isinstance(value, str) and value.strip() != "":

            try:
                converted = float(value)
                new_row = row[:col_index] + (converted,) + row[col_index + 1:]
                priced.append(new_row)
            except ValueError:
                continue 
    
    fuelPriceSortingLogic(sorted(priced, key=lambda row: row[col_index]), fuelSortType)

def fuelPriceSortingLogic(sortedStations, fuelSortType):
    
    for x in range(len(sortedStations)):
        station_id = sortedStations[x][0]
        cur.execute(f"""
                    SELECT pfs_id, {fuelSortType}_price
                    FROM pfs_data
                    WHERE perm_closure == 0 AND temp_closure == 0 AND pfs_id == ?
                """, (station_id,))
        return cur.fetchall()
