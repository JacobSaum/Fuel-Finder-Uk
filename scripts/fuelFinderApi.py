import os
import time
import sqlite3
import requests
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.environ.get("FUEL_FINDER_CLIENT_ID")
CLIENT_SECRET = os.environ.get("FUEL_FINDER_CLIENT_SECRET")
API_BASE_URL = os.environ.get("FUEL_FINDER_API_BASE_URL")
TOKEN_URL = os.environ.get("FUEL_FINDER_TOKEN_URL")

# confirmed live against the real API with real credentials.
STATIONS_PATH = os.environ.get("FUEL_FINDER_STATIONS_PATH", "/api/v1/pfs")
PRICES_PATH = os.environ.get("FUEL_FINDER_PRICES_PATH", "/api/v1/pfs/fuel-prices")

# our 4 fuel columns <- the API's fuel_type codes (API also has B10/HVO, which
# we don't have columns for and skip)
FUEL_TYPE_MAP = {"E5": "e5", "E10": "e10", "B7_STANDARD": "b7s", "B7_PREMIUM": "b7p"}

conn = sqlite3.connect("pfs_data.db", check_same_thread=False)
cur = conn.cursor()

_token_cache = {"access_token": None, "expires_at": 0}

# Fuel Finder API limits: 100 requests/minute, 1 concurrent request per client.
# We only ever issue one request at a time (no threads/async here), so the only
# thing left to enforce is pacing — this keeps us at ~90/min with headroom.
MIN_REQUEST_INTERVAL = 60 / 90
MAX_RETRIES = 5
_last_request_at = 0


def isConfigured():
    return bool(CLIENT_ID and CLIENT_SECRET and API_BASE_URL and TOKEN_URL)


# single choke point for every HTTP call to the Fuel Finder API: paces requests
# to stay under the 100/min limit and retries on 429 with backoff (honouring
# Retry-After when the server sends one).
def _throttledRequest(method, url, **kwargs):
    global _last_request_at

    for attempt in range(MAX_RETRIES):
        wait = MIN_REQUEST_INTERVAL - (time.time() - _last_request_at)
        if wait > 0:
            time.sleep(wait)

        response = requests.request(method, url, timeout=20, **kwargs)
        _last_request_at = time.time()

        if response.status_code != 429:
            return response

        retryAfter = response.headers.get("Retry-After")
        delay = float(retryAfter) if retryAfter else (2 ** attempt)
        print(f"[fuelFinderApi] rate limited (429) — retrying in {delay:.1f}s")
        time.sleep(delay)

    response.raise_for_status()
    return response


