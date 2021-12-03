import typing
from http import HTTPStatus
from unittest import mock
from unittest.mock import patch

import pytest
from flask import Response
from flask.testing import FlaskClient

from anyway.app_and_db import app as flask_app
from anyway.backend_constants import BE_CONST
from anyway.error_code_and_strings import (
    ERROR_TO_HTTP_CODE_DICT,
    build_json_for_user_api_error,
    Errors,
)
from anyway.views.user_system.api import is_a_valid_role_name


@pytest.fixture
def app():
    flask_app.secret_key = "test_key_dont_use_in_prod"
    return flask_app.test_client()


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
    assert_return_code_for_user_update(Errors.BR_BAD_AUTH, rv)

    rv = app.get("/user/update", follow_redirects=True)
    assert rv.status_code == HTTPStatus.METHOD_NOT_ALLOWED


def test_user_update_bad_json(app):
    with patch("flask_login.utils._get_user") as current_user:
        set_current_user_mock(current_user)

        rv = user_update_post(app)
        assert_return_code_for_user_update(Errors.BR_FIELD_MISSING, rv)

        rv = user_update_post_json(app)
        assert rv.status_code == HTTPStatus.BAD_REQUEST
        assert b"Failed to decode JSON object" in rv.data

        rv = user_update_post_json(app, json_data={})
        assert_return_code_for_user_update(Errors.BR_FIELD_MISSING, rv)

        rv = user_update_post_json(app, json_data={"a": "a"})
        assert_return_code_for_user_update(Errors.BR_FIELD_MISSING, rv)


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

        with patch("anyway.views.user_system.api.get_current_user_email") as get_current_user_email:
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

        with patch("anyway.views.user_system.api.get_current_user_email") as get_current_user_email:
            get_current_user_email.side_effect = lambda: "aa@bb.com"

            rv = user_update_post_json(
                app, json_data={"first_name": "a", "last_name": "a", "phone": "1234567"}
            )
            assert_return_code_for_user_update(Errors.BR_BAD_PHONE, rv)


def test_user_update_success(app):
    with patch("flask_login.utils._get_user") as current_user:
        set_current_user_mock(current_user)

        with patch("anyway.views.user_system.api.get_current_user_email") as get_current_user_email:
            get_current_user_email.side_effect = lambda: None

            with patch("anyway.views.user_system.api.update_user_in_db"):
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
    assert_return_code_for_user_update(Errors.BR_BAD_AUTH, rv)
    with patch("flask_login.utils._get_user") as current_user:
        set_current_user_mock(current_user)
        with patch("anyway.views.user_system.api.get_current_user") as get_current_user:
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

        with patch("anyway.views.user_system.api.get_role_object") as get_role_object:
            get_role_object.return_value = mock.MagicMock()
            get_role_object.return_value.name = BE_CONST.Roles2Names.Admins.value

            rv = post_json(
                app, path, json_data={"role": BE_CONST.Roles2Names.Admins.value, "email": "a"}
            )
            assert_return_code_for_user_update(Errors.BR_USER_NOT_FOUND, rv, extra="a")


def set_mock_and_test_perm(app, current_user, path):
    set_current_user_mock(current_user)
    rv = app.post(path, follow_redirects=True)
    assert_return_code_for_user_update(Errors.BR_BAD_AUTH, rv)
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
        assert_return_code_for_user_update(Errors.BR_USER_NOT_FOUND, rv, extra="a")
        with patch("anyway.views.user_system.api.get_user_by_email") as get_user_by_email:
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
        assert_return_code_for_user_update(Errors.BR_ROLE_NAME_MISSING, rv)

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
