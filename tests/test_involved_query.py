import unittest
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
