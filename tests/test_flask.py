# -*- coding: utf-8 -*-
# from anyway.utilities import open_utf8
import json
import typing
from collections import Counter
from functools import partial
from http import HTTPStatus
from http import client as http_client
from unittest import mock
from unittest.mock import patch

import pytest
from flask import Response, jsonify
from flask.testing import FlaskClient
from urlobject import URLObject

from anyway.app_and_db import app as flask_app
from anyway.backend_constants import BE_CONST
from anyway.error_code_and_strings import (
    ERROR_TO_HTTP_CODE_DICT,
    build_json_for_user_api_error,
    Errors,
)
from anyway.views.user_system.api import is_a_valid_role_name, roles_and_grants_accepted


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


def assert_return_code_for_user_update(error_code: int, rv: Response, extra: str = None, msg: str = "") -> None:
    assert rv.status_code == ERROR_TO_HTTP_CODE_DICT[error_code], msg
    assert rv.json == build_json_for_user_api_error(error_code, extra), msg


def user_update_post_json(app: FlaskClient, json_data: typing.Optional[dict] = None) -> Response:
    return post_json(app, "/user/update", json_data)


def post_json(app: FlaskClient, path: str, json_data: typing.Optional[dict] = None) -> Response:
    return app.post(path, json=json_data, follow_redirects=True, mimetype="application/json")


def user_update_post(app: FlaskClient) -> Response:
    return app.post("/user/update", follow_redirects=True)

@pytest.mark.user_system
def test_user_update_not_logged_in(app):
    rv = user_update_post(app)
    assert_return_code_for_user_update(Errors.BR_BAD_AUTH, rv)

    rv = app.get("/user/update", follow_redirects=True)
    assert rv.status_code == HTTPStatus.METHOD_NOT_ALLOWED


@pytest.mark.user_system
def test_user_update_bad_json(app):
    with patch("flask_login.utils._get_user") as current_user:
        set_current_user_mock(current_user)

        rv = user_update_post(app)
        assert_return_code_for_user_update(Errors.BR_FIELD_MISSING, rv)

        rv = user_update_post_json(app)
        assert rv.status_code == HTTPStatus.BAD_REQUEST
        assert b"Field is missing from json" in rv.data

        rv = user_update_post_json(app, json_data={})
        assert_return_code_for_user_update(Errors.BR_FIELD_MISSING, rv)

        rv = user_update_post_json(app, json_data={"a": "a"})
        assert_return_code_for_user_update(Errors.BR_FIELD_MISSING, rv)


@pytest.mark.user_system
def test_user_update_names(app):
    with patch("flask_login.utils._get_user") as current_user:
        set_current_user_mock(current_user)

        rv = user_update_post_json(app, json_data={"first_name": "a"})
        assert_return_code_for_user_update(Errors.BR_FIRST_NAME_OR_LAST_NAME_MISSING, rv)

        rv = user_update_post_json(app, json_data={"last_name": "a"})
        assert_return_code_for_user_update(Errors.BR_FIRST_NAME_OR_LAST_NAME_MISSING, rv)


@pytest.mark.user_system
def test_user_fail_on_email(app):
    with patch("flask_login.utils._get_user") as current_user:
        set_current_user_mock(current_user)

        with patch("anyway.views.user_system.api.get_current_user_email") as get_current_user_email:
            get_current_user_email.side_effect = lambda: None

            rv = user_update_post_json(app, json_data={"first_name": "a", "last_name": "a"})
            assert_return_code_for_user_update(Errors.BR_NO_EMAIL, rv)

            rv = user_update_post_json(
                app, json_data={"first_name": "a", "last_name": "a", "email": "aaaa"}
            )
            assert_return_code_for_user_update(Errors.BR_BAD_EMAIL, rv)


@pytest.mark.user_system
def test_user_fail_on_phone(app):
    with patch("flask_login.utils._get_user") as current_user:
        set_current_user_mock(current_user)

        with patch("anyway.views.user_system.api.get_current_user_email") as get_current_user_email:
            get_current_user_email.side_effect = lambda: "aa@bb.com"

            rv = user_update_post_json(
                app, json_data={"first_name": "a", "last_name": "a", "phone": "1234567"}
            )
            assert_return_code_for_user_update(Errors.BR_BAD_PHONE, rv)


