import sys
from flask import Flask, render_template, request, jsonify
from scripts.ingest import ensureSchema, readCsv
from scripts.fuelFinderApi import syncFuelFinderData, isConfigured
from searchResults import fuelSearch, getStationDetails

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/fuelSearch")
def searchFuel():
    fuelType = request.args.get("fuelType")
    searchDist = float(request.args.get("searchDist"))
    sortBy = request.args.get("sortBy")
    locationType = request.args.get("locationType", "postcode")

    valueArgs = {}
    if sortBy == "value":
        valueArgs["avg_mpg"] = float(request.args.get("avgMpg", 40))
        valueArgs["fill_litres"] = float(request.args.get("fillLitres", 40))

    try:
        if locationType == "coords":
            lat = float(request.args.get("lat"))
            lon = float(request.args.get("lon"))
            results = fuelSearch(fuelType, searchDist, sortBy, lat=lat, lon=lon, **valueArgs)
        else:
            postcode = request.args.get("postcode")
            results = fuelSearch(fuelType, searchDist, sortBy, postcode=postcode, **valueArgs)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except LookupError as e:
        return jsonify({"error": str(e)}), 404

    return jsonify(results)

@app.route("/station/<station_id>")
def stationDetail(station_id):
    details = getStationDetails(station_id)
    if details is None:
        return jsonify({"error": "Station not found."}), 404
    return jsonify(details)

if __name__ == "__main__":
    ensureSchema()

    try:
        if isConfigured():
            try:
                syncFuelFinderData()
            except Exception as e:
                print(f"[fuelFinderApi] live sync failed ({e}) — falling back to fuelData.csv")
                readCsv()
        else:
            print("[fuelFinderApi] not configured (set FUEL_FINDER_API_BASE_URL / FUEL_FINDER_TOKEN_URL in .env) — using fuelData.csv")
            readCsv()
    except KeyboardInterrupt:
        print("\n[app] startup interrupted — exiting.")
        sys.exit(0)

    app.run(debug=True)