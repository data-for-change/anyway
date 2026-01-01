import base64
import datetime
import json
import logging
import re
import typing
import copy
from functools import wraps
from http import HTTPStatus

from flask import Response, request, Request, jsonify, current_app, redirect, g
from flask_login import current_user, login_user, logout_user, LoginManager
from flask_principal import (
    Permission,
    RoleNeed,
    identity_changed,
    Identity,
    AnonymousIdentity,
    Principal,
    identity_loaded,
    UserNeed,
)
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from anyway.anyway_dataclasses.user_data import UserData
from anyway.app_and_db import db, app
from anyway.backend_constants import BE_CONST
from anyway.base import _set_cookie_hijack, _clear_cookie_hijack
from anyway.error_code_and_strings import (
    Errors as Es,
    ERROR_TO_HTTP_CODE_DICT,
    build_json_for_user_api_error,
)
from anyway.models import (
    Organization,
    Roles,
    Users,
    users_to_roles,
    users_to_organizations,
    Grant,
    users_to_grants,
)
from anyway.oauth import OAuthSignIn

from anyway.utilities import is_valid_number, is_a_valid_email, is_a_safe_redirect_url
from anyway.views.user_system.user_functions import (
    get_user_by_email,
    get_current_user_email,
    get_current_user,
)

# Setup Flask-login
login_manager = LoginManager()
# Those 2 function hijack are a temporary fix - more info in base.py
login_manager._set_cookie = _set_cookie_hijack
login_manager._clear_cookie = _clear_cookie_hijack
login_manager.init_app(app)
# Setup Flask-Principal
principals = Principal(app)

ANYWAY_APP_ID = 0
SAFETY_DATA_APP_ID = 1
ADMIN_EMAIL = "anyway@anyway.co.il"


# Copied and modified from flask-security
def roles_accepted(*roles, need_all_permission=False):
    """Decorator which specifies that a user must have at least one of the
    specified roles. Example::

        @app.route('/create_post')
        @roles_accepted('editor', 'author')
        def create_post():
            return 'Create Post'

    The current user must have either the `editor` role or `author` role in
    order to view the page.

    :param roles: The possible roles.
    """

    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if need_all_permission:
                permissions = [Permission(RoleNeed(role)) for role in roles]
                if False not in map(lambda perm: perm.can(), permissions):
                    return fn(*args, **kwargs)
            else:
                perm = Permission(*[RoleNeed(role) for role in roles])
                if perm.can():
                    return fn(*args, **kwargs)

            user_email = "not logged in"
            if not current_user.is_anonymous:
                user_email = current_user.email
            logging.info(
                f'roles_accepted: User "{user_email}" doesn\'t have the needed roles: {str(roles)} for Path {request.url_rule}'
            )
            return return_json_error(Es.BR_BAD_AUTH)

        return decorated_view

    return wrapper


def grants_accepted(*grant_names, app_id: int = SAFETY_DATA_APP_ID):
    """Decorator which specifies that a user must have at least one of the
    specified grants. Example::

        @app.route('/view_reports')
        @grants_accepted('view_reports', 'edit_reports')
        def view_reports():
            return 'View Reports'

    The current user must have either the `view_reports` grant or `edit_reports` grant in
    order to view the page.

    :param grant_names: The possible grant names.
    :param app_id: The app ID to check grants for (default: SAFETY_DATA_APP_ID).
    """

    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if current_user.is_anonymous:
                user_email = "not logged in"
                logging.info(
                    f'grants_accepted: User "{user_email}" is not logged in for Path {request.url_rule}'
                )
                return return_json_error(Es.BR_BAD_AUTH)

            # Check if user has any of the required grants
            user_grants = [grant.name for grant in current_user.grants if grant.app == app_id]
            has_grant = any(grant_name in user_grants for grant_name in grant_names)

            if not has_grant:
                user_email = current_user.email
                logging.info(
                    f'grants_accepted: User "{user_email}" doesn\'t have the needed grants: {str(grant_names)} for Path {request.url_rule}'
                )
                return return_json_error(Es.BR_MISSING_PERMISSION)

            return fn(*args, **kwargs)

        return decorated_view

    return wrapper


def roles_and_grants_accepted(
    roles: typing.List[str] = copy.copy([]),
    grants: typing.List[str] = copy.copy([]),
    app_id: int = SAFETY_DATA_APP_ID,
    need_all_permissions: bool = False,
):
    """Decorator which specifies that a user must have the required roles and/or grants.

    Example::

        @app.route('/admin_reports')
        @roles_and_grants_accepted(roles=['admins'], grants=['view_reports'], app_id=1)
        def admin_reports():
            return 'Admin Reports'

    The current user must have the specified roles (if any) and grants (if any).

    :param roles: List of required role names. If None or empty, role check is skipped.
    :param grants: List of required grant names. If None or empty, grant check is skipped.
    :param app_id: The app ID to check grants for (default: SAFETY_DATA_APP_ID).
    :param need_all_permissions: If True, user must have ALL specified roles/grants.
                                If False, user must have at least ONE of each specified type.
    """

    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            # Handle anonymous users same as roles_accepted()
            if current_user.is_anonymous:
                user_email = "not logged in"
                logging.info(
                    f'roles_and_grants_accepted: User "{user_email}" is not logged in for Path {request.url_rule}'
                )
                return return_json_error(Es.BR_BAD_AUTH)

            # If authenticated user doesn't have "app" attribute, it's an internal server error
            if not hasattr(current_user, "app"):
                user_email = getattr(current_user, "email", "unknown")
                logging.error(
                    f'roles_and_grants_accepted: Authenticated user "{user_email}" does not have "app" attribute for Path {request.url_rule}'
                )
                return Response(
                    response=json.dumps(
                        {
                            "error_code": 0,
                            "error_msg": "Internal server error: authenticated user missing app attribute",
                        }
                    ),
                    status=HTTPStatus.INTERNAL_SERVER_ERROR,
                    mimetype="application/json",
                )

            # If user has app with different value than app_id, handle as bad auth
            if current_user.app != app_id:
                user_email = current_user.email
                error_msg = (
                    f"belongs to a different app (app_id: {current_user.app}, required: {app_id})"
                )
                logging.info(
                    f'roles_and_grants_accepted: User "{user_email}" {error_msg} for Path {request.url_rule}'
                )
                return return_json_error(Es.BR_BAD_AUTH)

            user_email = current_user.email

            # Check roles if specified (skip if None or empty list)
            user_roles = {role.name for role in current_user.roles if role.app == app_id}
            if not current_user.is_anonymous:
                user_roles.add("authenticated")
            user_grants = {grant.name for grant in current_user.grants if grant.app == app_id}
            has_roles = (
                set(roles).issubset(user_roles) if need_all_permissions else set(roles) & user_roles
            )
            has_grants = (
                set(grants).issubset(user_grants)
                if need_all_permissions
                else set(grants) & user_grants
            )
            if has_roles and has_grants if need_all_permissions else (has_roles or has_grants):
                return fn(*args, **kwargs)
            else:
                logging.info(
                    f'roles_and_grants_accepted: User "{user_email}" doesn\'t have one of the needed roles: {str(roles)} or grants: {str(grants)} for Path {request.url_rule}'
                )
                return return_json_error(Es.BR_BAD_AUTH)

        return decorated_view

    return wrapper


