import pytest
from anyway.models import Marker  # for Marker.bounding_box_query
import datetime

# This tests year 2014 accidents as this is the current example git data for testing
# Once this changes to another year or to the current year's accidents (as should be) un-comment lines 11,13,15
# and change both 2014 and 2015 to: %s


@pytest.fixture
def base_kwargs():
    return {'approx': True, 'show_day': 7, 'show_discussions': True, 'accurate': True, 'surface': 0,
            'weather': 0, 'district': 0, 'show_markers': True, 'show_fatal': True, 'show_time': 24,
            'show_intersection': 3, 'show_light': True, 'sw_lat': 32.067363446951944, 'controlmeasure': 0,
            'start_date': datetime.date(2014, 1, 1), 'ne_lng': 34.79928962966915, 'show_severe': True,
            'end_date': datetime.date(2016, 1, 1), 'start_time': 25, 'acctype': 0, 'separation': 0,
            'show_urban': 3, 'show_lane': 3, 'sw_lng': 34.78877537033077, 'zoom': 17, 'show_holiday': 0,
            'end_time': 25, 'road': 0, 'ne_lat': 32.072427482938345}


def test_location_filters(base_kwargs):
    query = Marker.bounding_box_query(yield_per=50, **base_kwargs)[0]
    for marker in query:
        assert base_kwargs['sw_lat'] <= marker.latitude  <= base_kwargs['ne_lat']
        assert base_kwargs['sw_lng'] <= marker.longitude <= base_kwargs['ne_lng']


def test_accurate_filter(base_kwargs):
    base_kwargs['approx'] = False
    markers = Marker.bounding_box_query(yield_per=50, **base_kwargs)[0]
    for marker in markers:
        assert marker.locationAccuracy == 1


def test_approx_filter(base_kwargs):
    base_kwargs['accurate'] = False
    markers = Marker.bounding_box_query(yield_per=50, **base_kwargs)[0]
    for marker in markers:
        assert marker.locationAccuracy != 1


def test_fatal_severity_filter(base_kwargs):
    base_kwargs['show_fatal'] = False
    markers = Marker.bounding_box_query(yield_per=50, **base_kwargs)[0]
    for marker in markers:
        assert marker.severity != 1


def test_severe_severity_filter(base_kwargs):
    base_kwargs['show_severe'] = False
    markers = Marker.bounding_box_query(yield_per=50, **base_kwargs)[0]
    for marker in markers:
        assert marker.severity != 2


def test_light_severity_filter(base_kwargs):
    base_kwargs['show_light'] = False
    markers = Marker.bounding_box_query(yield_per=50, **base_kwargs)[0]
    for marker in markers:
        assert marker.severity != 3
