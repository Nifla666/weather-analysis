import WeatherAnalyzer

if __name__ == '__main__':
    analyzer = WeatherAnalyzer.WeatherAnalyzer()
    berlin_id = analyzer.add_location("Berlin", 52.52, 13.40)
    analyzer.fetch_weather_data(berlin_id)
    analyzer.get_weather_data(berlin_id)
    analyzer.list_all_locations()
    analyzer.start_periodic_fetching(interval_minutes=1)