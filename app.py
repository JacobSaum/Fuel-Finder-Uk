from flask import Flask, render_template
from scripts.ingest import ingestLogic
from searchResults import fuelSearch
from flask import Flask, request, jsonify

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

if __name__ == "__main__":
    ingestLogic()


    
    app.run(debug=True)