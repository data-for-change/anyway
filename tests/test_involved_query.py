import unittest
from anyway.views.safety_data.involved_query import InvolvedQuery
from anyway.views.safety_data.involved_query_gb import InvolvedQuery_GB
from anyway import app as flask_app

class TestInvolvedQuery(unittest.TestCase):
    involved_result = {
        "accident_timestamp": "2019-04-16 01:45",
        "accident_type_hebrew": "פגיעה בהולך רגל",
        "accident_year": 2019,
        "accident_yishuv_name": "תל אביב - יפו",
        "day_in_week_hebrew": "שלישי",
        "day_night_hebrew": "לילה ",
        "location_accuracy_hebrew": "עיגון מדויק",
        "multi_lane_hebrew": "מיפרדה בנויה ללא גדר בטיחות",
        "one_lane_hebrew": "לאידוע",
        "road1": None,
        "road2": None,
        "road_segment_name": None,
        "road_type_hebrew": "עירונית לא בצומת",
        "road_width_hebrew": None,
        "speed_limit_hebrew": 'עד 50 קמ"ש',
        "street2_hebrew": None,
        "vehicles": "אופניים חשמליים",
        "latitude": "32.0559627551410",
        "longitude": "34.7708950471885",
        "_id": 3,
        "age_group_hebrew": "70-74",
        "injured_type_hebrew": "הולך רגל",
        "injured_type_short_hebrew": "הולך רגל",
        "injury_severity_hebrew": "פצוע קשה",
        "population_type_hebrew": "יהודים",
        "vehicle_vehicle_type_hebrew": "הולך רגל",
        "sex_hebrew": "נקבה",
        "TEST-vehicle_type": None,
        "TEST-injured_type": 1,
        "vehicle_type_short_hebrew": None,
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
        self.assertEqual(f((1 << 34) | (1 << 4)), "משאית, קורקינט חשמלי")

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

        actual = test_client.get(
            "/involved?sy=2019&ey=2019&sex=2&age=15&injt=1&sev=1194&st=2215"
        )
        self.assertEqual("200 OK", actual.status, "3")
        self.maxDiff = None
        res = actual.json["data"][0]
        self.assertEqual(2215, res["street1"])
        self.assertIsNone(res["street2"])
        res.pop("street1_hebrew")
        res.pop("street1")
        res.pop("street2")
        self.assertEqual(self.involved_result, res, "4")

        actual = test_client.get("/involved/groupby?sy=2019&ey=2019&gb=year&gb2=lca&city=5000,1&sort=d")
        self.assertEqual("200 OK", actual.status, "5")
        self.assertTrue(len(actual.json) > 0, "9")
        actual = test_client.get("/involved/groupby?sy=2019&ey=2019&city=5000,1&gb=vcl&lim=15&sort=d")
        self.assertEqual("200 OK", actual.status, "7")
        self.assertTrue(len(actual.json) > 0, "9")
        actual = test_client.get("/involved/groupby?sy=2019&ey=2019&city=5000,1&gb=cpop&sort=a")
        self.assertEqual("200 OK", actual.status, "10")
        self.assertTrue(len(actual.json) > 0, "12")
        actual = test_client.get(
            "/involved/groupby?sy=2019&ey=2019&city=5000,1&sev=1&st=1&rd=1" \
            "&rds=1&sex=1&age=1&pt=1&dn=1&mn=1&acc=1&selfacc=1&rt=1&sp=1&rw=1" \
            "&ml=1&ol=1&lca=1" \
            "&gb=cpop&gb2=injt&sort=a&lim=1")
        self.assertEqual("200 OK", actual.status, "13")
        self.assertEqual(0, len(actual.json), "14")


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
