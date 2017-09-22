# -*- coding: utf-8 -*-
from anyway import app as flask_app
import json
import pytest
from functools import partial
from urlobject import URLObject
from collections import Counter

@pytest.fixture
def app():
    return flask_app.test_client()


query_flag = partial(pytest.mark.parametrize, argvalues=["1", ""])


def test_main(app):
    rv = app.get('/')
    assert rv.status == '200 OK'
    assert '<title>ANYWAY - משפיעים בכל דרך</title>' in rv.data

    #rv = app.post('/new-features')
    #assert rv.status == '200 OK'
    #print(rv.data)


#It requires parameters to know which markers you want.
def test_markers_empty(app):
    rv = app.get('/markers')
    assert rv.status == '400 BAD REQUEST'
    assert '<title>400 Bad Request</title>' in rv.data
    #print(rv.data)


@pytest.fixture(scope="module")
def marker_counter():
    counter = Counter()
    yield counter
    assert counter['markers'] == 1688


def test_bad_date(app):
    rv = app.get("/markers?ne_lat=32.08656790211843&ne_lng=34.80611543655391&sw_lat=32.08003198103277&sw_lng=34.793884563446&zoom=17&thin_markers=false&start_date=a1104537600&end_date=1484697600&show_fatal=1&show_severe=1&show_light=1&approx=1&accurate=1&show_markers=1&show_discussions=1&show_urban=3&show_intersection=3&show_lane=3&show_day=7&show_holiday=0&show_time=24&start_time=25&end_time=25&weather=0&road=0&separation=0&surface=0&acctype=0&controlmeasure=0&district=0&case_type=0")
    assert rv.status == '400 BAD REQUEST'
    assert rv.headers['Content-Type'] == 'text/html'


def test_markers_2014086707(app):
    # clicking on a car image
    rv = app.get("/markers/2014086707")
    assert rv.status == '200 OK'
    #print(rv.data)
    with open('tests/markers_2014086707.json') as fh:
        assert json.loads(rv.data) == json.load(fh)


@query_flag("show_fatal")
@query_flag("show_severe")
@query_flag("show_light")
@query_flag("show_approx")
@query_flag("show_accurate")
def test_markers(app, show_fatal, show_severe, show_light, show_accurate, show_approx, marker_counter):
    url = URLObject('/markers').set_query_params({
        "ne_lat": "32.085413468822", "ne_lng": "34.797736215591385", "sw_lat": "32.07001357040486", "sw_lng": "34.775548982620194", "zoom": "16", "thin_markers": "false",
        "start_date": "1104537600", "end_date": "1484697600", "show_fatal": show_fatal, "show_severe": show_severe, "show_light": show_light, "approx": show_approx, "accurate": show_accurate, "show_markers": "1",
        "show_discussions": "1", "show_urban": "3", "show_intersection": "3", "show_lane": "3", "show_day": "7", "show_holiday": "0", "show_time": "24", "start_time": "25",
        "end_time": "25", "weather": "0", "road": "0", "separation": "0", "surface": "0", "acctype": "0", "controlmeasure": "0", "district": "0", "case_type": "0"})

    rv = app.get(url)
    assert rv.status == '200 OK'
    assert rv.headers['Content-Type'] == 'application/json'

    resp = json.loads(rv.data)

    marker_counter["markers"] += len(resp['markers'])

    for marker in resp['markers']:
        assert show_fatal or marker['severity'] != 1
        assert show_severe or marker['severity'] != 2
        assert show_light or marker['severity'] != 3
        assert show_accurate or marker['locationAccuracy'] != 1
        assert show_approx or marker['locationAccuracy'] == 1


def test_clusters(app):
    rv = app.get("/clusters?ne_lat=34.430273343405844&ne_lng=44.643749999999955&sw_lat=28.84061194106889&sw_lng=22.385449218749955&zoom=6&thin_markers=true&start_date=1104537600&end_date=1486944000&show_fatal=1&show_severe=1&show_light=1&approx=1&accurate=1&show_markers=1&show_discussions=1&show_urban=3&show_intersection=3&show_lane=3&show_day=7&show_holiday=0&show_time=24&start_time=25&end_time=25&weather=0&road=0&separation=0&surface=0&acctype=0&controlmeasure=0&district=0&case_type=0")
    assert rv.status == '200 OK'
    #print(rv.data)
    resp = json.loads(rv.data)
    assert 'clusters' in resp
    assert resp['clusters']
    for cluster in resp['clusters']:
        for attr in ['longitude', 'latitude', 'size']:
            assert attr in cluster


def test_single_marker(app):
    rv = app.get("/markers/2014027147")
    assert rv.status == '200 OK'
    #print(rv.data)
    resp = json.loads(rv.data)
    #assert 'clusters' in resp
    assert resp[0]['accident_id'] == 2014027147
