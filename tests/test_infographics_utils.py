import unittest
from unittest.mock import patch
from sqlalchemy import and_
from anyway.widgets.widget_utils import (format_2_level_items,
                                         get_expression_for_segment_junctions,
                                         add_resolution_location_accuracy_filter,
                                         get_expression_for_fields,
                                         get_filter_expression_raw,
                                         get_filter_expression,
                                         get_expression_for_non_road_segment_fields,

                                         )
from anyway.backend_constants import AccidentSeverity
from anyway.models import AccidentMarkerView, RoadJunctionKM, RoadSegments, InvolvedMarkerView
from anyway.widgets.segment_junctions import SegmentJunctions
from anyway.backend_constants import BE_CONST
RC = BE_CONST.ResolutionCategories


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
    # noinspection SpellCheckingInspection
    rjks = [
        RoadJunctionKM(road=1, non_urban_intersection=1, km=1.0),
        RoadJunctionKM(road=1, non_urban_intersection=2, km=2.0),
        RoadJunctionKM(road=1, non_urban_intersection=22, km=2.0),
        RoadJunctionKM(road=1, non_urban_intersection=3, km=3.0),
        RoadJunctionKM(road=10, non_urban_intersection=1, km=10.0),
        RoadJunctionKM(road=20, non_urban_intersection=2, km=10.0),
        RoadJunctionKM(road=20, non_urban_intersection=22, km=10.0),
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
        self.assertEqual([1, 2, 22, 3], actual, "3")
        actual = sg.get_segment_junctions(4)
        self.assertEqual([3], actual, "4")
        actual = sg.get_segment_junctions(21)
        self.assertEqual([2, 22], actual, "5")

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
        self.assertEqual('1', actual.clauses[0].right.effective_value, "10")
        self.assertEqual('markers_hebrew.street2', str(actual.expression.clauses[1].left), "11")
        self.assertEqual('1', actual.clauses[1].right.effective_value, "12")

    @patch("anyway.widgets.widget_utils.SegmentJunctions")
    def test_get_expression_for_segment_junctions(self, sg):
        sg.get_instance.return_value = sg
        sg.get_segment_junctions.return_value = []
        actual = get_expression_for_segment_junctions(17, AccidentMarkerView)
        self.assertEqual('1 != 1', str(actual.expression), "1")

    def test_add_resolution_location_accuracy_filter(self):
        f = {"1": 1}
        actual = add_resolution_location_accuracy_filter(f, RC.STREET)
        self.assertEqual({'1': 1, 'location_accuracy': [1, 3]}, actual, "2")
        actual = add_resolution_location_accuracy_filter(None, RC.STREET)
        self.assertEqual({'location_accuracy': [1, 3]}, actual, "3")
        actual = add_resolution_location_accuracy_filter(f, RC.SUBURBAN_JUNCTION)
        self.assertEqual({'1': 1, 'location_accuracy': [1, 4]}, actual, "4")
        actual = add_resolution_location_accuracy_filter(None, RC.SUBURBAN_ROAD)
        self.assertEqual({'location_accuracy': [1, 4]}, actual, "5"
                         )
        actual = add_resolution_location_accuracy_filter(f, RC.SUBURBAN_JUNCTION)
        self.assertEqual({'1': 1, 'location_accuracy': [1, 4]}, actual, "6",)
        actual = add_resolution_location_accuracy_filter(None, RC.STREET)
        self.assertEqual({'location_accuracy': [1, 3]}, actual, "7")
        actual = add_resolution_location_accuracy_filter(f, RC.OTHER)
        self.assertEqual(f, actual, "8")
        actual = add_resolution_location_accuracy_filter(None, RC.OTHER)
        self.assertIsNone(actual, "9")

    @patch("anyway.widgets.widget_utils.and_")
    @patch("anyway.widgets.widget_utils.split_location_fields_and_others")
    @patch("anyway.widgets.widget_utils.get_expression_for_road_segment_location_fields")
    @patch("anyway.widgets.widget_utils.get_expression_for_non_road_segment_fields")
    def test_get_expression_for_fields(self, non_segment_ex, segment_ex, split, sql_and):
        sql_and_return_val = "sql_and_return_val"
        sql_and.return_value = sql_and_return_val
        non_segment_ex_return_val = "non_segment_ex_return_val"
        segment_ex_return_val = "segment_ex_return_val"
        segment_ex.return_value = segment_ex_return_val
        f = {"road1": 1}
        o = {"location_accuracy": 1}
        non_segment_ex.return_value = non_segment_ex_return_val
        actual = get_expression_for_fields(f, InvolvedMarkerView)
        non_segment_ex.assert_called_with(f, InvolvedMarkerView, sql_and)
        self.assertEqual(non_segment_ex_return_val, actual, "1")

        non_segment_ex.reset_mock()
        f = {"road_segment_id": 1}
        split.return_value = (f, {})
        actual = get_expression_for_fields(f, InvolvedMarkerView)
        self.assertEqual(segment_ex_return_val, actual, "2")
        non_segment_ex.assert_not_called()
        segment_ex.assert_called_with(f, InvolvedMarkerView)

        non_segment_ex.reset_mock()
        segment_ex.reset_mock()
        f = {"road_segment_id": 1}
        split.return_value = (f, o)
        actual = get_expression_for_fields(f, InvolvedMarkerView)
        self.assertEqual(sql_and_return_val, actual, "3")
        non_segment_ex.assert_called_with(o, InvolvedMarkerView, sql_and)
        segment_ex.assert_called_with(f, InvolvedMarkerView)
        sql_and.assert_called_with(segment_ex_return_val, non_segment_ex_return_val)

    @patch("anyway.widgets.widget_utils.or_")
    def test_get_filter_expression_1(self, sql_or):
        sql_or_return_val = "sql_or_return_val"
        sql_or.return_value = sql_or_return_val
        actual = get_filter_expression(InvolvedMarkerView, "street1_hebrew", "name")
        self.assertEqual(sql_or_return_val, actual, "1")
        for i in [0, 1]:
            arg = str(sql_or.call_args.args[i])
            self.assertTrue(arg.startswith(f'involved_markers_hebrew.street{i+1}_hebrew ='), f"2.{i}")

    def test_get_filter_expression_raw(self):
        actual = get_filter_expression_raw(InvolvedMarkerView, "location_accuracy", "1")
        self.assertIn("involved_markers_hebrew.location_accuracy =",
                      str(actual), "1")

        actual = get_filter_expression_raw(InvolvedMarkerView, "location_accuracy", [1, 3])
        self.assertIn("involved_markers_hebrew.location_accuracy IN",
                      str(actual), "2")

    def test_get_expression_for_non_road_segment_fields(self):
        actual = get_expression_for_non_road_segment_fields({"location_accuracy": "1"},
                                                            InvolvedMarkerView,
                                                            and_)
        self.assertIn("involved_markers_hebrew.location_accuracy =",
                      str(actual), "1")
        actual = get_expression_for_non_road_segment_fields({"location_accuracy": "1",
                                                             "road1": 1},
                                                            InvolvedMarkerView,
                                                            and_)
        self.assertIn("involved_markers_hebrew.location_accuracy =",
                      str(actual), "2")
        self.assertIn("involved_markers_hebrew.road1 =",
                      str(actual), "3")
        self.assertIn(" AND ",
                      str(actual), "4")


if __name__ == '__main__':
    unittest.main()
