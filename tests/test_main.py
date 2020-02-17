from six import iteritems

from anyway.flask_app import parse_data
from anyway.models import AccidentMarker


def test_data_null():
    assert parse_data(AccidentMarker, None) is None


def test_bad_data():
    assert parse_data(AccidentMarker, dict(type=1, title="No properties")) is None


def test_parse_marker():
    marker_dummy = dict(type=1, title="test title", description="test description", latitude=1, longitude=1)
    marker = parse_data(AccidentMarker, marker_dummy)
    for key, value in iteritems(marker_dummy):
        assert getattr(marker, key) == value
