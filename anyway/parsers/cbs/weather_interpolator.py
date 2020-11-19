import datetime
import logging
import math
import collections
import random

from lxml import etree

WEATHER_HISTORY_WINDOW = 60 * 60  # sec
WEATHER_SAMPLING_INTERVAL = 10 * 60  # sec
WEATHER_STATION_XML = "anyway/parsers/cbs/weather_stations.xml"
DEFAULT_NUMBER_OF_INTERPOLATION_POINTS = 3


def get_weather(
    latitude, longitude, timestamp, interpolation_points=DEFAULT_NUMBER_OF_INTERPOLATION_POINTS
):
    timestamp = datetime.datetime.fromisoformat(timestamp)

    # Phase I: find N closest weather stations to target coordinates (N==interpolation_points)
    closest_stations = get_closest_stations(
        WEATHER_STATION_XML, latitude, longitude, interpolation_points
    )
    logging.debug(f"Closest stations: {str(closest_stations)}")

    # Phase II: find weather history for each station
    for idx in range(len(closest_stations)):
        closest_stations[idx]["weather"] = get_weather_at_station(
            closest_stations[idx]["id"], timestamp
        )

    # Phase III: Calculate time weighted weather for each station based on weather history
    for idx in range(len(closest_stations)):
        closest_stations[idx][
            "time_weighted_weather_parameters"
        ] = weight_weather_parameters_in_time_domain(closest_stations[idx]["weather"])

    # Phase IV: Create distance/weather_param_value tuples for spatial interpolation
    weather_parameters_for_spatial_interpolation = {}
    for station in closest_stations:
        for parameter_name, parameter_value in station["time_weighted_weather_parameters"].items():
            weather_parameters_for_spatial_interpolation.setdefault(parameter_name, []).append(
                (station["distance"], parameter_value)
            )

    # Phase V: Find weather parameters at target location using
    # inverse distance weighted interpolation on station weather data
    weather_at_target = {}
    for (
        weather_parameter,
        distance_value_tuples,
    ) in weather_parameters_for_spatial_interpolation.items():
        weather_at_target[weather_parameter] = perform_inverse_distance_weighted_interpolation(
            distance_value_tuples
        )

    logging.debug(f"Weather at target: {str(weather_at_target)}")

    return weather_at_target


def parse_xml(xml_file_location):
    """
    Parse the xml
    """
    with open(xml_file_location) as fobj:
        xml = fobj.read().encode()

    weather_stations_locations = []
    root = etree.fromstring(xml)  # pylint: disable=c-extension-no-member
    for appt in root.getchildren():
        weather_station_parameters = {}
        for elem in appt.getchildren():
            if elem.text:
                if elem.tag in ["longitude", "latitude", "altitude"]:
                    weather_station_parameters[elem.tag] = float(elem.text)
                elif elem.tag in ["id"]:
                    weather_station_parameters[elem.tag] = int(elem.text)
                else:
                    weather_station_parameters[elem.tag] = elem.text

        weather_stations_locations.append(weather_station_parameters)

    return weather_stations_locations


def get_distance(origin, destination):
    """
    Calculate the Haversine distance.

    Parameters
    ----------
    origin : tuple of float
        (lat, long)
    destination : tuple of float
        (lat, long)

    Returns
    -------
    distance_in_km : float

    Examples
    --------
    >>> origin = (48.1372, 11.5756)  # Munich
    >>> destination = (52.5186, 13.4083)  # Berlin
    >>> round(get_distance(origin, destination), 1)
    504.2
    """
    lat1, lon1 = origin
    lat2, lon2 = destination
    radius = 6371  # km

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) * math.sin(dlat / 2) + math.cos(math.radians(lat1)) * math.cos(
        math.radians(lat2)
    ) * math.sin(dlon / 2) * math.sin(dlon / 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    d = radius * c

    return d


def get_closest_stations(weather_stations_locations_xml, latitude, longitude, num_of_stations):

    # Load XML file with weather stations' Latitude/Longitude coordinates
    weather_stations_locations = parse_xml(weather_stations_locations_xml)

    # Calculate the distance of target location from each weather station
    target_location = (latitude, longitude)
    distances_to_weather_stations = {}
    for weather_station in weather_stations_locations:
        distance_to_station = get_distance(
            target_location, (weather_station["latitude"], weather_station["longitude"])
        )
        distances_to_weather_stations[distance_to_station] = weather_station

    # Sort the results
    sorted_distances = collections.OrderedDict(sorted(distances_to_weather_stations.items()))

    # Return response with N closest stations (N==num_of_stations)
    idx = 0
    closest_stations = []
    for _distance, weather_station in sorted_distances.items():
        weather_station.update({"distance": _distance})
        closest_stations.append(
            {
                "id": weather_station["id"],
                "name": weather_station["name"],
                # to avoid "divide by zero" situations, round 0 to 0.01
                "distance": max(0.01, _distance),
            }
        )

        idx += 1
        if idx >= num_of_stations:
            break

    return closest_stations


def get_weather_at_station(station_id, timestamp):
    # TODO: replace this mock with actual request to meteorological service API once we have the TOKEN
    # https://ims.gov.il/node/87

    results = []

    # The API should return response with samples in 10min intervals
    idx = station_id
    for delta_sec in range(0, WEATHER_HISTORY_WINDOW, WEATHER_SAMPLING_INTERVAL):
        results.append(
            {
                "timestamp": timestamp - datetime.timedelta(seconds=delta_sec),
                "weather_parameters": {
                    "temperature": random.uniform(0, 45),
                    "rain": idx,
                },
            }
        )

        idx += 2

    return results


def weight_weather_parameters_in_time_domain(weather_samples):
    weights = []
    for idx in range(len(weather_samples) - 1):
        weights.insert(0, 1.0 / (2 ** (len(weather_samples) - idx)))
    weights.insert(0, 1 - sum(weights))

    time_weighted_parameters = {}
    for idx, weather_sample in enumerate(weather_samples):
        for parameter_name, parameter_value in weather_sample["weather_parameters"].items():
            if parameter_name in ["rain"]:
                time_weighted_parameters[parameter_name] = (
                    time_weighted_parameters.get(parameter_name, 0) + parameter_value * weights[idx]
                )

    return time_weighted_parameters


def perform_inverse_distance_weighted_interpolation(distance_value_tuples):

    # https://math.stackexchange.com/questions/1336386/weighted-average-distance-between-3-or-more-points
    # https://stackoverflow.com/a/3119544
    numerator = 0
    denominator = 0
    for distance, value in distance_value_tuples:
        numerator += value / distance
        denominator += 1 / distance

    return numerator / denominator
