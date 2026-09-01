import sqlite3

conn = sqlite3.connect("pfs_data.db")
cur = conn.cursor()

# gets simplified version of data with only fuel prices and id
def getStationData():
    cur.execute("""
        SELECT pfs_id, brand_name, e5_price, e10_price, b7s_price, b7p_price
        FROM pfs_data
        WHERE perm_closure == 0 AND temp_closure == 0
    """)
    return cur.fetchall()

FUEL_COLUMNS = {
    "e5": 2,
    "e10": 3,
    "b7s": 4,
    "b7p": 5
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

    return sorted(priced, key=lambda row: row[col_index])
    
