import unittest

from anyway.flask_app import parse_data
from anyway.models import AccidentMarker


class MainTest(unittest.TestCase):
    def test_data_null(self):
        self.assertIsNone(parse_data(AccidentMarker, None))

    def test_bad_data(self):
        self.assertIsNone(parse_data(AccidentMarker, dict(type=1, title="No properties")))

    def test_parse_marker(self):
        marker_dummy = {
            "type": 1,
            "title": "test title",
            "description": "test description",
            "latitude": 1,
            "longitude": 1,
        }
        marker = parse_data(AccidentMarker, marker_dummy)
        for key, value in marker_dummy.items():
            self.assertEqual(getattr(marker, key), value)
