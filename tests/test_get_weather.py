import anyway.parsers.cbs.weather_interpolator as weather_interpolator


class TestWeatherData:

    def test_get_weather_at_weather_station_location(self):
        """
        Target coordinates are very close to TEL-AVIV weather station
        So rain values at that station should be weighed at ~1 and values from other stations should be weighted at ~0
        """

        rain_in_tel_aviv = list(range(46, 58, 2))
        time_weighted_value = 0
        for idx in range(len(self._get_weights())):
            time_weighted_value += rain_in_tel_aviv[idx] * self._get_weights()[idx]

        weather_data = weather_interpolator.get_weather(32.0580, 34.7588, "2011-11-04T00:05:23", 3)
        assert abs(weather_data["rain"] - time_weighted_value) < 0.01

    def test_get_weather_at_equal_distance_from_3_weather_stations(self):
        """
        Target coordinates are at almost the same distance from 3 closest weather stations
        So rain values should be weighted equally
        """

        station_ids = [8, 5, 18]
        time_weighted_value_values = [0, 0, 0]

        for station_idx, station_id in enumerate(station_ids):
            rain_values = list(range(station_id, station_id+12, 2))
            for idx in range(len(self._get_weights())):
                time_weighted_value_values[station_idx] += rain_values[idx] * self._get_weights()[idx]

        expected_rain = sum(time_weighted_value_values) / len(time_weighted_value_values)

        weather_data = weather_interpolator.get_weather(33.0580, 34.7588, "2011-11-04T00:05:23", 3)
        assert abs(weather_data["rain"] - expected_rain) < 0.2

    def _get_weights(self):
        return [0.515625, 0.25, 0.125, 0.0625, 0.03125, 0.015625]
