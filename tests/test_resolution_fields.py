import unittest
from anyway.parsers.resolution_fields import ResolutionFields as RF
from anyway.backend_constants import BE_CONST


class ResolutionFieldsTestCase(unittest.TestCase):
    def test_get_supported_resolution_of_fields(self):
        actual = RF.get_supported_resolution_of_fields(["road1", "road_segment_id"])
        self.assertEqual(BE_CONST.ResolutionCategories.SUBURBAN_ROAD, actual[0], "1")

    def test_get_all_location_fields(self):
        actual = RF.get_all_location_fields()
        self.assertGreater(len(actual), 5, "1")

if __name__ == '__main__':
    unittest.main()