@pytest.mark.user_system
def test_user_update_success(app):
    with patch("flask_login.utils._get_user") as current_user:
        set_current_user_mock(current_user)

        with patch("anyway.views.user_system.api.get_current_user_email") as get_current_user_email:
            get_current_user_email.side_effect = lambda: None

            with patch("anyway.views.user_system.api.update_user_in_db"):
                rv = user_update_post_json(
                    app, json_data={"first_name": "a", "last_name": "a", "email": "aa@gmail.com"}
                )
                assert rv.status_code == HTTPStatus.OK, "1"

                get_current_user_email.side_effect = lambda: "aa@bb.com"

                rv = user_update_post_json(
                    app, json_data={"first_name": "a", "last_name": "a", "phone": "0541234567"}
                )
                assert rv.status_code == HTTPStatus.OK, "2"

                rv = user_update_post_json(app, json_data={"first_name": "a", "last_name": "a"})
                assert rv.status_code == HTTPStatus.OK, "3"

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
                assert rv.status_code == HTTPStatus.OK, "4"


# Used in test_get_current_user
USER_ID = 5
USER_EMAIL = "YossiCohen@gmail.com"
USER_ACTIVE = True
OAUTH_PROVIDER = "google"
FIRST_NAME = "Yossi"
LAST_NAME = "Cohen"
USER_COMPLETED = True


@pytest.mark.user_system
def test_get_current_user(app):
    rv = app.get("/user/info", follow_redirects=True)
    assert_return_code_for_user_update(Errors.BR_BAD_AUTH, rv)
    with patch("flask_login.utils._get_user") as current_user:
        set_current_user_mock(current_user)
        with patch("anyway.views.user_system.api.get_current_user") as get_current_user:
            get_mock_current_user(get_current_user)
            rv = app.get("/user/info", follow_redirects=True)
            assert rv.status_code == HTTPStatus.OK, "1"
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
                "app": 0,
            }, "2"


def get_mock_current_user(get_current_user: mock.MagicMock) -> mock.MagicMock:
    ret_obj = mock.MagicMock()
    ret_obj.serialize_exposed_to_user.side_effect = lambda: {
        "id": USER_ID,
        "user_register_date": None,
        "email": USER_EMAIL,
        "is_active": USER_ACTIVE,
        "oauth_provider": OAUTH_PROVIDER,
        "oauth_provider_user_name": None,
        "oauth_provider_user_picture_url": None,
        "first_name": FIRST_NAME,
        "last_name": LAST_NAME,
        "phone": None,
        "user_type": None,
        "user_url": None,
        "user_desc": None,
        "is_user_completed_registration": USER_COMPLETED,
        "roles": [],
        "app": 0,
    }
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
    ret_obj.app = 0
    get_current_user.side_effect = lambda: ret_obj
    return ret_obj


def set_current_user_mock(get_curr_user: mock.MagicMock, user_id=USER_ID) -> None:
    get_curr_user.return_value = mock.MagicMock()
    get_curr_user.return_value.is_anonymous = False
    get_curr_user.return_value.id = user_id
    get_curr_user.return_value.app = 0
    get_curr_user.return_value.grants = []
    get_curr_user.return_value.email = USER_EMAIL
    authenticated = mock.MagicMock()
    authenticated.name = BE_CONST.Roles2Names.Authenticated.value
    authenticated.app = 0
    get_curr_user.return_value.roles = [authenticated]


@pytest.mark.user_system
def test_user_remove_from_role(app):
    user_add_or_remove_role(app, "/user/remove_from_role")


@pytest.mark.user_system
def test_user_add_to_role(app):
    user_add_or_remove_role(app, "/user/add_to_role")


def user_add_or_remove_role(app: FlaskClient, path: str) -> None:
    rv = app.get(path, follow_redirects=True)
    assert rv.status_code == HTTPStatus.METHOD_NOT_ALLOWED, "1"
    with patch("flask_login.utils._get_user") as current_user:
        set_mock_and_test_perm(app, current_user, path)

        rv = post_json(app, path, json_data={"email": "a"})
        assert_return_code_for_user_update(Errors.BR_NAME_MISSING, rv, msg="2")

        with patch("anyway.views.user_system.api.get_role_object") as get_role_object:
            get_role_object.return_value = mock.MagicMock()
            get_role_object.return_value.name = BE_CONST.Roles2Names.Admins.value

            rv = post_json(
                app, path, json_data={"role": BE_CONST.Roles2Names.Admins.value, "email": "a"}
            )
            assert_return_code_for_user_update(Errors.BR_USER_NOT_FOUND, rv, extra="a", msg="3")