@login_manager.user_loader
def load_user(id: str) -> Users:
    return db.session.query(Users).get(id)


# noinspection PyUnusedLocal
@identity_loaded.connect_via(app)
def on_identity_loaded(sender, identity):
    # Set the identity user object
    identity.user = current_user

    # Add the UserNeed to the identity
    if hasattr(current_user, "id"):
        identity.provides.add(UserNeed(current_user.id))

    # Assuming the User model has a list of roles, update the
    # identity with the roles that the user provides
    if hasattr(current_user, "roles"):
        for role in current_user.roles:
            identity.provides.add(RoleNeed(role.name))

    if not current_user.is_anonymous:
        identity.provides.add(RoleNeed("authenticated"))


@principals.identity_loader
def load_identity_when_session_expires():
    if hasattr(current_user, "id"):
        if hasattr(current_user, "is_active"):
            if not current_user.is_active:
                logout_user()
                return AnonymousIdentity()

        return Identity(current_user.id)


def return_json_error(error_code: int, *argv) -> Response:
    return Response(
        response=json.dumps(build_json_for_user_api_error(error_code, argv)),
        status=ERROR_TO_HTTP_CODE_DICT[error_code],
        mimetype="application/json",
    )


def an_oauth_authorize(provider: str) -> Response:
    return oauth_authorize(provider, callback_endpoint="an_oauth_callback", app_id=ANYWAY_APP_ID)


def sd_oauth_authorize(provider: str) -> Response:
    return oauth_authorize(
        provider, callback_endpoint="sd_oauth_callback", app_id=SAFETY_DATA_APP_ID
    )


def oauth_authorize(provider: str, callback_endpoint: str, app_id: int) -> Response:
    if provider != "google":
        return return_json_error(Es.BR_ONLY_SUPPORT_GOOGLE)

    # Allow login if user is anonymous OR logged into a different app
    if not current_user.is_anonymous and current_user.app == app_id:
        return return_json_error(Es.BR_USER_ALREADY_LOGGED_IN)

    redirect_url_from_url = request.args.get("redirect_url", type=str)
    redirect_url = BE_CONST.DEFAULT_REDIRECT_URL
    if redirect_url_from_url and is_a_safe_redirect_url(redirect_url_from_url):
        redirect_url = redirect_url_from_url

    oauth = OAuthSignIn.get_provider(provider)
    return oauth.authorize(callback_endpoint=callback_endpoint, redirect_url=redirect_url)


def logout() -> Response:
    logout_user()
    identity_changed.send(current_app._get_current_object(), identity=AnonymousIdentity())
    return Response(status=HTTPStatus.OK)


def an_oauth_callback(provider: str, app_id: int = ANYWAY_APP_ID) -> Response:
    return oauth_callback(provider, app_id=ANYWAY_APP_ID, callback_endpoint="an_oauth_callback")


def sd_oauth_callback(provider: str, app_id: int = ANYWAY_APP_ID) -> Response:
    return oauth_callback(
        provider, app_id=SAFETY_DATA_APP_ID, callback_endpoint="sd_oauth_callback"
    )


