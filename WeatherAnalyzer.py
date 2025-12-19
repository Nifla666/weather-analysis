import sqlite3
from datetime import datetime

import requests

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
            return

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

        connection.close()

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

