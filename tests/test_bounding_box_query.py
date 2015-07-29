import unittest
from models import Marker  # for Marker.bounding_box_query
import datetime

# This tests year 2014 accidents as this is the current example git data for testing
# Once this changes to another year or to the current year's accidents (as should be) un-comment lines 11,13,15
# and change both 2014 and 2015 to: %s


class TestQueryFilters(unittest.TestCase):
    # cyear = str(datetime.datetime.now().strftime("%Y"))
    global start_date
    start_date = "01/01/2014"     # % cyear
    global end_date
    end_date = "01/01/2015"       # % str(int(cyear)-1)

    def setUp(self):
        self.query = Marker.bounding_box_query(ne_lat=32.36, ne_lng=35.088, sw_lat=32.292, sw_lng=34.884,
                                               start_date=start_date, end_date=end_date,
                                               fatal=False, severe=True, light=True, approx=False, accurate=True,
                                               is_thin=False, yield_per=None)

    def tearDown(self):
        self.query = None

    def test_location_filters(self):
        for marker in self.query:
            self.assertTrue(self.query['sw_lat'] <= marker.latitude <= self.query['ne_lat'])
            self.assertTrue(self.query['sw_lng'] <= marker.longitude <= self.query['ne_lng'])

    def test_accuracy_filter(self):
        for marker in self.query:
            self.assertFalse(marker['approx'])

    def test_severity_filters(self):
        for marker in self.query:
            self.assertFalse(marker['fatal'])
            self.assertTrue(marker['severe'])
            self.assertTrue(marker['light'])


if __name__ == '__main__':
    unittest.main()
    suite = unittest.TestLoader().loadTestsFromTestCase(TestQueryFilters)
    unittest.TextTestRunner(verbosity=2).run(suite)