def oauth_callback(provider: str, app_id: int, callback_endpoint: str) -> Response:
    if provider != "google":
        return return_json_error(Es.BR_ONLY_SUPPORT_GOOGLE)

    oauth = OAuthSignIn.get_provider(provider)
    user_data: UserData = oauth.callback(callback_endpoint=callback_endpoint)
    if not user_data or not user_data.service_user_id:
        return return_json_error(Es.BR_NO_USER_ID)

    user = None
    try:
        user = (
            db.session.query(Users)
            .filter_by(oauth_provider=provider, oauth_provider_user_id=user_data.service_user_id)
            .filter(Users.app == app_id)
            .one()
        )
    except (NoResultFound, MultipleResultsFound):
        try:
            user = (
                db.session.query(Users)
                .filter_by(oauth_provider=provider, email=user_data.email)
                .filter(Users.app == app_id)
                .one()
            )
        except MultipleResultsFound as e:
            # Internal server error - this case should not exists
            raise e
        except NoResultFound:
            pass

    if not user:
        user = Users(
            user_register_date=datetime.datetime.now(),
            user_last_login_date=datetime.datetime.now(),
            email=user_data.email,
            oauth_provider_user_name=user_data.name,
            is_active=True,
            oauth_provider=provider,
            oauth_provider_user_id=user_data.service_user_id,
            oauth_provider_user_domain=user_data.service_user_domain,
            oauth_provider_user_picture_url=user_data.picture_url,
            oauth_provider_user_locale=user_data.service_user_locale,
            oauth_provider_user_profile_url=user_data.user_profile_url,
            app=app_id,
        )
        db.session.add(user)
    else:
        if not user.is_active:
            return return_json_error(Es.BR_USER_NOT_ACTIVE)

        user.user_last_login_date = datetime.datetime.now()
        if (
            user.oauth_provider_user_id == "unknown-manual-insert"
        ):  # Only for anyway@anyway.co.il first login
            user.oauth_provider_user_id = user_data.service_user_id
            user.oauth_provider_user_name = user_data.name
            user.oauth_provider_user_domain = user_data.service_user_domain
            user.oauth_provider_user_picture_url = user_data.picture_url
            user.oauth_provider_user_locale = user_data.service_user_locale
            user.oauth_provider_user_profile_url = user_data.user_profile_url

    db.session.commit()

    redirect_url = BE_CONST.DEFAULT_REDIRECT_URL
    redirect_url_json_base64 = request.args.get("state", type=str)
    if redirect_url_json_base64:
        redirect_url_json = json.loads(base64.b64decode(redirect_url_json_base64.encode("UTF8")))
        redirect_url_to_check = redirect_url_json.get("redirect_url")
        if redirect_url_to_check and is_a_safe_redirect_url(redirect_url_to_check):
            redirect_url = redirect_url_to_check

    login_user(user, True)
    identity_changed.send(current_app._get_current_object(), identity=Identity(user.id))

    return redirect(redirect_url, code=HTTPStatus.FOUND)


# TODO: in the future add pagination if needed
def get_all_users_info(app_id: int) -> Response:
    dict_ret = []
    for user_obj in (
        db.session.query(Users).filter(Users.app == app_id).order_by(Users.user_register_date).all()
    ):
        dict_ret.append(user_obj.serialize_exposed_to_user())
    return jsonify(dict_ret)


@roles_and_grants_accepted(roles=[BE_CONST.Roles2Names.Admins.value], app_id=ANYWAY_APP_ID)
def an_get_all_users_info() -> Response:
    return get_all_users_info(app_id=ANYWAY_APP_ID)


@roles_and_grants_accepted(roles=[BE_CONST.Roles2Names.Admins.value], app_id=SAFETY_DATA_APP_ID)
def sd_get_all_users_info() -> Response:
    return get_all_users_info(app_id=SAFETY_DATA_APP_ID)


def get_user_info(app_id: int) -> Response:
    user_obj = get_current_user()
    if user_obj is None:
        return return_json_error(Es.BR_USER_NOT_FOUND, "")
    if user_obj.app != app_id:
        print(f"User {user_obj.email}:{user_obj.app} found in current app:{app_id}")
        return return_json_error(Es.BR_USER_NOT_FOUND, "")
    return jsonify(user_obj.serialize_exposed_to_user())


@roles_and_grants_accepted(roles=[BE_CONST.Roles2Names.Authenticated.value], app_id=ANYWAY_APP_ID)
def an_get_user_info() -> Response:
    return get_user_info(app_id=ANYWAY_APP_ID)


@roles_and_grants_accepted(
    roles=[BE_CONST.Roles2Names.Authenticated.value], app_id=SAFETY_DATA_APP_ID
)
def sd_get_user_info() -> Response:
    return get_user_info(app_id=SAFETY_DATA_APP_ID)


def is_user_logged_in(app_id: int) -> Response:
    is_logged_in = not current_user.is_anonymous
    if is_logged_in and hasattr(current_user, "app") and current_user.app != app_id:
        is_logged_in = False
    return jsonify({"is_user_logged_in": is_logged_in})


def an_is_user_logged_in() -> Response:
    return is_user_logged_in(app_id=ANYWAY_APP_ID)


def sd_is_user_logged_in() -> Response:
    return is_user_logged_in(app_id=SAFETY_DATA_APP_ID)


def remove_from_role(app_id: int) -> Response:
    return change_user_roles("remove", app_id)


@roles_and_grants_accepted(roles=[BE_CONST.Roles2Names.Admins.value], app_id=ANYWAY_APP_ID)
def an_remove_from_role() -> Response:
    return remove_from_role(app_id=ANYWAY_APP_ID)


@roles_and_grants_accepted(roles=[BE_CONST.Roles2Names.Admins.value], app_id=SAFETY_DATA_APP_ID)
def sd_remove_from_role() -> Response:
    return remove_from_role(app_id=SAFETY_DATA_APP_ID)


def add_to_role(app_id: int) -> Response:
    return change_user_roles("add", app_id)


@roles_and_grants_accepted(roles=[BE_CONST.Roles2Names.Admins.value], app_id=ANYWAY_APP_ID)
def an_add_to_role() -> Response:
    return add_to_role(app_id=ANYWAY_APP_ID)


@roles_and_grants_accepted(roles=[BE_CONST.Roles2Names.Admins.value], app_id=SAFETY_DATA_APP_ID)
def sd_add_to_role() -> Response:
    return add_to_role(app_id=SAFETY_DATA_APP_ID)


def is_input_fields_malformed(request: Request, allowed_fields: typing.List[str]) -> bool:
    # Validate input
    try:
        req_dict = request.json
    except Exception:
        return True
    if not req_dict:
        return True
    for key in req_dict:
        if key not in allowed_fields:
            return True
    return False


