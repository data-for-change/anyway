import unittest
from unittest.mock import patch, Mock
import json
from anyway.parsers.cities import UpdateCitiesFromDataGov

class TestUpdateCitiesFromDataGov(unittest.TestCase):
    # ...existing code...

    @patch('anyway.parsers.cities.requests.Session.get')
    def test_add_osm_data(self, mock_get):
        mock_response = Mock()
        mock_response.ok = True
        mock_response.text = json.dumps({
            "elements": [
                {"tags": {"name:he": "name:he", "name:he2": "xx"}, "id": 1, "lat": 32.0853, "lon": 34.7818},
                {"tags": {"name:he": "xx", "name:he2": "name:he2"}, "id": 2, "lat": 32.0853, "lon": 34.7818},
                {"tags": {"name:en": "name:en", "name:en7": "xx"}, "id": 3, "lat": 31.7683, "lon": 35.2137},
                {"tags": {"name:en": "xx", "name:en7": "name:en7"}, "id": 4, "lat": 31.7683, "lon": 35.2137},
            ]
        })
        mock_get.return_value = mock_response

        heb_name_dict = {
            "name:he": {"heb_name": "name:he", "eng_name": "yy"},
            "name:he2": {"heb_name": "name:he2", "eng_name": "yy"},
            "other": {"heb_name": "name:he2", "eng_name": "yy"},
        }
        eng_name_dict = {
            "name:en": {"heb_name": "yy", "eng_name": "name:en"},
            "name:en7": {"heb_name": "yy", "eng_name": "name:en7"},
            "other": heb_name_dict["other"],
        }

        updater = UpdateCitiesFromDataGov()
        updater.add_osm_data(heb_name_dict, eng_name_dict)

        self.assertEqual(heb_name_dict["name:he"]["id_osm"], 1, "1")
        self.assertEqual(heb_name_dict["name:he"]["lat"], 32.0853, "2")
        self.assertEqual(heb_name_dict["name:he"]["lon"], 34.7818, "3")
        self.assertEqual(heb_name_dict["name:he2"]["id_osm"], 2, "4")
        self.assertEqual(eng_name_dict["name:en"]["id_osm"], 3, "5")
        self.assertEqual(eng_name_dict["name:en7"]["id_osm"], 4, "6")
        self.assertNotIn("id_osm", heb_name_dict["other"], "7")
        self.assertNotIn("id_osm", eng_name_dict["other"], "8")

if __name__ == '__main__':
    unittest.main()
