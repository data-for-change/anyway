import unittest
from anyway.views.safety_data.involved_query import InvolvedQuery

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

if __name__ == '__main__':
    unittest.main()
