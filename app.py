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
    searchDist = float(request.args.get("searchDist"))
    sortBy = request.args.get("sortBy")

    try:
        results = fuelSearch(fuelType, postcode, searchDist, sortBy)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except LookupError as e:
        return jsonify({"error": str(e)}), 404

    return jsonify(results)

if __name__ == "__main__":
    ingestLogic()


    
    app.run(debug=True)