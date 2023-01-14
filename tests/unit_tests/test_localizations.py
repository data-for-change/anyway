import unittest

from anyway.localization import get_city_name

RAMAT_GAN_CITY_CODE = 8600


class LocalizationsTest(unittest.TestCase):
    def test_hebrew(self):
        self.assertEqual(get_city_name(RAMAT_GAN_CITY_CODE, "he"), "רמת גן")

    def test_english(self):
        self.assertEqual(get_city_name(RAMAT_GAN_CITY_CODE, "en"), "RAMAT GAN")

    def test_not_found(self):
        self.assertIsNone(get_city_name("NOT_AN_ACTUAL_CODE", "en"))
