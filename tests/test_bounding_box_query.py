import unittest
from models import Marker  # for Marker.bounding_box_query
import datetime


class TestQueryFilters(unittest.TestCase):
    cyear = str(datetime.datetime.now().strftime("%Y"))
    global start_date
    start_date = "01/01/%s" % cyear
    global end_date
    end_date = "01/01/%s" % str(int(cyear)-1)

    def setUp(self):
        self.query = Marker.bounding_box_query(ne_lat=32.36, ne_lng=35.088, sw_lat=32.292, sw_lng=34.884,
                                               start_date=start_date, end_date=end_date,
                                               fatal=False, severe=True, light=True, inaccurate=False,
                                               is_thin=False, yield_per=None)

    def tearDown(self):
        self.query = None

    def test_location_filters(self):
        for marker in self.query:
            self.assertEqual(self.query['sw_lat'] < marker.latitude < self.query['ne_lat'], True)
            self.assertEqual(self.query['sw_lng'] < marker.longitude < self.query['ne_lng'], True)

    def test_accuracy_filter(self):
        for marker in self.query:
            self.assertEqual(marker['inaccurate'], False)

    def test_severity_filters(self):
        for marker in self.query:
            self.assertEqual(marker['fatal'], False)
            self.assertEqual(marker['severe'], True)
            self.assertEqual(marker['light'], True)


if __name__ == '__main__':
    unittest.main()
    suite = unittest.TestLoader().loadTestsFromTestCase(TestQueryFilters)
    unittest.TextTestRunner(verbosity=2).run(suite)