from WeatherAnalyzer import WeatherAnalyzer
from flask import Flask, jsonify, request
from flask_apscheduler import APScheduler
from datetime import datetime

# Global WeatherAnalyzer instance and scheduler
analyzer = WeatherAnalyzer()
scheduler = APScheduler()

# Creating flask app
app = Flask(__name__)

# Main endpoint with API documentation
# Get via: curl http://localhost:5000/
@app.route('/')
def home():
    return jsonify({
        "message": "Weather Analyzer API",
        "version": "1.0",
        "endpoints": {
            "GET /locations": "Retrieving all saved locations.",
            "POST /locations": "Adding new location (JSON: {name, latitude, longitude}).",
            "GET /weather/<location_id>": "Retrieving weather data for a given location (optional: ?limit=10).",
            "POST /weather/<location_id>/fetch": "Fetching new weather data for a given location.",
            "POST /weather/fetch-periodically": "Start periodic fetching all locations (optional ?interval-minutes=30)"
        }
    })

# Returning all saved locations
# Get via: curl http://localhost:5000/locations     # standard is GET so no -X option necessary
@app.route('/locations', methods=['GET'])
def get_locations():
    return jsonify(analyzer.get_all_locations_json())

# Adding new location
# Add via: curl -X POST http://localhost:5000/locations \
#               -H "Content-Type: application/json" \           # Body contains JSON data
#               -d "{\"name\":\"Hamburg\",\"latitude\":53.55,\"longitude\":9.99}"   # example for Hamburg
@app.route('/locations', methods=['POST'])
def add_location():
    data = request.get_json()

    if not data or "name" not in data or "latitude" not in data or "longitude" not in data:
        return jsonify({"error": "name, latitude and longitude necessary"}), 400    # Bad Request

    location_id = analyzer.add_location(data['name'], data['latitude'], data['longitude'])

    return jsonify({
        "success": True,
        "location_id": location_id,
        "name": data["name"]
    }), 201     # HTTP  status code resource created

# Returns weather data for given location
# Get via: curl http://localhost:5000/weather/1?limit=5 where 1 is an example id and from ? its optional
@app.route('/weather/<int:location_id>', methods=['GET'])
def get_weather(location_id):
    limit = request.args.get("limit", default=10, type=int)

    data = analyzer.get_weather_data_json(location_id, limit)

    if not data:
        return jsonify({"error": "No data found or location non existent"}), 404    # HTTP status code resource not found

    return jsonify(data)

# Retrieves new weather data for given location
# Get via: curl -X POST http://localhost:5000/weather/1/fetch where 1 is an example id
@app.route('/weather/<int:location_id>/fetch', methods=['POST'])
def fetch_weather_now(location_id):
    success = analyzer.fetch_weather_data(location_id)

    if not success:
        return jsonify({"error": "Error while fetching weather data"}), 500     # HTTP status code internal server error

    return jsonify({
        "success": True,
        "message": f"Weather data for location with ID {location_id} successfully fetched."
    })

# Start periodic fetching all locations (optional ?interval-minutes=30)
# Start via curl -X POST http://localhost:5000/weather/fetch-periodically?interval-minutes=30
@app.route('/weather/fetch-periodically', methods=['POST'])
def fetch_periodically():
    current_interval = analyzer.get_periodic_fetch_interval()
    interval_minutes = request.args.get("interval-minutes", default=current_interval, type=int)
    if interval_minutes < 0:
        return jsonify({"error": "Interval minutes must be greater than 0"}), 400

    # Save new value if it differs from the current
    if interval_minutes != current_interval:
        analyzer.set_periodic_fetch_interval(interval_minutes)

    print(scheduler.get_job("periodic-fetch"))
    if scheduler.get_job("periodic-fetch") is None:
        scheduler.add_job(func=analyzer.fetch_all_locations, trigger="interval", minutes=interval_minutes, next_run_time=datetime.now(), id="periodic-fetch")
        scheduler.start()
    else:
        scheduler.modify_job("periodic-fetch", trigger="interval", minutes=interval_minutes)

    return jsonify(f"periodic fetching initiated successfully (interval in minutes: {interval_minutes})"), 201

# Stop the periodic fetching job with one last fetch
# Stop via curl -X DELETE http://localhost:5000/weather/fetch-periodically
@app.route('/weather/fetch-periodically', methods=['DELETE'])
def stop_fetching_periodically():
    if scheduler.get_job("periodic-fetch"):
        scheduler.modify_job("periodic-fetch", trigger="date", run_date=datetime.now())
        return jsonify("periodic fetching terminated successfully"), 200

    return jsonify({"error": "no periodic fetch job found"}), 400

# Starting the Flask webserver
def start_api_server(port=5000):
    print(f"\nAPI-Server running on http://localhost:{port}")
    print("API-Documentation: http://localhost:5000/\n")
    app.run(host='0.0.0.0', port=port, debug=False)