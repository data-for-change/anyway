import unittest
from anyway.views.safety_data.involved_query import InvolvedQuery
from anyway.views.safety_data.involved_query_gb import InvolvedQuery_GB
from anyway import app as flask_app

class TestInvolvedQuery(unittest.TestCase):
    involved_result = {
         'accident_timestamp': '2014-03-23 00:00',
         'accident_type_hebrew': 'פגיעה בהולך רגל', 'accident_year': 2014,
         'accident_yishuv_name': 'תל אביב - יפו', 'day_in_week_hebrew': 'ראשון',
         'day_night_hebrew': 'לילה', 'location_accuracy_hebrew': 'עיגון מדויק',
         'multi_lane_hebrew': None, 'one_lane_hebrew': 'חד סיטרי', 'road1': None,
         'road2': None, 'road_segment_name': None,
         'road_type_hebrew': 'עירונית לא בצומת', 'road_width_hebrew': 'עד 5 מטר',
         'speed_limit_hebrew': 'עד 50 קמ"ש',
         'street2_hebrew': None, 'vehicles': 'רכב נוסעים פרטי',
         'latitude': '32.0701379776572', 'longitude': '34.7978130577587',
         '_id': 24, 'age_group_hebrew': '70-74',
         'injured_type_hebrew': 'הולך רגל', 'injured_type_short_hebrew': 'הולך רגל',
         'injury_severity_hebrew': 'פצוע קשה', 'population_type_hebrew': 'יהודים',
         'vehicle_vehicle_type_hebrew': 'הולך רגל', 'sex_hebrew': 'נקבה',
         'TEST-vehicle_type': None, 'TEST-injured_type': 1,
         'vehicle_type_short_hebrew': None
         }

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

    def test_e2e(self):
        test_client = flask_app.test_client()

        actual = test_client.get("/involved?sy=2014&ey=2014&sex=2&age=15&injt=1"
                                    "&sev=2&st=2551")
        self.assertEqual("200 OK", actual.status, "3")
        self.maxDiff = None
        res = actual.json["data"][0]
        res.pop("street1_hebrew")
        self.assertEqual(self.involved_result, res, "4")

        expected = [{'_id': 2014,
                    'count': [{'grp2': 'מרכז דרך', 'count': 691},
                                {'grp2': 'מרכז ישוב', 'count': 55},
                                {'grp2': 'עיגון מדויק', 'count': 1844}
                                ]
                    }
        ]
        actual = test_client.get("/involved/groupby?sy=2014&ey=2014&gb=year&gb2=lca&city=5000,1")
        self.assertEqual("200 OK", actual.status, "5")
        self.assertEqual(expected, actual.json, "6")


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
