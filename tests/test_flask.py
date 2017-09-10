# -*- coding: utf-8 -*-
from anyway import app as flask_app
import json
import pytest

@pytest.fixture
def app():
    return flask_app.test_client()


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


# this was the request I saw when I loaded the main page
def test_markers(app):
    rv = app.get("/markers?ne_lat=32.08656790211843&ne_lng=34.80611543655391&sw_lat=32.08003198103277&sw_lng=34.793884563446&zoom=17&thin_markers=false&start_date=1104537600&end_date=1484697600&show_fatal=1&show_severe=1&show_light=1&approx=1&accurate=1&show_markers=1&show_discussions=1&show_urban=3&show_intersection=3&show_lane=3&show_day=7&show_holiday=0&show_time=24&start_time=25&end_time=25&weather=0&road=0&separation=0&surface=0&acctype=0&controlmeasure=0&district=0&case_type=0")
    assert rv.status == '200 OK'
    assert rv.headers['Content-Type'] == 'application/json'
    #print(rv.data)
    resp = json.loads(rv.data)
    assert 'markers' in resp
    assert len(resp['markers']) == 41
    #print(len(resp['markers']))


def test_markers_2014086707(app):
    # clicking on a car image
    rv = app.get("/markers/2014086707")
    assert rv.status == '200 OK'
    #print(rv.data)
    with open('tests/markers_2014086707.json') as fh:
        assert json.loads(rv.data) == json.load(fh)


def test_markers_fatal_only(app):
    rv = app.get("/markers?ne_lat=32.082754580757744&ne_lng=34.79886274337764&sw_lat=32.072645555012734&sw_lng=34.77712612152095&zoom=16&thin_markers=false&start_date=1104537600&end_date=1485129600&show_fatal=1&show_severe=&show_light=&approx=1&accurate=1&show_markers=1&show_discussions=1&show_urban=3&show_intersection=3&show_lane=3&show_day=7&show_holiday=0&show_time=24&start_time=25&end_time=25&weather=0&road=0&separation=0&surface=0&acctype=0&controlmeasure=0&district=0&case_type=0")
    assert rv.status == '200 OK'
    #print(rv.data)
    resp = json.loads(rv.data)
    assert 'markers' in resp
    assert len(resp['markers']) == 1


def test_markers_fatal_only_response(app):
    rv = app.get("/markers?ne_lat=32.082754580757744&ne_lng=34.79886274337764&sw_lat=32.072645555012734&sw_lng=34.77712612152095&zoom=16&thin_markers=false&start_date=1104537600&end_date=1485129600&show_fatal=1&show_severe=&show_light=&approx=1&accurate=1&show_markers=1&show_discussions=1&show_urban=3&show_intersection=3&show_lane=3&show_day=7&show_holiday=0&show_time=24&start_time=25&end_time=25&weather=0&road=0&separation=0&surface=0&acctype=0&controlmeasure=0&district=0&case_type=0")
    assert rv.status == '200 OK'
    #print(rv.data)
    resp = json.loads(rv.data)
    assert 'markers' in resp
    #assert len(resp['markers']) == 16
    for i in range(0,len(resp['markers'])):
        assert resp['markers'][i]['severity'] == 1


def test_markers_severe_only(app):
    rv = app.get("/markers?ne_lat=32.082754580757744&ne_lng=34.79886274337764&sw_lat=32.072645555012734&sw_lng=34.77712612152095&zoom=16&thin_markers=false&start_date=1104537600&end_date=1485129600&show_fatal=&show_severe=1&show_light=&approx=1&accurate=1&show_markers=1&show_discussions=1&show_urban=3&show_intersection=3&show_lane=3&show_day=7&show_holiday=0&show_time=24&start_time=25&end_time=25&weather=0&road=0&separation=0&surface=0&acctype=0&controlmeasure=0&district=0&case_type=0")
    assert rv.status == '200 OK'
    #print(rv.data)
    resp = json.loads(rv.data)
    assert 'markers' in resp
    assert len(resp['markers']) == 16


def test_markers_severve_only_response(app):
    rv = app.get("/markers?ne_lat=32.082754580757744&ne_lng=34.79886274337764&sw_lat=32.072645555012734&sw_lng=34.77712612152095&zoom=16&thin_markers=false&start_date=1104537600&end_date=1485129600&show_fatal=&show_severe=1&show_light=&approx=1&accurate=1&show_markers=1&show_discussions=1&show_urban=3&show_intersection=3&show_lane=3&show_day=7&show_holiday=0&show_time=24&start_time=25&end_time=25&weather=0&road=0&separation=0&surface=0&acctype=0&controlmeasure=0&district=0&case_type=0")
    assert rv.status == '200 OK'
    #print(rv.data)
    resp = json.loads(rv.data)
    assert 'markers' in resp
    #assert len(resp['markers']) == 16
    for i in range(0,len(resp['markers'])):
        assert resp['markers'][i]['severity'] == 2