def _getAccessToken():
    if _token_cache["access_token"] and time.time() < _token_cache["expires_at"] - 30:
        return _token_cache["access_token"]

    if not isConfigured():
        raise RuntimeError(
            "Fuel Finder API is not configured — set FUEL_FINDER_API_BASE_URL and "
            "FUEL_FINDER_TOKEN_URL in .env (FUEL_FINDER_CLIENT_ID/SECRET are already set)."
        )

    response = _throttledRequest(
        "POST", TOKEN_URL,
        data={
            "grant_type": "client_credentials",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "scope": "fuelfinder.read",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    response.raise_for_status()
    payload = response.json()["data"]

    _token_cache["access_token"] = payload["access_token"]
    _token_cache["expires_at"] = time.time() + payload.get("expires_in", 3600)
    return _token_cache["access_token"]


def _authedGet(path, params=None):
    token = _getAccessToken()
    response = _throttledRequest(
        "GET", f"{API_BASE_URL}{path}",
        headers={"Authorization": f"Bearer {token}"},
        params=params,
    )
    return response


# yields one batch (list of items) at a time from a paginated endpoint.
# The API pages via a "batch-number" query param (1-indexed, ~500 items per
# batch) and signals the end by returning 404 once you go past the last one.
def _paginate(path, max_batches=200):
    batch = 1
    while batch <= max_batches:
        response = _authedGet(path, params={"batch-number": batch})
        if response.status_code == 404:
            break
        response.raise_for_status()

        items = response.json()
        if not items:
            break

        yield items
        batch += 1


def _dig(d, *path, default=None):
    for key in path:
        if not isinstance(d, dict):
            return default
        d = d.get(key)
    return d if d is not None else default


def _boolToInt(value):
    return 1 if value in (True, "true", "True", 1, "1") else 0


def _syncStations():
    upserted = 0
    for batch in _paginate(STATIONS_PATH):
        for station in batch:
            pfs_id = _dig(station, "node_id")
            if not pfs_id:
                continue

            amenities = _dig(station, "amenities", default=[]) or []

            cur.execute("""
                INSERT INTO pfs_data (
                    pfs_id, brand_name, temp_closure, perm_closure, is24hr, postcode,
                    address_line_1, address_line_2, city, county, latitude, longitude,
                    isToilets, isCarWash, isAdBlue, isScreenwash, isWater
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(pfs_id) DO UPDATE SET
                    brand_name=excluded.brand_name, temp_closure=excluded.temp_closure,
                    perm_closure=excluded.perm_closure, is24hr=excluded.is24hr,
                    postcode=excluded.postcode, address_line_1=excluded.address_line_1,
                    address_line_2=excluded.address_line_2, city=excluded.city,
                    county=excluded.county, latitude=excluded.latitude, longitude=excluded.longitude,
                    isToilets=excluded.isToilets, isCarWash=excluded.isCarWash,
                    isAdBlue=excluded.isAdBlue, isScreenwash=excluded.isScreenwash,
                    isWater=excluded.isWater
            """, (
                pfs_id,
                _dig(station, "brand_name"),
                _boolToInt(_dig(station, "temporary_closure")),
                _boolToInt(_dig(station, "permanent_closure")),
                _boolToInt("twenty_four_hour_fuel" in amenities),
                _dig(station, "location", "postcode"),
                _dig(station, "location", "address_line_1"),
                _dig(station, "location", "address_line_2"),
                _dig(station, "location", "city"),
                _dig(station, "location", "county"),
                _dig(station, "location", "latitude"),
                _dig(station, "location", "longitude"),
                _boolToInt("customer_toilets" in amenities),
                _boolToInt("car_wash" in amenities),
                _boolToInt("adblue_pumps" in amenities or "adblue_packaged" in amenities),
                _boolToInt("air_pump_or_screenwash" in amenities),
                _boolToInt("water_filling" in amenities),
            ))
            upserted += 1

    conn.commit()
    return upserted


def _syncPrices():
    updated = 0
    for batch in _paginate(PRICES_PATH):
        for entry in batch:
            pfs_id = _dig(entry, "node_id")
            if not pfs_id:
                continue

            prices = {}
            updatedAt = {}
            for fuelEntry in _dig(entry, "fuel_prices", default=[]) or []:
                column = FUEL_TYPE_MAP.get(_dig(fuelEntry, "fuel_type"))
                if column is None:
                    continue
                prices[column] = _dig(fuelEntry, "price")
                updatedAt[column] = _dig(fuelEntry, "price_last_updated")

            cur.execute("""
                UPDATE pfs_data SET
                    e5_price=COALESCE(?, e5_price), e10_price=COALESCE(?, e10_price),
                    b7s_price=COALESCE(?, b7s_price), b7p_price=COALESCE(?, b7p_price),
                    e5_price_updated=COALESCE(?, e5_price_updated),
                    e10_price_updated=COALESCE(?, e10_price_updated),
                    b7s_price_updated=COALESCE(?, b7s_price_updated),
                    b7p_price_updated=COALESCE(?, b7p_price_updated)
                WHERE pfs_id=?
            """, (
                prices.get("e5"), prices.get("e10"), prices.get("b7s"), prices.get("b7p"),
                updatedAt.get("e5"), updatedAt.get("e10"), updatedAt.get("b7s"), updatedAt.get("b7p"),
                pfs_id,
            ))
            updated += cur.rowcount

    conn.commit()
    return updated


# pulls the latest forecourt + price data from the live Fuel Finder API and
# upserts it into pfs_data, in place of the old fuelData.csv snapshot.
def syncFuelFinderData():
    stationCount = _syncStations()
    priceCount = _syncPrices()
    print(f"[fuelFinderApi] synced {stationCount} stations, updated prices for {priceCount} stations")
