import unittest
from main import parse_data
from models import Marker

class TestParseData(unittest.TestCase):

    def setUp(self):
        self.marker_dummy = dict(type=1, title="test title", description="test description", latitude=1, longitude=1)
        self.bad_marker_dummy = dict(type=1, title="No properties")

    def tearDown(self):
        self.marker_dummy = None
        self.bad_marker_dummy = None

    def test_data_null(self):
        self.assertIsNone(parse_data(Marker, None))

    def test_bad_data(self):
        self.assertIsNone(parse_data(Marker, self.bad_marker_dummy))

    def test_parse_marker(self):
        marker = parse_data(Marker, self.marker_dummy)
        for key, value in self.marker_dummy.iteritems():
            self.assertEqual(marker.getattr(key), value)

if __name__ == '__main__':
    unittest.main()
    suite = unittest.TestLoader().loadTestsFromTestCase(TestParseData)
    unittest.TextTestRunner(verbosity=2).run(suite)
