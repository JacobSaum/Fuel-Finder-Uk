import sqlite3

conn = sqlite3.connect("pfs_data.db", check_same_thread=False)
cur = conn.cursor()

# gets simplified version of data with relevant feilds

def getStationData():
    cur.execute("""
        SELECT pfs_id, brand_name
        FROM pfs_data
        WHERE perm_closure == 0 AND temp_closure == 0
    """)
    return cur.fetchall()

# sorts price by distance to pfs
def sortDistance(stationData, distances):

    return sorted(stationData, key=lambda row: distances[row[0]])


    
