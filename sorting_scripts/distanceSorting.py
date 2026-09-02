import sqlite3
from sorting_scripts.priceSorting import FUEL_COLUMNS

conn = sqlite3.connect("pfs_data.db", check_same_thread=False)
cur = conn.cursor()

# gets simplified version of data with relevant feilds

def getStationData():
    cur.execute("""
        SELECT pfs_id, brand_name, e5_price, e10_price, b7s_price, b7p_price
        FROM pfs_data
        WHERE perm_closure == 0 AND temp_closure == 0
    """)
    return cur.fetchall()

# sorts stations by distance to search location
def sortDistance(stationData, distances, fuelType):
    if fuelType not in FUEL_COLUMNS:
        raise ValueError(f"Unknown fuel type: {fuelType}")

    col_index = FUEL_COLUMNS[fuelType]

    distanced = []
    for row in stationData:
            value = row[col_index]
            if isinstance(value, (int, float)):
                new_row = row
            elif isinstance(value, str) and value.strip() != "":
                try:
                    converted = float(value)
                    new_row = row[:col_index] + (converted,) + row[col_index + 1:]
                except ValueError:
                    continue
            else:
                continue

            if distances.get(new_row[0]) is None:
                continue

            distanced.append(new_row)

    return sorted(distanced, key=lambda row: distances[row[0]])


    
