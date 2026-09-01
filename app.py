from flask import Flask, render_template
from scripts.ingest import ingestLogic
from searchResults import fuelSearch

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

if __name__ == "__main__":
    ingestLogic()
    results = fuelSearch("e10", "AB39 8AL", 15, "distance")
    print(results)

    
    app.run(debug=True)