def set_mock_and_test_perm(app, current_user, path):
    set_current_user_mock(current_user)
    rv = app.post(path, follow_redirects=True)
    assert_return_code_for_user_update(Errors.BR_BAD_AUTH, rv, msg="3")
    role = mock.MagicMock()
    role.name = BE_CONST.Roles2Names.Admins.value
    role.app = 0
    current_user.return_value.roles = [role]


@pytest.mark.user_system
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


@pytest.mark.single_test
@pytest.mark.user_system
def test_user_change_user_active_mode(app: FlaskClient) -> None:
    path = "/user/change_user_active_mode"
    rv = app.get(path, follow_redirects=True)
    assert rv.status_code == HTTPStatus.METHOD_NOT_ALLOWED, "1"
    with patch("flask_login.utils._get_user") as current_user:
        set_mock_and_test_perm(app, current_user, path)

        rv = post_json(app, path, json_data={"email": "a"})
        assert_return_code_for_user_update(Errors.BR_USER_NOT_FOUND, rv, extra="a", msg="2")
        with patch("anyway.views.user_system.api.get_user_by_email") as get_user_by_email:
            get_user_by_email.side_effect = lambda db, email, app_id: mock.MagicMock()

            rv = post_json(app, path, json_data={"email": "a@b.com"})
            assert_return_code_for_user_update(Errors.BR_NO_MODE, rv, msg="3")

            rv = post_json(app, path, json_data={"email": "a@b.com", "mode": "true"})
            assert_return_code_for_user_update(Errors.BR_BAD_MODE, rv, msg="4")

            rv = post_json(app, path, json_data={"email": "a@b.com", "mode": 1})
            assert_return_code_for_user_update(Errors.BR_BAD_MODE, rv, msg="5")

            rv = post_json(app, path, json_data={"email": "a@b.com", "mode": False})
            assert rv.status_code == HTTPStatus.OK, "5"


@pytest.mark.user_system
def test_add_role(app):
    path = "/user/add_role"
    rv = app.get(path, follow_redirects=True)
    assert rv.status_code == HTTPStatus.METHOD_NOT_ALLOWED
    with patch("flask_login.utils._get_user") as current_user:
        set_mock_and_test_perm(app, current_user, path)

        rv = post_json(app, path, json_data={"email": "a"})
        assert_return_code_for_user_update(Errors.BR_NAME_MISSING, rv)

        rv = post_json(app, path, json_data={"description": ""})
        assert_return_code_for_user_update(Errors.BR_NAME_MISSING, rv)

        rv = post_json(app, path, json_data={"name": ""})
        assert_return_code_for_user_update(Errors.BR_NAME_MISSING, rv)

        rv = post_json(app, path, json_data={"name": "aa vv"})
        assert_return_code_for_user_update(Errors.BR_BAD_NAME, rv)

        rv = post_json(app, path, json_data={"name": "aa"})
        assert_return_code_for_user_update(Errors.BR_DESCRIPTION_MISSING, rv)

        rv = post_json(app, path, json_data={"name": "aa", "description": ""})
        assert_return_code_for_user_update(Errors.BR_DESCRIPTION_MISSING, rv)


