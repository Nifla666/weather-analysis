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