def change_user_roles(action: str, app_id: int) -> Response:
    req_dict = request.json
    if not req_dict:
        return return_json_error(Es.BR_FIELD_MISSING)

    role_name = req_dict.get("role")
    if not role_name:
        return return_json_error(Es.BR_NAME_MISSING)
    role = get_role_object(role_name, app_id)
    if role is None:
        return return_json_error(Es.BR_NOT_EXIST, role_name)

    email = req_dict.get("email")
    user = get_user_by_email(db, email, app_id)
    if user is None:
        return return_json_error(Es.BR_USER_NOT_FOUND, email)

    if action == "add":
        # Add user to role
        # Check if user already has this role in this app
        existing = (
            db.session.query(users_to_roles)
            .filter(
                (users_to_roles.c.user_id == user.id)
                & (users_to_roles.c.role_id == role.id)
                & (users_to_roles.c.app == app_id)
            )
            .first()
        )
        if existing:
            return return_json_error(Es.BR_USER_ALREADY_IN, role_name)
        # Insert into users_to_roles with app_id
        db.session.execute(
            users_to_roles.insert().values(  # pylint: disable=no-value-for-parameter
                user_id=user.id, role_id=role.id, app=app_id
            )
        )
        # Refresh user to get updated roles
        db.session.refresh(user)
        # Add user to role in the current instance
        if current_user.email == user.email:
            # g is flask global data
            g.identity.provides.add(RoleNeed(role.name))
    elif action == "remove":
        # Remove user from role
        d = users_to_roles.delete().where(  # noqa pylint: disable=no-value-for-parameter
            (users_to_roles.c.user_id == user.id)
            & (users_to_roles.c.role_id == role.id)
            & (users_to_roles.c.app == app_id)
        )
        result = db.session.execute(d)
        if result.rowcount == 0:
            return return_json_error(Es.BR_USER_NOT_IN, email, role_name)
    db.session.commit()

    return Response(status=HTTPStatus.OK)


def get_role_object(role_name, app_id: int) -> typing.Optional[Roles]:
    role = (
        db.session.query(Roles).filter(Roles.name == role_name).filter(Roles.app == app_id).first()
    )
    return role


def admin_update_user(app_id: int) -> Response:
    allowed_fields = [
        "user_current_email",
        "first_name",
        "last_name",
        "email",
        "phone",
        "user_type",
        "user_url",
        "user_desc",
        "is_user_completed_registration",
    ]

    res = is_input_fields_malformed(request, allowed_fields)
    if res:
        return return_json_error(Es.BR_FIELD_MISSING)
    req_dict = request.json

    user_current_email = req_dict.get("user_current_email")
    user = get_user_by_email(db, user_current_email, app_id)
    if user is None:
        return return_json_error(Es.BR_USER_NOT_FOUND, user_current_email)

    user_db_new_email = req_dict.get("email")
    if not is_a_valid_email(user_db_new_email):
        return return_json_error(Es.BR_BAD_EMAIL)

    phone = req_dict.get("phone")
    if phone and not is_valid_number(phone):
        return return_json_error(Es.BR_BAD_PHONE)

    first_name = req_dict.get("first_name")
    last_name = req_dict.get("last_name")
    user_desc = req_dict.get("user_desc")
    user_type = req_dict.get("user_type")
    user_url = req_dict.get("user_url")
    is_user_completed_registration = req_dict.get("is_user_completed_registration")
    update_user_in_db(
        user,
        first_name,
        last_name,
        phone,
        user_db_new_email,
        user_desc,
        user_type,
        user_url,
        is_user_completed_registration,
    )

    return Response(status=HTTPStatus.OK)


@roles_and_grants_accepted(roles=[BE_CONST.Roles2Names.Admins.value], app_id=ANYWAY_APP_ID)
def an_admin_update_user() -> Response:
    return admin_update_user(app_id=ANYWAY_APP_ID)


@roles_and_grants_accepted(roles=[BE_CONST.Roles2Names.Admins.value], app_id=SAFETY_DATA_APP_ID)
def sd_admin_update_user() -> Response:
    return admin_update_user(app_id=SAFETY_DATA_APP_ID)


# This code is also used as part of the user first registration


def user_update(app_id: int) -> Response:
    allowed_fields = [
        "first_name",
        "last_name",
        "email",
        "phone",
        "user_type",
        "user_url",
        "user_desc",
    ]

    res = is_input_fields_malformed(request, allowed_fields)
    if res:
        return return_json_error(Es.BR_FIELD_MISSING)
    req_dict = request.json

    first_name = req_dict.get("first_name")
    last_name = req_dict.get("last_name")
    if not first_name or not last_name:
        return return_json_error(Es.BR_FIRST_NAME_OR_LAST_NAME_MISSING)

    # If we don't have the user email then we have to get it else only update if the user want.
    tmp_given_user_email = req_dict.get("email")
    user_db_email = get_current_user_email()
    if not user_db_email or tmp_given_user_email:
        if not tmp_given_user_email:
            return return_json_error(Es.BR_NO_EMAIL)

        if not is_a_valid_email(tmp_given_user_email):
            return return_json_error(Es.BR_BAD_EMAIL)

        user_db_email = tmp_given_user_email

    phone = req_dict.get("phone")
    if phone and not is_valid_number(phone):
        return return_json_error(Es.BR_BAD_PHONE)

    user_type = req_dict.get("user_type")
    user_url = req_dict.get("user_url")
    user_desc = req_dict.get("user_desc")

    if current_user.app != app_id:
        return return_json_error(Es.BR_USER_NOT_FOUND, "")

    update_user_in_db(
        current_user,
        first_name,
        last_name,
        phone,
        user_db_email,
        user_desc,
        user_type,
        user_url,
        True,
    )

    return Response(status=HTTPStatus.OK)


@roles_and_grants_accepted(roles=[BE_CONST.Roles2Names.Authenticated.value], app_id=ANYWAY_APP_ID)
def an_user_update() -> Response:
    return user_update(app_id=ANYWAY_APP_ID)