@pytest.mark.skip(reason="already covered by others. kept for future tests.")
def test_grant_and_admin_endpoint(app):
    """Test endpoint that requires both admin role and test_grant grant."""
    path = "/sd-user/test_grant_and_admin"

    # Test 1: Not logged in (anonymous) - handled same as roles_accepted()
    rv = app.get(path, follow_redirects=True)
    assert_return_code_for_user_update(Errors.BR_BAD_AUTH, rv, msg="1")

    with patch("flask_login.utils._get_user") as current_user:
        # Test 2: Authenticated user without "app" attribute - internal server error
        set_current_user_mock(current_user)
        # Remove app attribute if it exists
        if hasattr(current_user.return_value, 'app'):
            delattr(current_user.return_value, 'app')
        rv = app.get(path, follow_redirects=True)
        assert rv.status_code == HTTPStatus.INTERNAL_SERVER_ERROR, "2"
        assert "missing app attribute" in rv.json.get("error_msg", "").lower(), "2b"

        # Test 3: User with different app_id - bad auth
        current_user.return_value.app = 0  # ANYWAY_APP_ID instead of SAFETY_DATA_APP_ID
        role3 = mock.MagicMock()
        role3.name = BE_CONST.Roles2Names.Admins.value
        grant3 = mock.MagicMock()
        grant3.name = "test_grant"
        grant3.app = 1  # SAFETY_DATA_APP_ID
        current_user.return_value.roles = [role3]
        current_user.return_value.grants = [grant3]
        rv = app.get(path, follow_redirects=True)
        assert_return_code_for_user_update(Errors.BR_BAD_AUTH, rv, msg="3")

        # Test 4: Logged in with correct app_id but not admin and no grant
        current_user.return_value.app = 1  # SAFETY_DATA_APP_ID
        current_user.return_value.roles = []
        current_user.return_value.grants = []
        rv = app.get(path, follow_redirects=True)
        assert_return_code_for_user_update(Errors.BR_MISSING_PERMISSION, rv, msg="4")

        # Test 5: Admin but no grant
        role = mock.MagicMock()
        role.name = BE_CONST.Roles2Names.Admins.value
        current_user.return_value.roles = [role]
        current_user.return_value.grants = []
        rv = app.get(path, follow_redirects=True)
        assert_return_code_for_user_update(Errors.BR_MISSING_PERMISSION, rv, msg="5")

        # Test 6: Has grant but not admin
        grant = mock.MagicMock()
        grant.name = "test_grant"
        grant.app = 1  # SAFETY_DATA_APP_ID
        current_user.return_value.roles = []
        current_user.return_value.grants = [grant]
        rv = app.get(path, follow_redirects=True)
        assert_return_code_for_user_update(Errors.BR_BAD_AUTH, rv, msg="6")

        # Test 7: Has admin and grant - should succeed
        role = mock.MagicMock()
        role.name = BE_CONST.Roles2Names.Admins.value
        grant = mock.MagicMock()
        grant.name = "test_grant"
        grant.app = 1  # SAFETY_DATA_APP_ID
        current_user.return_value.roles = [role]
        current_user.return_value.grants = [grant]
        rv = app.get(path, follow_redirects=True)
        assert rv.status_code == HTTPStatus.OK, "7"
        assert rv.json == {"message": "Access granted: user has both admin role and test_grant grant"}, "8"

        # Test 8: Has admin and different grant - should fail
        grant2 = mock.MagicMock()
        grant2.name = "other_grant"
        grant2.app = 1
        current_user.return_value.grants = [grant2]
        rv = app.get(path, follow_redirects=True)
        assert_return_code_for_user_update(Errors.BR_MISSING_PERMISSION, rv, msg="9")


def create_test_endpoint(roles=None, grants=None, app_id=1, need_all_permissions=False, endpoint_name=None, url_path=None):
    """
    Helper function to create a test endpoint with variable decorator parameters.

    Args:
        roles: List of required role names
        grants: List of required grant names
        app_id: App ID for grant checking
        need_all_permissions: Whether user needs all permissions
        endpoint_name: Unique endpoint name (auto-generated if None)
        url_path: URL path for the endpoint (auto-generated if None)

    Returns:
        tuple: (endpoint_name, url_path) for cleanup
    """
    if endpoint_name is None:
        import uuid
        endpoint_name = f"test_endpoint_{uuid.uuid4().hex[:8]}"
    if url_path is None:
        url_path = f"/api/test_{endpoint_name}"

    # Create endpoint with variable decorator parameters
    @roles_and_grants_accepted(roles=roles, grants=grants, app_id=app_id, need_all_permissions=need_all_permissions)
    def test_endpoint():
        return jsonify({"message": "OK"}), 200

    # Register the endpoint
    flask_app.add_url_rule(url_path, endpoint=endpoint_name, view_func=test_endpoint, methods=["GET"])

    return endpoint_name, url_path


