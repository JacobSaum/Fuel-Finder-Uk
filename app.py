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
    postcode = request.args.get("postcode")
    searchDistance = float(request.args.get("searchDistance"))
    sortType = request.args.get("sortType")

    results = fuelSearch(fuelType, postcode, searchDistance, sortType)

    return jsonify(results)

if __name__ == "__main__":
    ingestLogic()


    
    app.run(debug=True)