@roles_and_grants_accepted(
    roles=[BE_CONST.Roles2Names.Authenticated.value], app_id=SAFETY_DATA_APP_ID
)
def sd_user_update() -> Response:
    return user_update(app_id=SAFETY_DATA_APP_ID)


def update_user_in_db(
    user: Users,
    first_name: str,
    last_name: str,
    phone: str,
    user_db_email: str,
    user_desc: str,
    user_type: str,
    user_url: str,
    is_user_completed_registration: bool,
) -> None:
    user.first_name = first_name
    user.last_name = last_name
    user.email = user_db_email
    user.phone = phone
    user.user_type = user_type
    user.user_url = user_url
    user.user_desc = user_desc
    user.is_user_completed_registration = is_user_completed_registration
    db.session.commit()


def change_user_active_mode(app_id: int) -> Response:
    req_dict = request.json
    if not req_dict:
        return return_json_error(Es.BR_FIELD_MISSING)

    email = req_dict.get("email")
    user = get_user_by_email(db, email, app_id)
    if user is None:
        return return_json_error(Es.BR_USER_NOT_FOUND, email)

    mode = req_dict.get("mode")
    if mode is None:
        return return_json_error(Es.BR_NO_MODE)

    if type(mode) != bool:
        return return_json_error(Es.BR_BAD_MODE)

    user.is_active = mode
    db.session.commit()
    return Response(status=HTTPStatus.OK)


@roles_and_grants_accepted(roles=[BE_CONST.Roles2Names.Admins.value], app_id=ANYWAY_APP_ID)
def an_change_user_active_mode() -> Response:
    return change_user_active_mode(app_id=ANYWAY_APP_ID)


@roles_and_grants_accepted(roles=[BE_CONST.Roles2Names.Admins.value], app_id=SAFETY_DATA_APP_ID)
def sd_change_user_active_mode() -> Response:
    return change_user_active_mode(app_id=SAFETY_DATA_APP_ID)


def add_role(app_id: int) -> Response:
    req_dict = request.json
    if not req_dict:
        return return_json_error(Es.BR_FIELD_MISSING)

    name = req_dict.get("name")
    if not name:
        return return_json_error(Es.BR_NAME_MISSING)

    if not is_a_valid_role_name(name):
        return return_json_error(Es.BR_BAD_NAME)

    role = db.session.query(Roles).filter(Roles.name == name).filter(Roles.app == app_id).first()
    if role:
        return return_json_error(Es.BR_EXIST)

    description = req_dict.get("description")
    if not description:
        return return_json_error(Es.BR_DESCRIPTION_MISSING)

    if not is_a_valid_role_description(description):
        return return_json_error(Es.BR_BAD_DESCRIPTION)

    role = Roles(
        name=name, description=description, create_date=datetime.datetime.now(), app=app_id
    )
    db.session.add(role)
    db.session.commit()
    return Response(status=HTTPStatus.OK)


@roles_and_grants_accepted(roles=[BE_CONST.Roles2Names.Admins.value], app_id=ANYWAY_APP_ID)
def an_add_role() -> Response:
    return add_role(app_id=ANYWAY_APP_ID)


@roles_and_grants_accepted(roles=[BE_CONST.Roles2Names.Admins.value], app_id=SAFETY_DATA_APP_ID)
def sd_add_role() -> Response:
    return add_role(app_id=SAFETY_DATA_APP_ID)


def is_a_valid_role_name(name: str) -> bool:
    if len(name) < 2 or len(name) >= Roles.name.type.length:
        return False

    match = re.match("^[a-zA-Z0-9_-]+$", name)
    if not match:
        return False

    return True


def is_a_valid_role_description(name: str) -> bool:
    if len(name) >= Roles.description.type.length:
        return False

    return True


def get_roles_list(app_id: int) -> Response:
    roles_list = db.session.query(Roles).filter(Roles.app == app_id).all()
    send_list = [
        {"id": role.id, "name": role.name, "description": role.description} for role in roles_list
    ]

    return Response(
        response=json.dumps(send_list), status=HTTPStatus.OK, mimetype="application/json"
    )


@roles_and_grants_accepted(roles=[BE_CONST.Roles2Names.Admins.value], app_id=ANYWAY_APP_ID)
def an_get_roles_list() -> Response:
    return get_roles_list(app_id=ANYWAY_APP_ID)


@roles_and_grants_accepted(roles=[BE_CONST.Roles2Names.Admins.value], app_id=SAFETY_DATA_APP_ID)
def sd_get_roles_list() -> Response:
    return get_roles_list(app_id=SAFETY_DATA_APP_ID)


def get_organization_list(app_id: int) -> Response:
    orgs_list = db.session.query(Organization).filter(Organization.app == app_id).all()
    send_list = [org.name for org in orgs_list]

    return Response(
        response=json.dumps(send_list), status=HTTPStatus.OK, mimetype="application/json"
    )


@roles_and_grants_accepted(roles=[BE_CONST.Roles2Names.Admins.value], app_id=ANYWAY_APP_ID)
def an_get_organization_list() -> Response:
    return get_organization_list(app_id=ANYWAY_APP_ID)


@roles_and_grants_accepted(roles=[BE_CONST.Roles2Names.Admins.value], app_id=SAFETY_DATA_APP_ID)
def sd_get_organization_list() -> Response:
    return get_organization_list(app_id=SAFETY_DATA_APP_ID)


def add_organization(name: str, app_id: int) -> Response:
    if not name:
        return return_json_error(Es.BR_FIELD_MISSING)

    org = (
        db.session.query(Organization)
        .filter(Organization.name == name)
        .filter(Organization.app == app_id)
        .first()
    )
    if not org:
        org = Organization(name=name, create_date=datetime.datetime.now(), app=app_id)
        db.session.add(org)
        db.session.commit()

    return Response(status=HTTPStatus.OK)


