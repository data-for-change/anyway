import logging

from anyway.app_and_db import db
from anyway.models import (
    AccidentMarker,
    AccidentWeather,
)
from anyway.parsers.cbs.weather_interpolator import get_weather


def ensure_accidents_weather_data(start_date=None, filters=None):
    """
    :param start_date: Add start date filter to the query that lists accident markers to add weather data to
    :param filters: additional filters to add to the query that lists accident markers to add weather data to
    This is used mainly for testing - format DD-MM-YYYY
    :returns: int representing the number of accidents to which weather data was added
    """
    logging.info(f"Ensuring accidents weather data {start_date} {filters}")
    query = db.session.query(AccidentMarker).filter(AccidentMarker.weather_data == None)
    if start_date:
        query = query.filter(AccidentMarker.created > start_date)
    if filters is not None:
        query = query.filter(*filters)
    accident_markers_to_update = query.all()
    if accident_markers_to_update:
        logging.debug(
            f"Found accident markers without weather data. {len(accident_markers_to_update)}"
        )
    accidents_weather_data = []
    for accident_marker in query.all():
        weather_data = get_weather(
            accident_marker.latitude, accident_marker.longitude, accident_marker.created.isoformat()
        )
        accidents_weather_data.append(
            {
                "accident_id": accident_marker.id,
                "provider_and_id": accident_marker.provider_and_id,
                "provider_code": accident_marker.provider_code,
                "accident_year": accident_marker.accident_year,
                "rain_rate": weather_data["rain"],
            }
        )
    if accidents_weather_data:
        logging.debug(f"Adding weather data to accidents. {accidents_weather_data}")
        db.session.bulk_insert_mappings(AccidentWeather, accidents_weather_data)
        db.session.commit()
    logging.debug("Finished filling accidents weather data")
    return len(accident_markers_to_update) if accident_markers_to_update else 0
