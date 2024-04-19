import unittest
from unittest.mock import patch
from anyway.widgets.widget_utils import (format_2_level_items, get_filter_expression,
                                         get_expression_for_segment_junctions)
from anyway.backend_constants import AccidentSeverity
from anyway.models import AccidentMarkerView, RoadJunctionKM, RoadSegments
from anyway.widgets.segment_junctions import SegmentJunctions


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

    t = RoadJunctionKM()
    rjks = [
        RoadJunctionKM(road=1, non_urban_intersection=1, km=1.0),
        RoadJunctionKM(road=1, non_urban_intersection=2, km=2.0),
        RoadJunctionKM(road=1, non_urban_intersection=3, km=3.0),
        RoadJunctionKM(road=10, non_urban_intersection=1, km=10.0),
        RoadJunctionKM(road=20, non_urban_intersection=2, km=10.0),
        RoadJunctionKM(road=30, non_urban_intersection=3, km=10.0),
    ]
    segments = [
        RoadSegments(segment_id=1, road=1, from_km=0.0, to_km=1.0),
        RoadSegments(segment_id=2, road=1, from_km=1.0, to_km=2.0),
        RoadSegments(segment_id=3, road=1, from_km=1.0, to_km=3.0),
        RoadSegments(segment_id=4, road=1, from_km=3.0, to_km=4.0),
        RoadSegments(segment_id=11, road=10, from_km=0.0, to_km=10.0),
        RoadSegments(segment_id=12, road=10, from_km=10.0, to_km=20.0),
        RoadSegments(segment_id=21, road=20, from_km=0.0, to_km=10.0),
        RoadSegments(segment_id=22, road=20, from_km=10.0, to_km=20.0),
        RoadSegments(segment_id=31, road=30, from_km=0.0, to_km=10.0),
        RoadSegments(segment_id=32, road=30, from_km=10.0, to_km=20.0),
    ]

    def test_format_two_level_items(self):
        actual = format_2_level_items(
            self.item1,
            level1_vals=None,
            level2_vals=AccidentSeverity
        )
        self.assertEqual(self.items1_res, actual, "leve 2 formatting")

    @patch("anyway.widgets.segment_junctions.db")
    def test_get_segment_junctions(self, db):
        db.session.query.all.side_effect = [self.rjks, self.segments]
        db.session.query.return_value = db.session.query
        sg = SegmentJunctions()
        actual = sg.get_segment_junctions(1)
        self.assertEqual([], actual, "1")
        actual = sg.get_segment_junctions(2)
        self.assertEqual([1], actual, "2")
        actual = sg.get_segment_junctions(3)
        self.assertEqual([1, 2, 3], actual, "3")

    def test_get_filter_expression(self):
        actual = get_filter_expression(AccidentMarkerView, "road_segment_name", "seg1")
        self.assertEqual('markers_hebrew.road_segment_name', str(actual.left), "1")
        self.assertEqual('seg1', actual.right.value, "2")
        actual = get_filter_expression(AccidentMarkerView, "street1_hebrew", ["s1"])
        self.assertEqual(2, len(actual.expression.clauses), "3")
        self.assertEqual('markers_hebrew.street1_hebrew', str(actual.expression.clauses[0].left), "4")
        self.assertEqual('s1', actual.clauses[0].right.element.clauses[0].value, "5")
        self.assertEqual('markers_hebrew.street2_hebrew', str(actual.expression.clauses[1].left), "6")
        self.assertEqual('s1', actual.clauses[1].right.element.clauses[0].value, "7")
        actual = get_filter_expression(AccidentMarkerView, "street1", "1")
        self.assertEqual(2, len(actual.expression.clauses), "8")
        self.assertEqual('markers_hebrew.street1', str(actual.expression.clauses[0].left), "9")
        self.assertEqual('1', actual.clauses[0].right.element.clauses[0].value, "10")
        self.assertEqual('markers_hebrew.street2', str(actual.expression.clauses[1].left), "11")
        self.assertEqual('1', actual.clauses[1].right.element.clauses[0].value, "12")

    @patch("anyway.widgets.widget_utils.SegmentJunctions")
    def test_get_expression_for_segment_junctions(self, sg):
        sg.get_instance.return_value = sg
        sg.get_segment_junctions.return_value = []
        actual = get_expression_for_segment_junctions(17, AccidentMarkerView)
        self.assertEqual('1 != 1', str(actual.expression), "1")


if __name__ == '__main__':
    unittest.main()