@roles_and_grants_accepted(roles=[BE_CONST.Roles2Names.Admins.value], app_id=ANYWAY_APP_ID)
def an_add_organization(name: str) -> Response:
    return add_organization(name, app_id=ANYWAY_APP_ID)


@roles_and_grants_accepted(roles=[BE_CONST.Roles2Names.Admins.value], app_id=SAFETY_DATA_APP_ID)
def sd_add_organization(name: str) -> Response:
    return add_organization(name, app_id=SAFETY_DATA_APP_ID)


def update_user_org(user_email: str, org_name: str, app_id: int) -> Response:
    user = get_user_by_email(db, user_email, app_id)
    if user is None:
        return return_json_error(Es.BR_USER_NOT_FOUND, user_email)

    # Remove all existing organization memberships for this user in this app
    db.session.execute(
        users_to_organizations.delete().where(  # pylint: disable=no-value-for-parameter
            (users_to_organizations.c.user_id == user.id) & (users_to_organizations.c.app == app_id)
        )
    )

    if org_name is not None:
        try:
            org_obj = (
                db.session.query(Organization)
                .filter(Organization.name == org_name)
                .filter(Organization.app == app_id)
                .one()
            )
        except NoResultFound:
            return return_json_error(Es.BR_ORG_NOT_FOUND)
        # Insert into users_to_organizations with app_id
        db.session.execute(
            users_to_organizations.insert().values(  # pylint: disable=no-value-for-parameter
                user_id=user.id, organization_id=org_obj.id, app=app_id
            )
        )

    db.session.commit()
    return Response(status=HTTPStatus.OK)


@roles_and_grants_accepted(roles=[BE_CONST.Roles2Names.Admins.value], app_id=ANYWAY_APP_ID)
def an_update_user_org(user_email: str, org_name: str) -> Response:
    return update_user_org(user_email, org_name, app_id=ANYWAY_APP_ID)


@roles_and_grants_accepted(roles=[BE_CONST.Roles2Names.Admins.value], app_id=SAFETY_DATA_APP_ID)
def sd_update_user_org(user_email: str, org_name: str) -> Response:
    return update_user_org(user_email, org_name, app_id=SAFETY_DATA_APP_ID)


def delete_user(email: str, app_id: int) -> Response:
    user = get_user_by_email(db, email, app_id)
    if user is None:
        return return_json_error(Es.BR_USER_NOT_FOUND, email)

    # Delete user roles for this app
    db.session.execute(
        users_to_roles.delete().where(  # pylint: disable=no-value-for-parameter
            (users_to_roles.c.user_id == user.id) & (users_to_roles.c.app == app_id)
        )
    )

    # Delete user organizations membership for this app
    db.session.execute(
        users_to_organizations.delete().where(  # pylint: disable=no-value-for-parameter
            (users_to_organizations.c.user_id == user.id) & (users_to_organizations.c.app == app_id)
        )
    )

    db.session.delete(user)
    db.session.commit()
    return Response(status=HTTPStatus.OK)


@roles_and_grants_accepted(roles=[BE_CONST.Roles2Names.Admins.value], app_id=ANYWAY_APP_ID)
def an_delete_user(email: str) -> Response:
    return delete_user(email, app_id=ANYWAY_APP_ID)


@roles_and_grants_accepted(roles=[BE_CONST.Roles2Names.Admins.value], app_id=SAFETY_DATA_APP_ID)
def sd_delete_user(email: str) -> Response:
    return delete_user(email, app_id=SAFETY_DATA_APP_ID)


def is_a_valid_grant_name(name: str) -> bool:
    if len(name) < 2 or len(name) >= Grant.name.type.length:
        return False

    match = re.match("^[a-zA-Z0-9_-]+$", name)
    if not match:
        return False

    return True


def is_a_valid_grant_description(description: str) -> bool:
    if description and len(description) >= Grant.description.type.length:
        return False

    return True


def get_grant_object(grant_name: str, app_id: int):
    grant = (
        db.session.query(Grant).filter(Grant.name == grant_name).filter(Grant.app == app_id).first()
    )
    return grant


def add_grant(app_id: int) -> Response:
    req_dict = request.json
    if not req_dict:
        return return_json_error(Es.BR_FIELD_MISSING)

    name = req_dict.get("name")
    if not name:
        return return_json_error(Es.BR_NAME_MISSING)

    if not is_a_valid_grant_name(name):
        return return_json_error(Es.BR_BAD_NAME)

    grant = db.session.query(Grant).filter(Grant.name == name).filter(Grant.app == app_id).first()
    if grant:
        return return_json_error(Es.BR_EXIST)

    description = req_dict.get("description")
    if not description:
        return return_json_error(Es.BR_DESCRIPTION_MISSING)

    if not is_a_valid_grant_description(description):
        return return_json_error(Es.BR_BAD_DESCRIPTION)

    grant = Grant(
        name=name, description=description, create_date=datetime.datetime.now(), app=app_id
    )
    db.session.add(grant)
    db.session.commit()
    return Response(status=HTTPStatus.OK)


@roles_and_grants_accepted(roles=[BE_CONST.Roles2Names.Admins.value], app_id=SAFETY_DATA_APP_ID)
def sd_add_grant() -> Response:
    return add_grant(app_id=SAFETY_DATA_APP_ID)


