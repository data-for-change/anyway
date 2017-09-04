# -*- coding: utf-8 -*-
import unittest
import main
import json

class TestSite(unittest.TestCase):
    def setUp(self):
        self.app = main.app.test_client()

    def test_main(self):
        rv = self.app.get('/')
        self.assertEqual(rv.status, '200 OK')
        self.assertIn('<title>ANYWAY - משפיעים בכל דרך</title>', rv.data)

        #rv = self.app.post('/new-features')
        #assert rv.status == '200 OK'
        #print(rv.data)

    #It requires parameters to know which markers you want.
    def test_markers_empty(self):
        rv = self.app.get('/markers')
        self.assertEqual(rv.status, '400 BAD REQUEST')
        self.assertIn('<title>400 Bad Request</title>', rv.data)
        #print(rv.data)

    # this was the request I saw when I loaded the main page
    def test_markers(self):
        rv = self.app.get("/markers?ne_lat=32.08656790211843&ne_lng=34.80611543655391&sw_lat=32.08003198103277&sw_lng=34.793884563446&zoom=17&thin_markers=false&start_date=1104537600&end_date=1484697600&show_fatal=1&show_severe=1&show_light=1&approx=1&accurate=1&show_markers=1&show_discussions=1&show_urban=3&show_intersection=3&show_lane=3&show_day=7&show_holiday=0&show_time=24&start_time=25&end_time=25&weather=0&road=0&separation=0&surface=0&acctype=0&controlmeasure=0&district=0&case_type=0")
        self.assertEqual(rv.status, '200 OK')
        self.assertEqual(rv.headers['Content-Type'], 'application/json')
        #print(rv.data)
        resp = json.loads(rv.data)
        self.assertIn('markers', resp)
        self.assertEqual(len(resp['markers']), 41)
        #print(len(resp['markers']))

    def test_markers_2014086707(self):
        # clicking on a car image
        rv = self.app.get("/markers/2014086707")
        self.assertEqual(rv.status, '200 OK')
        #print(rv.data)
        with open('tests/markers_2014086707.json') as fh:
            self.assertEqual(json.loads(rv.data), json.load(fh))

    def test_markers_fatal_only(self):
        rv = self.app.get("/markers?ne_lat=32.082754580757744&ne_lng=34.79886274337764&sw_lat=32.072645555012734&sw_lng=34.77712612152095&zoom=16&thin_markers=false&start_date=1104537600&end_date=1485129600&show_fatal=1&show_severe=&show_light=&approx=1&accurate=1&show_markers=1&show_discussions=1&show_urban=3&show_intersection=3&show_lane=3&show_day=7&show_holiday=0&show_time=24&start_time=25&end_time=25&weather=0&road=0&separation=0&surface=0&acctype=0&controlmeasure=0&district=0&case_type=0")
        self.assertEqual(rv.status, '200 OK')
        #print(rv.data)
        resp = json.loads(rv.data)
        self.assertIn('markers', resp)
        self.assertEqual(len(resp['markers']), 1)

    def test_markers_fatal_only_response(self):
        rv = self.app.get("/markers?ne_lat=32.082754580757744&ne_lng=34.79886274337764&sw_lat=32.072645555012734&sw_lng=34.77712612152095&zoom=16&thin_markers=false&start_date=1104537600&end_date=1485129600&show_fatal=1&show_severe=&show_light=&approx=1&accurate=1&show_markers=1&show_discussions=1&show_urban=3&show_intersection=3&show_lane=3&show_day=7&show_holiday=0&show_time=24&start_time=25&end_time=25&weather=0&road=0&separation=0&surface=0&acctype=0&controlmeasure=0&district=0&case_type=0")
        self.assertEqual(rv.status, '200 OK')
        #print(rv.data)
        resp = json.loads(rv.data)
        self.assertIn('markers', resp)
        #self.assertEqual(len(resp['markers']), 16)
        for i in range(0,len(resp['markers'])):
          self.assertEqual(resp['markers'][i]['severity'], 1)

    def test_markers_severe_only(self):
        rv = self.app.get("/markers?ne_lat=32.082754580757744&ne_lng=34.79886274337764&sw_lat=32.072645555012734&sw_lng=34.77712612152095&zoom=16&thin_markers=false&start_date=1104537600&end_date=1485129600&show_fatal=&show_severe=1&show_light=&approx=1&accurate=1&show_markers=1&show_discussions=1&show_urban=3&show_intersection=3&show_lane=3&show_day=7&show_holiday=0&show_time=24&start_time=25&end_time=25&weather=0&road=0&separation=0&surface=0&acctype=0&controlmeasure=0&district=0&case_type=0")
        self.assertEqual(rv.status, '200 OK')
        #print(rv.data)
        resp = json.loads(rv.data)
        self.assertIn('markers', resp)
        self.assertEqual(len(resp['markers']), 16)

    def test_markers_severve_only_response(self):
        rv = self.app.get("/markers?ne_lat=32.082754580757744&ne_lng=34.79886274337764&sw_lat=32.072645555012734&sw_lng=34.77712612152095&zoom=16&thin_markers=false&start_date=1104537600&end_date=1485129600&show_fatal=&show_severe=1&show_light=&approx=1&accurate=1&show_markers=1&show_discussions=1&show_urban=3&show_intersection=3&show_lane=3&show_day=7&show_holiday=0&show_time=24&start_time=25&end_time=25&weather=0&road=0&separation=0&surface=0&acctype=0&controlmeasure=0&district=0&case_type=0")
        self.assertEqual(rv.status, '200 OK')
        #print(rv.data)
        resp = json.loads(rv.data)
        self.assertIn('markers', resp)
        #self.assertEqual(len(resp['markers']), 16)
        for i in range(0,len(resp['markers'])):
          self.assertEqual(resp['markers'][i]['severity'], 2)

    def test_markers_light_only(self):
        rv = self.app.get("/markers?ne_lat=32.082754580757744&ne_lng=34.79886274337764&sw_lat=32.072645555012734&sw_lng=34.77712612152095&zoom=16&thin_markers=false&start_date=1104537600&end_date=1485129600&show_fatal=&show_severe=&show_light=1&approx=1&accurate=1&show_markers=1&show_discussions=1&show_urban=3&show_intersection=3&show_lane=3&show_day=7&show_holiday=0&show_time=24&start_time=25&end_time=25&weather=0&road=0&separation=0&surface=0&acctype=0&controlmeasure=0&district=0&case_type=0")
        self.assertEqual(rv.status, '200 OK')
        #print(rv.data)
        resp = json.loads(rv.data)
        self.assertIn('markers', resp)
        self.assertEqual(len(resp['markers']), 110)

    def test_markers_light_only_response(self):
        rv = self.app.get("/markers?ne_lat=32.082754580757744&ne_lng=34.79886274337764&sw_lat=32.072645555012734&sw_lng=34.77712612152095&zoom=16&thin_markers=false&start_date=1104537600&end_date=1485129600&show_fatal=&show_severe=&show_light=1&approx=1&accurate=1&show_markers=1&show_discussions=1&show_urban=3&show_intersection=3&show_lane=3&show_day=7&show_holiday=0&show_time=24&start_time=25&end_time=25&weather=0&road=0&separation=0&surface=0&acctype=0&controlmeasure=0&district=0&case_type=0")
        self.assertEqual(rv.status, '200 OK')
        #print(rv.data)
        resp = json.loads(rv.data)
        self.assertIn('markers', resp)
        #self.assertEqual(len(resp['markers']), 16)
        for i in range(0,len(resp['markers'])):
          self.assertEqual(resp['markers'][i]['severity'], 3)

    def test_markers_accurate_only(self):
        rv = self.app.get("/markers?ne_lat=32.082754580757744&ne_lng=34.79886274337764&sw_lat=32.072645555012734&sw_lng=34.77712612152095&zoom=16&thin_markers=false&start_date=1104537600&end_date=1485129600&show_fatal=1&show_severe=1&show_light=1&approx=&accurate=1&show_markers=1&show_discussions=1&show_urban=3&show_intersection=3&show_lane=3&show_day=7&show_holiday=0&show_time=24&start_time=25&end_time=25&weather=0&road=0&separation=0&surface=0&acctype=0&controlmeasure=0&district=0&case_type=0")
        self.assertEqual(rv.status, '200 OK')
        #print(rv.data)
        resp = json.loads(rv.data)
        self.assertIn('markers', resp)
        #self.assertEqual(len(resp['markers']), 16)
        for i in range(0,len(resp['markers'])):
          self.assertEqual(resp['markers'][i]['locationAccuracy'], 1)

    def test_markers_approx_only(self):
        rv = self.app.get("/markers?ne_lat=32.082754580757744&ne_lng=34.79886274337764&sw_lat=32.072645555012734&sw_lng=34.77712612152095&zoom=16&thin_markers=false&start_date=1104537600&end_date=1485129600&show_fatal=1&show_severe=1&show_light=1&approx=1&accurate=&show_markers=1&show_discussions=1&show_urban=3&show_intersection=3&show_lane=3&show_day=7&show_holiday=0&show_time=24&start_time=25&end_time=25&weather=0&road=0&separation=0&surface=0&acctype=0&controlmeasure=0&district=0&case_type=0")
        self.assertEqual(rv.status, '200 OK')
        #print(rv.data)
        resp = json.loads(rv.data)
        self.assertIn('markers', resp)
        #self.assertEqual(len(resp['markers']), 16)
        for i in range(0,len(resp['markers'])):
          self.assertTrue(resp['markers'][i]['locationAccuracy'] in (2,3))

    def test_clusters(self):
        rv = self.app.get("/clusters?ne_lat=34.430273343405844&ne_lng=44.643749999999955&sw_lat=28.84061194106889&sw_lng=22.385449218749955&zoom=6&thin_markers=true&start_date=1104537600&end_date=1486944000&show_fatal=1&show_severe=1&show_light=1&approx=1&accurate=1&show_markers=1&show_discussions=1&show_urban=3&show_intersection=3&show_lane=3&show_day=7&show_holiday=0&show_time=24&start_time=25&end_time=25&weather=0&road=0&separation=0&surface=0&acctype=0&controlmeasure=0&district=0&case_type=0")
        self.assertEqual(rv.status, '200 OK')
        #print(rv.data)
        resp = json.loads(rv.data)
        self.assertIn('clusters', resp)
        self.assertGreater(len(resp['clusters']), 0)

    def test_single_marker(self):
        rv = self.app.get("/markers/2014027147")
        self.assertEqual(rv.status, '200 OK')
        #print(rv.data)
        resp = json.loads(rv.data)
        #self.assertIn('clusters', resp)
        self.assertEqual(resp[0]['accident_id'], 2014027147)

# vim: expandtab

