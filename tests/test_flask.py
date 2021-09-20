# -*- coding: utf-8 -*-
# from anyway.utilities import open_utf8
import json
from collections import Counter
from functools import partial
from unittest import mock
from unittest.mock import patch

import pytest
from http import client as http_client, HTTPStatus

import typing

from flask import Response
from flask.testing import FlaskClient
from urlobject import URLObject

from anyway.app_and_db import app as flask_app
from anyway.backend_constants import BE_CONST
from anyway.error_code_and_strings import (
    ERROR_TO_HTTP_CODE_DICT,
    build_json_for_user_api_error,
    Errors,
)
from anyway.flask_app import is_a_valid_role_name


@pytest.fixture
def app():
    flask_app.secret_key = "test_key_dont_use_in_prod"
    return flask_app.test_client()


query_flag = partial(pytest.mark.parametrize, argvalues=["1", ""])


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


def assert_return_code_for_user_update(error_code: int, rv: Response, extra: str = None) -> None:
    assert rv.status_code == ERROR_TO_HTTP_CODE_DICT[error_code]
    assert rv.json == build_json_for_user_api_error(error_code, extra)


def user_update_post_json(app: FlaskClient, json_data: typing.Optional[dict] = None) -> Response:
    return post_json(app, "/user/update", json_data)


def post_json(app: FlaskClient, path: str, json_data: typing.Optional[dict] = None) -> Response:
    return app.post(path, json=json_data, follow_redirects=True, mimetype="application/json")


def user_update_post(app: FlaskClient) -> Response:
    return app.post("/user/update", follow_redirects=True)


def test_user_update_not_logged_in(app):
    rv = user_update_post(app)
    assert_return_code_for_user_update(Errors.BR_USER_NOT_LOGGED_IN, rv)

    rv = app.get("/user/update", follow_redirects=True)
    assert rv.status_code == HTTPStatus.METHOD_NOT_ALLOWED


def test_user_update_bad_json(app):
    with patch("flask_login.utils._get_user") as current_user:
        set_current_user_mock(current_user)

        rv = user_update_post(app)
        assert_return_code_for_user_update(Errors.BR_BAD_JSON, rv)

        rv = user_update_post_json(app)
        assert rv.status_code == HTTPStatus.BAD_REQUEST
        assert b"Failed to decode JSON object" in rv.data

        rv = user_update_post_json(app, json_data={})
        assert_return_code_for_user_update(Errors.BR_BAD_JSON, rv)

        rv = user_update_post_json(app, json_data={"a": "a"})
        assert_return_code_for_user_update(Errors.BR_UNKNOWN_FIELD, rv, "a")


def test_user_update_names(app):
    with patch("flask_login.utils._get_user") as current_user:
        set_current_user_mock(current_user)

        rv = user_update_post_json(app, json_data={"first_name": "a"})
        assert_return_code_for_user_update(Errors.BR_FIRST_NAME_OR_LAST_NAME_MISSING, rv)

        rv = user_update_post_json(app, json_data={"last_name": "a"})
        assert_return_code_for_user_update(Errors.BR_FIRST_NAME_OR_LAST_NAME_MISSING, rv)


def test_user_fail_on_email(app):
    with patch("flask_login.utils._get_user") as current_user:
        set_current_user_mock(current_user)

        with patch("anyway.flask_app.get_current_user_email") as get_current_user_email:
            get_current_user_email.side_effect = lambda: None

            rv = user_update_post_json(app, json_data={"first_name": "a", "last_name": "a"})
            assert_return_code_for_user_update(Errors.BR_NO_EMAIL, rv)

            rv = user_update_post_json(
                app, json_data={"first_name": "a", "last_name": "a", "email": "aaaa"}
            )
            assert_return_code_for_user_update(Errors.BR_BAD_EMAIL, rv)


def test_user_fail_on_phone(app):
    with patch("flask_login.utils._get_user") as current_user:
        set_current_user_mock(current_user)

        with patch("anyway.flask_app.get_current_user_email") as get_current_user_email:
            get_current_user_email.side_effect = lambda: "aa@bb.com"

            rv = user_update_post_json(
                app, json_data={"first_name": "a", "last_name": "a", "phone": "1234567"}
            )
            assert_return_code_for_user_update(Errors.BR_BAD_PHONE, rv)