def change_user_grants(action: str, app_id: int) -> Response:
    req_dict = request.json
    if not req_dict:
        return return_json_error(Es.BR_FIELD_MISSING)

    grant_name = req_dict.get("grant")
    if not grant_name:
        return return_json_error(Es.BR_NAME_MISSING)
    grant = get_grant_object(grant_name, app_id)
    if grant is None:
        return return_json_error(Es.BR_NOT_EXIST, grant_name)

    email = req_dict.get("email")
    user = get_user_by_email(db, email, app_id)
    if user is None:
        return return_json_error(Es.BR_USER_NOT_FOUND, email)

    if action == "add":
        # Add user to grant
        # Check if user already has this grant in this app
        existing = (
            db.session.query(users_to_grants)
            .filter(
                (users_to_grants.c.user_id == user.id)
                & (users_to_grants.c.grant_id == grant.id)
                & (users_to_grants.c.app == app_id)
            )
            .first()
        )
        if existing:
            return return_json_error(Es.BR_USER_ALREADY_IN, grant_name)
        # Insert into users_to_grants with app_id
        db.session.execute(
            users_to_grants.insert().values(  # pylint: disable=no-value-for-parameter
                user_id=user.id, grant_id=grant.id, app=app_id
            )
        )
        # Refresh user to get updated grants
        db.session.refresh(user)
    elif action == "remove":
        # Remove user from grant
        d = users_to_grants.delete().where(  # noqa pylint: disable=no-value-for-parameter
            (users_to_grants.c.user_id == user.id)
            & (users_to_grants.c.grant_id == grant.id)
            & (users_to_grants.c.app == app_id)
        )
        result = db.session.execute(d)
        if result.rowcount == 0:
            return return_json_error(Es.BR_USER_NOT_IN, email, grant_name)
    db.session.commit()

    return Response(status=HTTPStatus.OK)


def add_to_grant(app_id: int) -> Response:
    return change_user_grants("add", app_id)


@roles_and_grants_accepted(roles=[BE_CONST.Roles2Names.Admins.value], app_id=SAFETY_DATA_APP_ID)
def sd_add_to_grant() -> Response:
    return add_to_grant(app_id=SAFETY_DATA_APP_ID)


def remove_from_grant(app_id: int) -> Response:
    return change_user_grants("remove", app_id)


@roles_and_grants_accepted(roles=[BE_CONST.Roles2Names.Admins.value], app_id=SAFETY_DATA_APP_ID)
def sd_remove_from_grant() -> Response:
    return remove_from_grant(app_id=SAFETY_DATA_APP_ID)


def delete_grant(app_id: int) -> Response:
    req_dict = request.json
    if not req_dict:
        return return_json_error(Es.BR_FIELD_MISSING)

    grant_name = req_dict.get("grant")
    if not grant_name:
        return return_json_error(Es.BR_NAME_MISSING)

    grant = get_grant_object(grant_name, app_id)
    if grant is None:
        return return_json_error(Es.BR_NOT_EXIST, grant_name)

    # Delete all user-grant associations for this grant in this app
    db.session.execute(
        users_to_grants.delete().where(  # pylint: disable=no-value-for-parameter
            (users_to_grants.c.grant_id == grant.id) & (users_to_grants.c.app == app_id)
        )
    )

    db.session.delete(grant)
    db.session.commit()
    return Response(status=HTTPStatus.OK)


@roles_and_grants_accepted(roles=[BE_CONST.Roles2Names.Admins.value], app_id=SAFETY_DATA_APP_ID)
def sd_delete_grant() -> Response:
    return delete_grant(app_id=SAFETY_DATA_APP_ID)


def get_grants_list(app_id: int) -> Response:
    grants_list = db.session.query(Grant).filter(Grant.app == app_id).all()
    send_list = [
        {"id": grant.id, "name": grant.name, "description": grant.description}
        for grant in grants_list
    ]

    return Response(
        response=json.dumps(send_list), status=HTTPStatus.OK, mimetype="application/json"
    )


@roles_and_grants_accepted(roles=[BE_CONST.Roles2Names.Admins.value], app_id=SAFETY_DATA_APP_ID)
def sd_get_grants_list() -> Response:
    return get_grants_list(app_id=SAFETY_DATA_APP_ID)


@roles_and_grants_accepted(
    roles=[BE_CONST.Roles2Names.Admins.value],
    grants=["test_grant"],
    app_id=SAFETY_DATA_APP_ID,
    need_all_permissions=False,
)
def sd_test_grant_and_admin_endpoint() -> Response:
    """Test endpoint that requires both admin role and test_grant grant."""
    return jsonify({"message": "Access granted: user has both admin role and test_grant grant"})


# CLI Helper Functions for Safety Data User Management