def cleanup_test_endpoint(endpoint_name):
    """Helper function to clean up a test endpoint."""
    try:
        # Remove from url_map
        rules_to_remove = [rule for rule in flask_app.url_map._rules if rule.endpoint == endpoint_name]
        for rule in rules_to_remove:
            flask_app.url_map._rules.remove(rule)
        # Rebuild the rules_by_endpoint dict
        flask_app.url_map._rules_by_endpoint = {}
        for rule in flask_app.url_map._rules:
            flask_app.url_map._rules_by_endpoint.setdefault(rule.endpoint, []).append(rule)
        # Remove from view_functions
        if endpoint_name in flask_app.view_functions:
            del flask_app.view_functions[endpoint_name]
    except Exception:
        # If cleanup fails, it's not critical for the test
        pass


# @pytest.mark.single_test
# @pytest.mark.user_system
@pytest.mark.skip(reason="Long test, run manually when needed")
def test_roles_and_grants_accepted(app):
    endpoint = "/api/test"
    url="/api/test"
    with patch("flask_login.utils._get_user") as get_curr_user:
        set_current_user_mock(get_curr_user)

        def run_test(roles, grants, app_id, need_all: bool, expected_error: int, app, msg:str=""):
            endpoint_name, url_path = create_test_endpoint(
                roles=roles,
                grants=grants,
                app_id=app_id,
                need_all_permissions=need_all,
                endpoint_name=endpoint,
                url_path=url,
            )
            try:
                rv = app.get(url_path, follow_redirects=True)
                if expected_error == 0:
                    assert rv.status_code == HTTPStatus.OK, msg
                else:
                    assert_return_code_for_user_update(expected_error, rv, msg=msg)
            finally:
                cleanup_test_endpoint(endpoint_name)

        run_test(roles=["not_exist"], grants=[], app_id=1, need_all=False,
                 expected_error=Errors.BR_BAD_AUTH,
                 app=app, msg="1 wrong app id")

        run_test(roles=["not_exist"], grants=[], app_id=0, need_all=False,
                 expected_error=Errors.BR_MISSING_PERMISSION,
                 app=app, msg="2 Missing permission")

        get_curr_user.return_value.app = 1  # ANYWAY_APP_ID instead of SAFETY_DATA_APP_ID
        role3 = mock.MagicMock()
        role3.name = "role3"
        get_curr_user.return_value.roles = [role3]

        run_test(roles=["role3"], grants=[], app_id=1, need_all=False,
                 expected_error=0, app=app, msg="3 Should succeed")
        run_test(roles=["role3"], grants=[], app_id=1, need_all=True,
                 expected_error=0, app=app, msg="4 Should succeed")
        run_test(roles=[], grants=["grant3"], app_id=1, need_all=False,
                 expected_error=Errors.BR_MISSING_PERMISSION, app=app, msg="5 Missing role")
        run_test(roles=["role3"], grants=["grant3"], app_id=1, need_all=False,
                 expected_error=0, app=app, msg="6 Should succeed")
        run_test(roles=["role3"], grants=["grant3"], app_id=1, need_all=True,
                 expected_error=Errors.BR_MISSING_PERMISSION, app=app, msg="7 Missing grant")

        grant3 = mock.MagicMock()
        grant3.name = "grant3"
        grant3.app = 1  # SAFETY_DATA_APP_ID
        get_curr_user.return_value.grants = [grant3]

        run_test(roles=[], grants=["grant3"], app_id=1, need_all=False,
                 expected_error=0, app=app, msg="8 Should succeed")
        run_test(roles=[], grants=["grant4"], app_id=1, need_all=False,
                 expected_error=Errors.BR_MISSING_PERMISSION, app=app, msg="9 Should succeed")
        run_test(roles=[], grants=["grant3"], app_id=1, need_all=True,
                 expected_error=0, app=app, msg="10 Should succeed")
        run_test(roles=["role4"], grants=["grant3"], app_id=1, need_all=False,
                 expected_error=0, app=app, msg="11 Should succeed")
        run_test(roles=["role4"], grants=["grant3"], app_id=1, need_all=True,
                 expected_error=Errors.BR_MISSING_PERMISSION, app=app, msg="12 Missing grant")