def test_user_update_success(app):
    with patch("flask_login.utils._get_user") as current_user:
        set_current_user_mock(current_user)

        with patch("anyway.flask_app.get_current_user_email") as get_current_user_email:
            get_current_user_email.side_effect = lambda: None

            with patch("anyway.flask_app.update_user_in_db"):
                rv = user_update_post_json(
                    app, json_data={"first_name": "a", "last_name": "a", "email": "aa@gmail.com"}
                )
                assert rv.status_code == HTTPStatus.OK

                get_current_user_email.side_effect = lambda: "aa@bb.com"

                rv = user_update_post_json(
                    app, json_data={"first_name": "a", "last_name": "a", "phone": "0541234567"}
                )
                assert rv.status_code == HTTPStatus.OK

                rv = user_update_post_json(app, json_data={"first_name": "a", "last_name": "a"})
                assert rv.status_code == HTTPStatus.OK

                send_json = {
                    "first_name": "a",
                    "last_name": "a",
                    "email": "aa@gmail.com",
                    "phone": "0541234567",
                    "user_type": "journalist",
                    "user_url": "http:\\www.a.com",
                    "user_desc": "a",
                }
                rv = user_update_post_json(app, json_data=send_json)
                assert rv.status_code == HTTPStatus.OK


# Used in test_get_current_user
USER_ID = 5
USER_EMAIL = "YossiCohen@gmail.com"
USER_ACTIVE = True
OAUTH_PROVIDER = "google"
FIRST_NAME = "Yossi"
LAST_NAME = "Cohen"
USER_COMPLETED = True


def test_get_current_user(app):
    rv = app.get("/user/info", follow_redirects=True)
    assert_return_code_for_user_update(Errors.BR_USER_NOT_LOGGED_IN, rv)
    with patch("flask_login.utils._get_user") as current_user:
        set_current_user_mock(current_user)
        with patch("anyway.flask_app.get_current_user") as get_current_user:
            get_mock_current_user(get_current_user)
            rv = app.get("/user/info", follow_redirects=True)
            assert rv.status_code == HTTPStatus.OK
            assert rv.json == {
                "id": USER_ID,
                "email": USER_EMAIL,
                "is_active": USER_ACTIVE,
                "oauth_provider": OAUTH_PROVIDER,
                "first_name": FIRST_NAME,
                "last_name": LAST_NAME,
                "is_user_completed_registration": USER_COMPLETED,
                "oauth_provider_user_name": None,
                "oauth_provider_user_picture_url": None,
                "phone": None,
                "user_desc": None,
                "user_register_date": None,
                "user_type": None,
                "user_url": None,
                "roles": [],
            }


def get_mock_current_user(get_current_user: mock.MagicMock) -> mock.MagicMock:
    ret_obj = mock.MagicMock()
    ret_obj.id = USER_ID
    ret_obj.user_register_date = None
    ret_obj.email = USER_EMAIL
    ret_obj.is_active = USER_ACTIVE
    ret_obj.oauth_provider = OAUTH_PROVIDER
    ret_obj.oauth_provider_user_name = None
    ret_obj.oauth_provider_user_picture_url = None
    ret_obj.phone = None
    ret_obj.user_type = None
    ret_obj.user_url = None
    ret_obj.user_desc = None
    ret_obj.first_name = FIRST_NAME
    ret_obj.last_name = LAST_NAME
    ret_obj.is_user_completed_registration = USER_COMPLETED
    ret_obj.roles = []
    get_current_user.side_effect = lambda: ret_obj
    return ret_obj


def set_current_user_mock(current_user: mock.MagicMock) -> None:
    current_user.return_value = mock.MagicMock()
    current_user.return_value.is_anonymous = False
    current_user.return_value.id = USER_ID


def test_user_remove_from_role(app):
    user_add_or_remove_role(app, "/user/remove_from_role")


def test_user_add_to_role(app):
    user_add_or_remove_role(app, "/user/add_to_role")