def add_safety_data_users(emails: typing.List[str]) -> dict:
    """
    Add one or more Safety Data users.

    Args:
        emails: List of email addresses to add

    Returns:
        Dictionary with keys: 'added', 'already_exists', 'invalid_email', 'failed'
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from anyway.config import SQLALCHEMY_DATABASE_URI

    engine = create_engine(SQLALCHEMY_DATABASE_URI, echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()

    summary = {"added": [], "already_exists": [], "invalid_email": [], "failed": []}

    for email in emails:
        # Validate email structure
        if not is_a_valid_email(email):
            logging.warning(f"Invalid email format: {email}")
            summary["invalid_email"].append(email)
            continue

        try:
            # Check if user already exists
            existing_user = (
                session.query(Users)
                .filter(Users.email == email, Users.app == SAFETY_DATA_APP_ID)
                .first()
            )

            if existing_user:
                logging.info(f"User already exists: {email}")
                summary["already_exists"].append(email)
                continue

            # Create new user following the pattern from add_builtin_safety_data_admin
            user = Users(
                user_register_date=datetime.datetime.now(),
                user_last_login_date=datetime.datetime.now(),
                email=email,
                oauth_provider_user_name=email,
                is_active=True,
                oauth_provider="manual",
                is_user_completed_registration=True,
                oauth_provider_user_id=f"manual-{email}",
                app=SAFETY_DATA_APP_ID,
            )
            session.add(user)
            session.commit()
            logging.info(f"Successfully added user: {email}")
            summary["added"].append(email)

        except Exception as e:
            session.rollback()
            logging.error(f"Failed to add user {email}: {e}")
            summary["failed"].append({"email": email, "error": str(e)})

    session.close()
    return summary


def remove_safety_data_user(email: str) -> dict:
    """
    Remove a Safety Data user.

    Args:
        email: Email address of the user to remove

    Returns:
        Dictionary with keys: 'removed', 'not_found', 'failed'
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from anyway.config import SQLALCHEMY_DATABASE_URI

    engine = create_engine(SQLALCHEMY_DATABASE_URI, echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()

    summary = {"removed": [], "not_found": [], "failed": []}

    try:
        user = (
            session.query(Users)
            .filter(Users.email == email, Users.app == SAFETY_DATA_APP_ID)
            .first()
        )

        if not user:
            logging.warning(f"User not found: {email}")
            summary["not_found"].append(email)
        else:
            session.delete(user)
            session.commit()
            logging.info(f"Successfully removed user: {email}")
            summary["removed"].append(email)

    except Exception as e:
        session.rollback()
        logging.error(f"Failed to remove user {email}: {e}")
        summary["failed"].append({"email": email, "error": str(e)})

    session.close()
    return summary


def add_grant_to_safety_data_user(email: str, grant_name: str) -> dict:
    """
    Add a grant to a Safety Data user.

    Args:
        email: Email address of the user
        grant_name: Name of the grant to add

    Returns:
        Dictionary with keys: 'added', 'already_has_grant', 'user_not_found', 'grant_not_found', 'failed'
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from anyway.config import SQLALCHEMY_DATABASE_URI

    engine = create_engine(SQLALCHEMY_DATABASE_URI, echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()

    summary = {
        "added": [],
        "already_has_grant": [],
        "user_not_found": [],
        "grant_not_found": [],
        "failed": [],
    }

    try:
        # Find user
        user = (
            session.query(Users)
            .filter(Users.email == email, Users.app == SAFETY_DATA_APP_ID)
            .first()
        )

        if not user:
            logging.warning(f"User not found: {email}")
            summary["user_not_found"].append(email)
            session.close()
            return summary

        # Find grant
        grant = (
            session.query(Grant)
            .filter(Grant.name == grant_name, Grant.app == SAFETY_DATA_APP_ID)
            .first()
        )

        if not grant:
            logging.warning(f"Grant not found: {grant_name}")
            summary["grant_not_found"].append(grant_name)
            session.close()
            return summary

        # Check if user already has this grant
        existing = (
            session.query(users_to_grants)
            .filter(
                users_to_grants.c.user_id == user.id,
                users_to_grants.c.grant_id == grant.id,
                users_to_grants.c.app == SAFETY_DATA_APP_ID,
            )
            .first()
        )

        if existing:
            logging.info(f"User {email} already has grant {grant_name}")
            summary["already_has_grant"].append({"email": email, "grant": grant_name})
        else:
            # Add grant to user following the pattern from add_builtin_safety_data_admin
            insert_stmt = users_to_grants.insert().values(  # pylint: disable=no-value-for-parameter
                user_id=user.id,
                grant_id=grant.id,
                app=SAFETY_DATA_APP_ID,
                create_date=datetime.datetime.now(),
            )
            session.execute(insert_stmt)
            session.commit()
            logging.info(f"Successfully added grant {grant_name} to user {email}")
            summary["added"].append({"email": email, "grant": grant_name})

    except Exception as e:
        session.rollback()
        logging.error(f"Failed to add grant {grant_name} to user {email}: {e}")
        summary["failed"].append({"email": email, "grant": grant_name, "error": str(e)})

    session.close()
    return summary


def remove_grant_from_safety_data_user(email: str, grant_name: str) -> dict:
    """
    Remove a grant from a Safety Data user.

    Args:
        email: Email address of the user
        grant_name: Name of the grant to remove

    Returns:
        Dictionary with keys: 'removed', 'does_not_have_grant', 'user_not_found', 'grant_not_found', 'failed'
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from anyway.config import SQLALCHEMY_DATABASE_URI

    engine = create_engine(SQLALCHEMY_DATABASE_URI, echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()

    summary = {
        "removed": [],
        "does_not_have_grant": [],
        "user_not_found": [],
        "grant_not_found": [],
        "failed": [],
    }

    try:
        # Find user
        user = (
            session.query(Users)
            .filter(Users.email == email, Users.app == SAFETY_DATA_APP_ID)
            .first()
        )

        if not user:
            logging.warning(f"User not found: {email}")
            summary["user_not_found"].append(email)
            session.close()
            return summary

        # Find grant
        grant = (
            session.query(Grant)
            .filter(Grant.name == grant_name, Grant.app == SAFETY_DATA_APP_ID)
            .first()
        )

        if not grant:
            logging.warning(f"Grant not found: {grant_name}")
            summary["grant_not_found"].append(grant_name)
            session.close()
            return summary

        # Delete grant from user
        delete_stmt = users_to_grants.delete().where(  # pylint: disable=no-value-for-parameter
            (users_to_grants.c.user_id == user.id)
            & (users_to_grants.c.grant_id == grant.id)
            & (users_to_grants.c.app == SAFETY_DATA_APP_ID)
        )
        result = session.execute(delete_stmt)

        if result.rowcount == 0:
            logging.info(f"User {email} does not have grant {grant_name}")
            summary["does_not_have_grant"].append({"email": email, "grant": grant_name})
        else:
            session.commit()
            logging.info(f"Successfully removed grant {grant_name} from user {email}")
            summary["removed"].append({"email": email, "grant": grant_name})

    except Exception as e:
        session.rollback()
        logging.error(f"Failed to remove grant {grant_name} from user {email}: {e}")
        summary["failed"].append({"email": email, "grant": grant_name, "error": str(e)})

    session.close()
    return summary
