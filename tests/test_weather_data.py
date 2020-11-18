import logging
from datetime import datetime

from sqlalchemy import func

from anyway.app_and_db import db
from anyway.backend_constants import BE_CONST
from anyway.models import (
    AccidentMarker,
    AccidentWeather,
)
from anyway.parsers.cbs.weather_data import ensure_accidents_weather_data


class TestWeatherData:

    def _insert_accident_marker(self, created=None):
        logging.info("Inserting test accident marker")

        # to not conflict with existing ids find max value and add one
        accident_marker_id = db.session.query(func.max(AccidentMarker.id)).one()[0] + 1
        logging.debug(f"Calculated id for accident marker: {accident_marker_id}")
        accident_marker = AccidentMarker(
            id=accident_marker_id,
            provider_and_id=0,
            provider_code=BE_CONST.CBS_ACCIDENT_TYPE_1_CODE,
            accident_year=2020,
            latitude=32.0580,
            longitude=34.7588,
        )
        if created:
            accident_marker.created = created

        db.session.add(accident_marker)
        db.session.commit()

        return accident_marker_id

    def test_ensure_accidents_weather_data(self):
        accident_marker_id = self._insert_accident_marker()

        logging.debug("Verifying accident marker does not have weather data")
        accident_marker = db.session.query(AccidentMarker).filter(AccidentMarker.id == accident_marker_id).one()
        assert accident_marker.weather_data is None

        # the test DB may have other markers we don't want to add weather data to, so ensuring only our marker
        filters = (
            AccidentMarker.id == accident_marker_id,
        )
        number_of_accidents_updated = ensure_accidents_weather_data(filters=filters)
        assert number_of_accidents_updated == 1

        logging.debug("Verifying weather data added to accident marker")
        accident_marker = db.session.query(AccidentMarker).filter(AccidentMarker.id == accident_marker_id).one()
        assert accident_marker.weather_data is not None

        logging.debug(f"Weather data verified {accident_marker.weather_data}")

        logging.debug("Verifying another run of ensure weather data changes nothing")
        number_of_accidents_updated = ensure_accidents_weather_data(filters=filters)
        assert number_of_accidents_updated == 0

        logging.debug("Removing test data")
        db.session.query(AccidentMarker).filter(AccidentMarker.id == accident_marker_id).delete()
        db.session.query(AccidentWeather).filter(AccidentWeather.id == accident_marker.weather_data.id).delete()
        db.session.commit()

    def test_ensure_accidents_weather_data_with_date_filter(self):
        old_date = datetime(year=2010, day=1, month=1)
        new_date = datetime(year=2020, day=1, month=1)
        old_accident_marker_id = self._insert_accident_marker(old_date)
        new_accident_marker_id = self._insert_accident_marker(new_date)

        # the test DB may have other markers we don't want to add weather data to, so ensuring only our marker
        filters = (
            AccidentMarker.id.in_([old_accident_marker_id, new_accident_marker_id]),
        )
        filter_date = datetime(year=2015, day=1, month=1)
        number_of_accidents_updated = ensure_accidents_weather_data(filter_date, filters)

        # only one accident will be updated since only one is after the filter date
        assert number_of_accidents_updated == 1

        logging.debug("Removing test data")
        accident_marker = db.session.query(AccidentMarker).filter(AccidentMarker.id == new_accident_marker_id).one()
        db.session.query(AccidentWeather).filter(AccidentWeather.id == accident_marker.weather_data.id).delete()
        db.session.query(AccidentMarker).filter(AccidentMarker.id == new_accident_marker_id).delete()
        db.session.query(AccidentMarker).filter(AccidentMarker.id == old_accident_marker_id).delete()
        db.session.commit()