def test_markers_light_only(app):
    rv = app.get("/markers?ne_lat=32.082754580757744&ne_lng=34.79886274337764&sw_lat=32.072645555012734&sw_lng=34.77712612152095&zoom=16&thin_markers=false&start_date=1104537600&end_date=1485129600&show_fatal=&show_severe=&show_light=1&approx=1&accurate=1&show_markers=1&show_discussions=1&show_urban=3&show_intersection=3&show_lane=3&show_day=7&show_holiday=0&show_time=24&start_time=25&end_time=25&weather=0&road=0&separation=0&surface=0&acctype=0&controlmeasure=0&district=0&case_type=0")
    assert rv.status == '200 OK'
    #print(rv.data)
    resp = json.loads(rv.data)
    assert 'markers' in resp
    assert len(resp['markers']) == 110


def test_markers_light_only_response(app):
    rv = app.get("/markers?ne_lat=32.082754580757744&ne_lng=34.79886274337764&sw_lat=32.072645555012734&sw_lng=34.77712612152095&zoom=16&thin_markers=false&start_date=1104537600&end_date=1485129600&show_fatal=&show_severe=&show_light=1&approx=1&accurate=1&show_markers=1&show_discussions=1&show_urban=3&show_intersection=3&show_lane=3&show_day=7&show_holiday=0&show_time=24&start_time=25&end_time=25&weather=0&road=0&separation=0&surface=0&acctype=0&controlmeasure=0&district=0&case_type=0")
    assert rv.status == '200 OK'
    #print(rv.data)
    resp = json.loads(rv.data)
    assert 'markers' in resp
    #assert len(resp['markers']) == 16
    for i in range(0,len(resp['markers'])):
        assert resp['markers'][i]['severity'] == 3


def test_markers_accurate_only(app):
    rv = app.get("/markers?ne_lat=32.082754580757744&ne_lng=34.79886274337764&sw_lat=32.072645555012734&sw_lng=34.77712612152095&zoom=16&thin_markers=false&start_date=1104537600&end_date=1485129600&show_fatal=1&show_severe=1&show_light=1&approx=&accurate=1&show_markers=1&show_discussions=1&show_urban=3&show_intersection=3&show_lane=3&show_day=7&show_holiday=0&show_time=24&start_time=25&end_time=25&weather=0&road=0&separation=0&surface=0&acctype=0&controlmeasure=0&district=0&case_type=0")
    assert rv.status == '200 OK'
    #print(rv.data)
    resp = json.loads(rv.data)
    assert 'markers' in resp
    #assert len(resp['markers']) == 16
    for i in range(0,len(resp['markers'])):
        assert resp['markers'][i]['locationAccuracy'] == 1


def test_markers_approx_only(app):
    rv = app.get("/markers?ne_lat=32.082754580757744&ne_lng=34.79886274337764&sw_lat=32.072645555012734&sw_lng=34.77712612152095&zoom=16&thin_markers=false&start_date=1104537600&end_date=1485129600&show_fatal=1&show_severe=1&show_light=1&approx=1&accurate=&show_markers=1&show_discussions=1&show_urban=3&show_intersection=3&show_lane=3&show_day=7&show_holiday=0&show_time=24&start_time=25&end_time=25&weather=0&road=0&separation=0&surface=0&acctype=0&controlmeasure=0&district=0&case_type=0")
    assert rv.status == '200 OK'
    #print(rv.data)
    resp = json.loads(rv.data)
    assert 'markers' in resp
    #assert len(resp['markers']) == 16
    for i in range(0,len(resp['markers'])):
        assert resp['markers'][i]['locationAccuracy'] in (2,3)


def test_clusters(app):
    rv = app.get("/clusters?ne_lat=34.430273343405844&ne_lng=44.643749999999955&sw_lat=28.84061194106889&sw_lng=22.385449218749955&zoom=6&thin_markers=true&start_date=1104537600&end_date=1486944000&show_fatal=1&show_severe=1&show_light=1&approx=1&accurate=1&show_markers=1&show_discussions=1&show_urban=3&show_intersection=3&show_lane=3&show_day=7&show_holiday=0&show_time=24&start_time=25&end_time=25&weather=0&road=0&separation=0&surface=0&acctype=0&controlmeasure=0&district=0&case_type=0")
    assert rv.status == '200 OK'
    #print(rv.data)
    resp = json.loads(rv.data)
    assert 'clusters' in resp
    assert resp['clusters']


def test_single_marker(app):
    rv = app.get("/markers/2014027147")
    assert rv.status == '200 OK'
    #print(rv.data)
    resp = json.loads(rv.data)
    #assert 'clusters' in resp
    assert resp[0]['accident_id'] == 2014027147
