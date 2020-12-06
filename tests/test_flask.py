# -*- coding: utf-8 -*-
# from anyway.utilities import open_utf8
import json
from collections import Counter
from functools import partial

import pytest
from http import client as http_client
from urlobject import URLObject

from anyway.app_and_db import app as flask_app
from anyway.flask_app import check_is_a_safe_redirect_url


@pytest.fixture
def app():
    return flask_app.test_client()


query_flag = partial(pytest.mark.parametrize, argvalues=["1", ""])


def test_url_redirect_checker(app):
    bad_urls = [
        "127,0.0.1",
        "127,0.0.1:50",
        "127.0.0.a:50",
        "127.0.0.1:50a",
        "https://127.0.0.a:50",
        "https://127.0.0.2:50",
        "https://127.0.0.1:50a",
        "https://127.0.0.1:a",
        "https://127.0.0.1:12345678",
        "https://127.0.0.1:12345678",
        "https://127.0.0.1.com",
        "127.0.0.1:50/test" "127.0.0.1",
        "127.0.0.1:50",
        "www.anyway.co.il",
        "https://www.anyway.com",
        "anyway.co.il",
        "https//cnn.com",
        "https//www.cnn.com" "https://www.anyway.co.il.com",
        "http://www.anyway.co.il.com",
        "https://anyway.com" "www.anyway-infographics-staging.web.app",
        "https://anyway-infographics-staging.web.app.com" "anyway-infographics-staging.web.app.com",
        "anyway-infographics-staging.web.app",
        "anyway-infographics-staging.web.app/test",
        "localhost",
        "localhost:8000",
        "localhost.com",
    ]

    good_urls = [
        "https://127.0.0.1",
        "https://127.0.0.1:50",
        "http://localhost",
        "http://localhost:8000",
        "https://127.0.0.1:50/test",
        "https://www.anyway.co.il/test",
        "https://www.anyway.co.il",
        "https://anyway-infographics-staging.web.app",
        "https://anyway-infographics-staging.web.app/test",
    ]

    for url in bad_urls:
        assert check_is_a_safe_redirect_url(url) is False

    for url in good_urls:
        assert check_is_a_safe_redirect_url(url) is True


@pytest.mark.server
def test_main(app):
    rv = app.get("/")
    assert rv.status_code == http_client.OK
    assert "<title>ANYWAY - משפיעים בכל דרך</title>" in rv.data.decode("utf-8")


# It requires parameters to know which markers you want.
@pytest.mark.server
def test_markers_empty(app):
    rv = app.get("/markers")
    assert rv.status_code == http_client.BAD_REQUEST
    assert "<title>400 Bad Request</title>" in rv.data.decode("utf-8")


@pytest.fixture(scope="module")
def marker_counter():
    counter = Counter()
    yield counter
    assert counter["markers"] == 1624


@pytest.mark.server
def test_bad_date(app):
    rv = app.get(
        "/markers?ne_lat=32.08656790211843&ne_lng=34.80611543655391&sw_lat=32.08003198103277&sw_lng=34.793884563446&zoom=17&thin_markers=false&start_date=a1104537600&end_date=1484697600&show_fatal=1&show_severe=1&show_light=1&approx=1&accurate=1&show_markers=1&show_discussions=1&show_urban=3&show_intersection=3&show_lane=3&show_day=7&show_holiday=0&show_time=24&start_time=25&end_time=25&weather=0&road=0&separation=0&surface=0&acctype=0&controlmeasure=0&district=0&case_type=0"
    )
    assert rv.status_code == http_client.BAD_REQUEST


@pytest.mark.partial_db
@query_flag("show_fatal")
@query_flag("show_severe")
@query_flag("show_light")
@query_flag("show_approx")
@query_flag("show_accurate")
def test_markers(
    app, show_fatal, show_severe, show_light, show_accurate, show_approx, marker_counter
):
    url = URLObject("/markers").set_query_params(
        {
            "ne_lat": "32.085413468822",
            "ne_lng": "34.797736215591385",
            "sw_lat": "32.07001357040486",
            "sw_lng": "34.775548982620194",
            "zoom": "16",
            "thin_markers": "false",
            "start_date": "1104537600",
            "end_date": "1484697600",
            "show_fatal": show_fatal,
            "show_severe": show_severe,
            "show_light": show_light,
            "approx": show_approx,
            "accurate": show_accurate,
            "show_markers": "1",
            "show_accidents": "1",
            "show_rsa": "0",
            "show_discussions": "1",
            "show_urban": "3",
            "show_intersection": "3",
            "show_lane": "3",
            "show_day": "7",
            "show_holiday": "0",
            "show_time": "24",
            "start_time": "25",
            "end_time": "25",
            "weather": "0",
            "road": "0",
            "separation": "0",
            "surface": "0",
            "acctype": "0",
            "controlmeasure": "0",
            "district": "0",
            "case_type": "0",
        }
    )

    rv = app.get(url)
    assert rv.status_code == http_client.OK
    assert rv.headers["Content-Type"] == "application/json"

    resp = json.loads(rv.data.decode("utf-8"))

    marker_counter["markers"] += len(resp["markers"])

    for marker in resp["markers"]:
        assert show_fatal or marker["accident_severity"] != 1
        assert show_severe or marker["accident_severity"] != 2
        assert show_light or marker["accident_severity"] != 3
        assert show_accurate or marker["location_accuracy"] != 1
        assert show_approx or marker["location_accuracy"] == 1