def user_add_or_remove_role(app: FlaskClient, path: str) -> None:
    rv = app.get(path, follow_redirects=True)
    assert rv.status_code == HTTPStatus.METHOD_NOT_ALLOWED
    with patch("flask_login.utils._get_user") as current_user:
        set_mock_and_test_perm(app, current_user, path)

        rv = post_json(app, path, json_data={"email": "a"})
        assert_return_code_for_user_update(Errors.BR_ROLE_NAME_MISSING, rv)

        with patch("anyway.flask_app.get_role_object") as get_role_object:
            get_role_object.return_value = mock.MagicMock()
            get_role_object.return_value.name = BE_CONST.Roles2Names.Admins.value

            rv = post_json(
                app, path, json_data={"role": BE_CONST.Roles2Names.Admins.value, "email": "a"}
            )
            assert_return_code_for_user_update(Errors.BR_BAD_EMAIL, rv)


def set_mock_and_test_perm(app, current_user, path):
    set_current_user_mock(current_user)
    rv = app.post(path, follow_redirects=True)
    assert_return_code_for_user_update(
        Errors.BR_MISSING_PERMISSION, rv
    )
    role = mock.MagicMock()
    role.name = BE_CONST.Roles2Names.Admins.value
    current_user.return_value.roles = [role]


def test_is_a_valid_role_name():
    bad_names = [
        "בדיקה",
        "aa bbb",
        "$%@",
        "a" * 1024,
        "",
    ]

    good_names = [
        "test",
    ]

    for url in bad_names:
        assert not is_a_valid_role_name(url)

    for url in good_names:
        assert is_a_valid_role_name(url)


def test_user_change_user_active_mode(app: FlaskClient) -> None:
    path = "/user/change_user_active_mode"
    rv = app.get(path, follow_redirects=True)
    assert rv.status_code == HTTPStatus.METHOD_NOT_ALLOWED
    with patch("flask_login.utils._get_user") as current_user:
        set_mock_and_test_perm(app, current_user, path)

        rv = post_json(app, path, json_data={"email": "a"})
        assert_return_code_for_user_update(Errors.BR_BAD_EMAIL, rv)
        with patch("anyway.flask_app.get_user_by_email") as get_user_by_email:
            get_user_by_email.side_effect = lambda db, email: mock.MagicMock()

            rv = post_json(app, path, json_data={"email": "a@b.com"})
            assert_return_code_for_user_update(Errors.BR_NO_MODE, rv)

            rv = post_json(app, path, json_data={"email": "a@b.com", "mode": "true"})
            assert_return_code_for_user_update(Errors.BR_BAD_MODE, rv)

            rv = post_json(app, path, json_data={"email": "a@b.com", "mode": 1})
            assert_return_code_for_user_update(Errors.BR_BAD_MODE, rv)

            rv = post_json(app, path, json_data={"email": "a@b.com", "mode": False})
            assert rv.status_code == HTTPStatus.OK


def test_add_role(app):
    path = "/user/add_role"
    rv = app.get(path, follow_redirects=True)
    assert rv.status_code == HTTPStatus.METHOD_NOT_ALLOWED
    with patch("flask_login.utils._get_user") as current_user:
        set_mock_and_test_perm(app, current_user, path)

        rv = post_json(app, path, json_data={"email": "a"})
        assert_return_code_for_user_update(Errors.BR_UNKNOWN_FIELD, rv, "email")

        rv = post_json(app, path, json_data={"description": ""})
        assert_return_code_for_user_update(Errors.BR_ROLE_NAME_MISSING, rv)

        rv = post_json(app, path, json_data={"name": ""})
        assert_return_code_for_user_update(Errors.BR_ROLE_NAME_MISSING, rv)

        rv = post_json(app, path, json_data={"name": "aa vv"})
        assert_return_code_for_user_update(Errors.BR_BAD_ROLE_NAME, rv)

        rv = post_json(app, path, json_data={"name": "aa"})
        assert_return_code_for_user_update(Errors.BR_ROLE_DESCRIPTION_MISSING, rv)

        rv = post_json(app, path, json_data={"name": "aa", "description": ""})
        assert_return_code_for_user_update(Errors.BR_ROLE_DESCRIPTION_MISSING, rv)
