import unittest
import requests
import json
from anyway.views.safety_data.involved_query import InvolvedQuery
from anyway.views.safety_data.involved_query_gb import InvolvedQuery_GB

class TestInvolvedQuery(unittest.TestCase):
    def test_vehicle_type_bit_2_heb(self):
        f = InvolvedQuery.vehicle_type_bit_2_heb
        self.assertEqual(f(1 << 1), "רכב נוסעים פרטי")
        self.assertEqual(f(0), "")
        self.assertEqual(f(1 << 3), "טנדר")
        self.assertEqual(f(1 << 20), "")
        self.assertEqual(f(1 << 17), "אחר ולא ידוע")
        self.assertEqual(f(1 << 0), "")
        self.assertEqual(f(1 << 26), "")
        self.assertEqual(f((1 << 1) | (1 << 2)), "רכב נוסעים פרטי, טרנזיט")
        self.assertEqual(f((1 << 21) | (1 << 25)), "קורקינט חשמלי, משאית")

    def test_dictify_double_group_by(self):
        data = [
            ("2021", "Male", 10),
            ("2021", "Female", 5),
            ("2022", "Male", 7),
            ("2022", "Female", 3),
        ]
        expected = [
            {"_id": "2021", "count": [{"grp2": "Male", "count": 10}, {"grp2": "Female", "count": 5}]},
            {"_id": "2022", "count": [{"grp2": "Male", "count": 7}, {"grp2": "Female", "count": 3}]},
        ]
        actual = InvolvedQuery_GB.dictify_double_group_by(data)
        self.assertEqual(actual, expected)

    def test_compare_to_heroku(self):
        heroku_url = "https://safety-data.herokuapp.com/api/v1/accident"
        local_url = "http://127.0.0.1:5000/involved"
        params_list = [
            {"sy": 2020, "ey": 2020, "sev": 1, "rd": 1, "rt": 4, "sex": 1, "injt": 1, "rw": 5, "age": 5, "acc": 3},
            {"sy": 2021, "ey": 2024, "rt": 4, "sex": 1, "injt": 1, "rw": 5, "age": 5, "acc": 3},
            {"sy": 2022, "ey": 2022, "sev": 1, "rd": 1, "rt": 4, "rw": 5, "age": 5, "acc": 3},
        ]
        failed = False
        for params in params_list:
            print(params)
            response = requests.get(heroku_url, params=params)
            her = json.loads(response.text)
            response = requests.get(local_url, params=params)
            loc = json.loads(response.text)
            self.assertEqual(len(her), len(loc), f"1:params: {params}")
            if len(her) > 0:
                hk = [x for x in her[0].keys() if x not in ('_id', 'vehicles', 'vehicle_vehicle_type_hebrew')]
                res = compare_dir_lists(loc, her, hk)
                if res:
                    print(res)
                    failed = True
        self.assertFalse(failed, "2")


def compare_dir_lists(l1, l2, keys):
    res = {}
    l1k = {x["accident_timestamp"]: x for x in l1}
    for d2 in l2:
        d1 = l1k[d2["accident_timestamp"]]
        eres = []
        for k in keys:
            if d1[k] != d2[k] and (d1[k] or d2[k]):
                eres.append(( k, d1[k], d2[k]))
        if len(eres) > 0:
            res[d2["accident_timestamp"]] = eres
    return res

if __name__ == '__main__':
    unittest.main()
