import sqlite3

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