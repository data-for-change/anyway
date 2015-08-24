import unittest
from models import Marker  # for Marker.bounding_box_query
import datetime

# This tests year 2014 accidents as this is the current example git data for testing
# Once this changes to another year or to the current year's accidents (as should be) un-comment lines 11,13,15
# and change both 2014 and 2015 to: %s


class TestQueryFilters(unittest.TestCase):
    """
    # cyear = str(datetime.datetime.now().strftime("%Y"))
    global start_date
    start_date = "01/01/2014"     # % cyear
    global end_date
    end_date = "01/01/2015"       # % str(int(cyear)-1)
    """

    def setUp(self):
        kwargs = {'approx': True, 'show_day': 7, 'show_discussions': True, 'accurate': True, 'surface': 0, 'weather': 0,
                  'district': 0, 'show_markers': True, 'show_fatal': True, 'show_time': 24, 'show_intersection': 3,
                  'show_light': True, 'sw_lat': 32.06711066128336, 'controlmeasure': 0, 'ne_lng': 34.799307929669226,
                  'show_severe': True, 'start_time': 25, 'acctype': 0, 'separation': 0, 'show_urban': 3, 'show_lane': 3,
                  'sw_lng': 34.78879367033085, 'zoom': 17, 'show_holiday': 0, 'end_time': 25, 'road': 0,
                  'ne_lat': 32.07254745790576, 'start_date': "01/01/2014", 'end_date': "01/01/2015"}

        self.query = Marker.bounding_box_query(yield_per=50, **kwargs)
        print self.query

    def tearDown(self):
        self.query = None

    def test_location_filters(self):
        for marker in self.query:
            self.assertTrue(self.query['sw_lat'] <= marker.latitude <= self.query['ne_lat'])
            self.assertTrue(self.query['sw_lng'] <= marker.longitude <= self.query['ne_lng'])

    def test_accuracy_filter(self):
        for marker in self.query:
            self.assertTrue(marker['approx'])

    def test_severity_filters(self):
        for marker in self.query:
            self.assertFalse(marker['fatal'])
            self.assertTrue(marker['severe'])
            self.assertTrue(marker['light'])


if __name__ == '__main__':
    unittest.main()
    suite = unittest.TestLoader().loadTestsFromTestCase(TestQueryFilters)
    unittest.TextTestRunner(verbosity=2).run(suite)
