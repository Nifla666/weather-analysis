import sqlite3
from datetime import datetime
import requests
import time

class WeatherAnalyzer:

    def __init__(self, db_name="weather_data.db"):
        self.db_name = db_name
        # Using open Meteo, because it is completely open source
        self.api_url = "https://api.open-meteo.com/v1/forecast"
        self.init_database()

    # Creates the database tables if they don't already exist
    def init_database(self):
        # Creating connection to the database self.db_name, creating it if it doesn't exist yet
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()

        # Creating table for safed places
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Creating table for weather data with linked location via the location id
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS weather_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                location_id INTEGER NOT NULL,
                temperature REAL,
                precipitation REAL,
                humidity REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (location_id) REFERENCES locations (id)
            )
        """)

        # Creating table for configurations
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS configurations (
                id VARCHAR(50) NOT NULL PRIMARY KEY,
                integer_value INTEGER
            )
        """)
        # Inserting the standard interval for periodic fetching if it isn't in the table
        cursor.execute("""
            SELECT id, integer_value FROM configurations WHERE id = ?
        """, ("fetch_interval_minutes", ))
        interval_configuration = cursor.fetchone()
        if interval_configuration is None:
            cursor.execute("""
                INSERT INTO configurations (id, integer_value) VALUES (?, ?)
            """, ("fetch_interval_minutes", 30))

        connection.commit()
        connection.close()
        print("database initialized")

    # Adds a location to the location table and returns its id
    # if it already exists it returns the id of the existing location
    def add_location(self, name, latitude, longitude):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()

        # check if name or latitude and longitude already exist in table
        cursor.execute("""
            SELECT * FROM locations
        """)
        all_locations = cursor.fetchall()
        for location in all_locations:
            if location[1] == name:
                print(f"location {name} already exists with id {location[0]}")
                connection.close()
                return location[0]
            if location[2] == latitude and location[3] == longitude:
                print(f"a location with latitude {latitude} and longitude {longitude} already exists with id {location[0]}")
                connection.close()
                return location[0]

        # Inserting the location into the table
        cursor.execute("""
            INSERT INTO locations (name, latitude, longitude) VALUES (?, ?, ?)           
        """, (name, latitude, longitude))

        location_id = cursor.lastrowid
        connection.commit()
        connection.close()

        print(f"location {name} added with id {location_id}")

        return location_id

    # Getting the weather data from the API and saving it in the database
    def fetch_weather_data(self, location_id):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()

        # First getting the location details
        cursor.execute("""
            SELECT name, latitude, longitude FROM locations WHERE id = ?           
        """, (location_id,))
        location = cursor.fetchone()

        if location is None:
            print(f"location with id {location_id} not found")
            connection.close()
            return False

        # Preparing parameters for API call
        name, latitude, longitude = location
        parameters = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,precipitation,relative_humidity_2m"
        }

        # Trying to get the data from the API
        try:
            response = requests.get(self.api_url, params=parameters)
            # If status code is between 200 and 299 this does nothing but if something goes wrong while getting the
            # website a HTTPError will be raised
            response.raise_for_status()
            # Get the fetched json data and splitting it in our requested values
            data = response.json()
            current = data["current"]
            temperature = current["temperature_2m"]
            precipitation = current["precipitation"]
            humidity = current["relative_humidity_2m"]

            # Inserting the fetched data in our database timestamp is automatically set to current timestamp
            cursor.execute("""
                INSERT INTO weather_data (location_id, temperature, precipitation, humidity) 
                VALUES (?, ?, ?, ?)
            """, (location_id, temperature, precipitation, humidity))

            connection.commit()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] weather data for location {name} saved with values: {temperature}°C, {precipitation}mm, {humidity}%")

        except requests.exceptions.RequestException as e:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] getting weather data for location {name} failed with exception: {e}")
            return False

        connection.close()
        return True

    # Getting the weather data for all saved locations
    def fetch_all_locations(self):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()

        cursor.execute("""
            SELECT id FROM locations           
        """)
        all_locations = cursor.fetchall()
        connection.close()

        for (location_id, ) in all_locations:
            self.fetch_weather_data(location_id)

    # Returning the last saved weather data
    def get_weather_data(self, location_id, limit=10):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()

        # Joining the two tables by the location_id in this query to also get the name of the location
        # They will be returned in descending order regarding the timestamps
        cursor.execute("""
            SELECT l.name, w.temperature, w.precipitation, w.humidity, w.timestamp 
            FROM weather_data w
            JOIN locations l ON w.location_id = l.id
            WHERE  w.location_id = ?
            ORDER BY w.timestamp DESC
            LIMIT ?
        """, (location_id, limit))

        data = cursor.fetchall()
        connection.close()

        return data

    # Returning the last saved weather data as a json compatible dictionary
    def get_weather_data_json(self, location_id, limit=10):
        data = self.get_weather_data(location_id, limit)

        if data is None:
            return None

        return {
            "location": data[0][0],
            "data": [
                {
                    "temperature": row[1],
                    "precipitation": row[2],
                    "humidity": row[3],
                    "timestamp": row[4]
                }
                for row in data
            ]
        }

    # Printing the last saved weather data on the console
    def print_weather_data(self, location_id, limit=10):
        data = self.get_weather_data(location_id, limit)

        # Printing data on console if some data does exist
        if data is None:
            print(f"no weather data found for location {location_id}")
            return

        print(f"\nWeather data for {data[0][0]}:")
        print(f"{'timestamp':<20} {'temperature':<10} {'precipitation':<15} {'humidity':<15}")

        for name, temperature, precipitation, humidity, timestamp in data:
            print(f"{timestamp:<20} {temperature}°C{'':<6} {precipitation}mm{'':<11} {humidity}%")

    # Returning all saved locations
    def get_all_locations(self):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()

        cursor.execute("""
            SELECT id, name, latitude, longitude FROM locations           
        """)
        all_locations = cursor.fetchall()
        connection.close()

        return all_locations

    # Returning all saved locations as json compatible dictionary
    def get_all_locations_json(self):
        locations = self.get_all_locations()

        return {
            "locations": [
                {
                    "id": location[0],
                    "name": location[1],
                    "latitude": location[2],
                    "longitude": location[3]
                }
                for location in locations
            ]
        }

    # Printing all saved locations on the console
    def print_all_locations(self):
        all_locations = self.get_all_locations()

        if all_locations is None:
            print("no locations saved in database")
            return

        print("\nAll saved locations:")

        for (location_id, name, latitude, longitude) in all_locations:
            print(f"ID {location_id}: {name} (latitude: {latitude}, longitude: {longitude})")

    # Getting the currently saved interval for the periodic fetching from the configurations table in minutes
    def get_periodic_fetch_interval(self):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()

        cursor.execute("""
                    SELECT integer_value FROM configurations WHERE id = ?
        """, ("fetch_interval_minutes",))
        interval_configuration = cursor.fetchone()
        if interval_configuration is None:
            return 30

        return interval_configuration[0]

    # Saving a new interval for the periodic fetching in the configurations table
    def set_periodic_fetch_interval(self, interval):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE configurations SET integer_value = ? WHERE id = ?
        """, (interval, "fetch_interval_minutes"))
        connection.commit()
        connection.close()
        print(f"{interval} set as new periodic fetch interval")

    # Periodically fetch the weather data for all saved locations in the specified interval (not used in the api)
    def start_periodic_fetching(self, interval_minutes=30):
        print(f"\nperiodic fetching of weather data in intervals of {interval_minutes} minutes initiating...")
        print("press CTRL+C to stop fetching") # Keyboard interrupt didn't really work in PyCharm

        interval_seconds = interval_minutes * 60
        all_locations = self.get_all_locations()

        if all_locations is None:
            return

        try:
            while True:
                # Fetching all weather data
                self.fetch_all_locations()
                # Wait for next fetch time
                time.sleep(interval_seconds)

        except KeyboardInterrupt:
            print("\nautomatic fetching disabled")