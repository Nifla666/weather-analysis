import WeatherAnalyzer
from WeatherAnalyzerAPI import start_api_server

if __name__ == '__main__':
    #analyzer = WeatherAnalyzer.WeatherAnalyzer()
    #berlin_id = analyzer.add_location("Berlin", 52.52, 13.40)
    #analyzer.fetch_weather_data(berlin_id)
    #analyzer.print_weather_data(berlin_id)
    #analyzer.print_all_locations()
    #analyzer.start_periodic_fetching(interval_minutes=1)
    start_api_server()