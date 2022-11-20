import pytest
from factory import make_factory, Iterator

from anyway import models
from anyway.app_and_db import db
from anyway.backend_constants import InjurySeverity
from anyway.factories import InvolvedFactory, UrbanAccidentMarkerFactory, \
    SuburbanAccidentMarkerFactory, RoadSegmentFactory
from anyway.vehicle_type import VehicleType
from anyway.widgets import widget_utils


@pytest.fixture()
def db_session():
    yield db.session
    db.session.rollback()


@pytest.mark.skip(reason="requires empty db")
def test_get_involved_counts_urban_location(db_session):
    severities_to_include = [InjurySeverity.SEVERE_INJURED, InjurySeverity.KILLED]
    severities_to_exclude = [InjurySeverity.LIGHT_INJURED]
    vehicle_types_to_include = [VehicleType.ELECTRIC_SCOOTER]
    vehicle_types_to_exclude = [VehicleType.BUS]

    severities_to_test = severities_to_include + severities_to_exclude
    vehicle_types_to_test = vehicle_types_to_include + vehicle_types_to_exclude

    severely_injured_killed_factory = make_factory(models.Involved,
                                                   injury_severity=Iterator([severity.value for severity in severities_to_test]),
                                                   vehicle_type=Iterator([v_type.value for v_type in vehicle_types_to_test]),
                                                   FACTORY_CLASS=InvolvedFactory,
                                                   )
    start_year = 2019
    years_with_data = 2

    for i in range(years_with_data):
        accident = UrbanAccidentMarkerFactory.create(accident_year=2020 + i)
        severely_injured_killed_factory.create_batch(len(severities_to_test) * len(vehicle_types_to_test),
                                                     accident_id=accident.id,
                                                     provider_code=accident.provider_code,
                                                     accident_year=accident.accident_year)
    results = widget_utils.get_involved_counts(start_year - 1, start_year + years_with_data + 1,
                                                    severities_to_include,
                                                    vehicle_types_to_include,
                                                    {'yishuv_symbol': 1})
    assert len(results) == years_with_data
    for res in results:
        assert res['value'] == len(severities_to_include) * \
              len(vehicle_types_to_include)


@pytest.mark.skip(reason="requires empty db")
def test_get_involved_counts_suburban_location(db_session):
    severity_to_include = InjurySeverity.SEVERE_INJURED
    vehicle_type_to_include = VehicleType.ELECTRIC_SCOOTER
    road_segment_to_include = 2
    road_segment_to_exclude = 4
    accident_year = 2020

    for segment in (road_segment_to_include, road_segment_to_exclude):
        accident = SuburbanAccidentMarkerFactory.create(accident_year=accident_year, road1=segment * 10)
        RoadSegmentFactory(road = segment * 10, segment_id = segment)
        InvolvedFactory(accident_id=accident.id,
                        provider_code=accident.provider_code,
                        accident_year=accident.accident_year,
                        injury_severity=severity_to_include.value,
                        vehicle_type=vehicle_type_to_include.value
                        )
    results = widget_utils.get_involved_counts(accident_year, accident_year,
                                               [severity_to_include],
                                               [vehicle_type_to_include],
                                               {'road_segment_id': road_segment_to_include})
    assert len(results) == 1
    assert results[0]['value'] == 1