import unittest
from anyway.widgets.widget_utils import format_2_level_items
from anyway.constants.accident_severity import AccidentSeverity


class TestInfographicsUtilsCase(unittest.TestCase):
    item1 = {
        "2019": {
            1: 0,
            2: 3,
            3: 22
        },
        "2020": {
            1: 1,
            2: 1,
            3: 22
        }
    }
    items1_res = [
        {
            "label_key": "2019",
            "series": [
                {"label_key": "fatal", "value": 0},
                {"label_key": "severe", "value": 3},
                {"label_key": "light", "value": 22},
            ]
        },
        {
            "label_key": "2020",
            "series": [
                {"label_key": "fatal", "value": 1},
                {"label_key": "severe", "value": 1},
                {"label_key": "light", "value": 22},
            ]
        }
    ]
    def test_format_two_level_items(self):
        actual = format_2_level_items(
            self.item1,
            level1_vals=None,
            level2_vals=AccidentSeverity
        )
        self.assertEqual(self.items1_res, actual, "leve 2 formatting")


if __name__ == '__main__':
    unittest.main()
