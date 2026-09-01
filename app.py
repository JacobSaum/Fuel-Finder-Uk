from flask import Flask, render_template
from scripts.ingest import ingestLogic
from geocoding import geocodingLogic
from priceSorting import sortFuelPrice, getStationData

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

if __name__ == "__main__":
    ingestLogic()

    # gets list of id's of valid stations
    valid_stations = geocodingLogic("AB39 8AL", 20)

    #gets all stations' data
    allStationData = getStationData()

    # Gets data for stations that are only nearby
    nearbyStationData = [row for row in allStationData if row[0] in valid_stations]

    sortedStations = sortFuelPrice("e5", nearbyStationData)
    app.run(debug=True)