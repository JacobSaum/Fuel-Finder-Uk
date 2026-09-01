
import sqlite3
import csv

conn = sqlite3.connect("pfs_data.db")
cur = conn.cursor()

def readCsv():

    schema_columns = ["pfs_id", "brand_name", "temp_closure", "perm_closure", "is24hr", "postcode", "address_line_1", "address_line_2", "city", "county", "latitude", "longitude", "isToilets", "isCarWash", "isAdBlue", "isScreenwash", "isWater", "e5_price", "e10_price", "b7s_price", "b7p_price", "e5_price_updated", "e10_price_updated", "b7s_price_updated", "b7p_price_updated"]

    csv_columns = ["forecourts.node_id", "forecourts.brand_name", "forecourts.temporary_closure", "forecourts.permanent_closure", "forecourts.amenities.twenty_four_hour_fuel", "forecourts.location.postcode", "forecourts.location.address_line_1", "forecourts.location.address_line_2", "forecourts.location.city", "forecourts.location.county", "forecourts.location.latitude", "forecourts.location.longitude", "forecourts.amenities.customer_toilets", "forecourts.amenities.vehicle_services.car_wash", "forecourts.amenities.fuel_and_energy_services.adblue_pumps", "forecourts.amenities.air_pump_or_screenwash", "forecourts.amenities.water_filling", "forecourts.fuel_price.E5", "forecourts.fuel_price.E10", "forecourts.fuel_price.B7S", "forecourts.fuel_price.B7P", "forecourts.price_change_effective_timestamp.E5", "forecourts.price_change_effective_timestamp.E10", "forecourts.price_change_effective_timestamp.B7S", "forecourts.price_change_effective_timestamp.B7P"]

    bool_fields = {
        "forecourts.temporary_closure",
        "forecourts.permanent_closure",
        "forecourts.amenities.twenty_four_hour_fuel",
        "forecourts.amenities.customer_toilets",
        "forecourts.amenities.vehicle_services.car_wash",
        "forecourts.amenities.fuel_and_energy_services.adblue_pumps",
        "forecourts.amenities.air_pump_or_screenwash",
        "forecourts.amenities.water_filling",
    }

    placeholders = ", ".join(["?"] * len(schema_columns))
    column_list = ", ".join(schema_columns)

    query = f"INSERT OR REPLACE INTO pfs_data ({column_list}) VALUES ({placeholders})"

    with open("fuelData.csv") as f:
        reader = csv.DictReader(f)
        for row in reader:
            values = []
            for csv_col in csv_columns:
                val = row[csv_col]
                if csv_col in bool_fields:
                    val = 1 if str(val).strip().lower() == "true" else 0
                values.append(val)
            
            cur.execute(query, tuple(values))

    conn.commit()

def printFirstRows():
    cur.execute("SELECT * FROM pfs_data WHERE pfs_id = ?", ("db5e336141f733ba061d971f3df4c6e267ea5ba406643ad03c9406a887e93dde",))
    row = cur.fetchone()
    print(row)



def ingestLogic():

    cur.execute("""
        CREATE TABLE IF NOT EXISTS pfs_data (
            pfs_id TEXT PRIMARY KEY,
            brand_name TEXT,
            temp_closure INTEGER,
            perm_closure INTEGER,
            is24hr INTEGER,
            postcode TEXT,
            address_line_1 TEXT,
            address_line_2 TEXT,
            city TEXT,
            county TEXT,
            latitude TEXT,
            longitude TEXT,
            isToilets INTEGER,
            isCarWash INTEGER,
            isAdBlue INTEGER,
            isScreenwash INTEGER,
            isWater INTEGER,
            e5_price REAL,
            e10_price REAL,
            b7s_price REAL,
            b7p_price REAL,
            e5_price_updated TEXT,
            e10_price_updated TEXT,
            b7s_price_updated TEXT,
            b7p_price_updated TEXT
        )
        
    """)

    conn.commit()

    readCsv()

    conn.close()

        

