import base64
import datetime
import json
import logging
import re
import typing
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
from anyway.models import Organization, Roles, Users, users_to_roles
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

# Copied and modified from flask-security
def roles_accepted(*roles):
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


def oauth_authorize(provider: str) -> Response:
    if provider != "google":
        return return_json_error(Es.BR_ONLY_SUPPORT_GOOGLE)

    if not current_user.is_anonymous:
        return return_json_error(Es.BR_USER_ALREADY_LOGGED_IN)

    redirect_url_from_url = request.args.get("redirect_url", type=str)
    redirect_url = BE_CONST.DEFAULT_REDIRECT_URL
    if redirect_url_from_url and is_a_safe_redirect_url(redirect_url_from_url):
        redirect_url = redirect_url_from_url

    oauth = OAuthSignIn.get_provider(provider)
    return oauth.authorize(redirect_url=redirect_url)


def logout() -> Response:
    logout_user()
    identity_changed.send(current_app._get_current_object(), identity=AnonymousIdentity())
    return Response(status=HTTPStatus.OK)


def oauth_callback(provider: str) -> Response:
    if provider != "google":
        return return_json_error(Es.BR_ONLY_SUPPORT_GOOGLE)

    oauth = OAuthSignIn.get_provider(provider)
    user_data: UserData = oauth.callback()
    if not user_data or not user_data.service_user_id:
        return return_json_error(Es.BR_NO_USER_ID)

    user = None
    try:
        user = (
            db.session.query(Users)
            .filter_by(oauth_provider=provider, oauth_provider_user_id=user_data.service_user_id)
            .one()
        )
    except (NoResultFound, MultipleResultsFound):
        try:
            user = (
                db.session.query(Users)
                .filter_by(oauth_provider=provider, email=user_data.email)
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
@roles_accepted(BE_CONST.Roles2Names.Admins.value)
def get_all_users_info() -> Response:
    dict_ret = []
    for user_obj in db.session.query(Users).order_by(Users.user_register_date).all():
        dict_ret.append(user_obj.serialize_exposed_to_user())
    return jsonify(dict_ret)


@roles_accepted(BE_CONST.Roles2Names.Authenticated.value)
def get_user_info() -> Response:
    user_obj = get_current_user()
    return jsonify(user_obj.serialize_exposed_to_user())


@roles_accepted(BE_CONST.Roles2Names.Admins.value)
def remove_from_role() -> Response:
    return change_user_roles("remove")


@roles_accepted(BE_CONST.Roles2Names.Admins.value)
def add_to_role() -> Response:
    return change_user_roles("add")


def is_input_fields_malformed(request: Request, allowed_fields: typing.List[str]) -> bool:
    # Validate input
    req_dict = request.json
    if not req_dict:
        return True
    for key in req_dict:
        if key not in allowed_fields:
            return True
    return False


def change_user_roles(action: str) -> Response:
    req_dict = request.json
    if not req_dict:
        return return_json_error(Es.BR_FIELD_MISSING)

    role_name = req_dict.get("role")
    if not role_name:
        return return_json_error(Es.BR_ROLE_NAME_MISSING)
    role = get_role_object(role_name)
    if role is None:
        return return_json_error(Es.BR_ROLE_NOT_EXIST, role_name)

    email = req_dict.get("email")
    user = get_user_by_email(db, email)
    if user is None:
        return return_json_error(Es.BR_USER_NOT_FOUND, email)

    if action == "add":
        # Add user to role
        for user_role in user.roles:
            if role.name == user_role.name:
                return return_json_error(Es.BR_USER_ALREADY_IN_ROLE, role_name)
        user.roles.append(role)
        # Add user to role in the current instance
        if current_user.email == user.email:
            # g is flask global data
            g.identity.provides.add(RoleNeed(role.name))
    elif action == "remove":
        # Remove user from role
        removed = False
        for user_role in user.roles:
            if role.name == user_role.name:
                d = users_to_roles.delete().where(  # noqa pylint: disable=no-value-for-parameter
                    (users_to_roles.c.user_id == user.id) & (users_to_roles.c.role_id == role.id)
                )
                db.session.execute(d)
                removed = True
        if not removed:
            return return_json_error(Es.BR_USER_NOT_IN_ROLE, email, role_name)
    db.session.commit()

    return Response(status=HTTPStatus.OK)


def get_role_object(role_name):
    role = db.session.query(Roles).filter(Roles.name == role_name).one()
    return role


@roles_accepted(BE_CONST.Roles2Names.Admins.value)
def admin_update_user() -> Response:
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
    user = get_user_by_email(db, user_current_email)
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


# This code is also used as part of the user first registration


@roles_accepted(BE_CONST.Roles2Names.Authenticated.value)
def user_update() -> Response:
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


@roles_accepted(BE_CONST.Roles2Names.Admins.value)
def change_user_active_mode() -> Response:
    req_dict = request.json
    if not req_dict:
        return return_json_error(Es.BR_FIELD_MISSING)

    email = req_dict.get("email")
    user = get_user_by_email(db, email)
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


@roles_accepted(BE_CONST.Roles2Names.Admins.value)
def add_role() -> Response:
    req_dict = request.json
    if not req_dict:
        return return_json_error(Es.BR_FIELD_MISSING)

    name = req_dict.get("name")
    if not name:
        return return_json_error(Es.BR_ROLE_NAME_MISSING)

    if not is_a_valid_role_name(name):
        return return_json_error(Es.BR_BAD_ROLE_NAME)

    role = db.session.query(Roles).filter(Roles.name == name).first()
    if role:
        return return_json_error(Es.BR_ROLE_EXIST)

    description = req_dict.get("description")
    if not description:
        return return_json_error(Es.BR_ROLE_DESCRIPTION_MISSING)

    if not is_a_valid_role_description(description):
        return return_json_error(Es.BR_BAD_ROLE_DESCRIPTION)

    role = Roles(name=name, description=description, create_date=datetime.datetime.now())
    db.session.add(role)
    db.session.commit()
    return Response(status=HTTPStatus.OK)


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


@roles_accepted(BE_CONST.Roles2Names.Admins.value)
def get_roles_list() -> Response:
    roles_list = db.session.query(Roles).all()
    send_list = [
        {"id": role.id, "name": role.name, "description": role.description} for role in roles_list
    ]

    return Response(
        response=json.dumps(send_list),
        status=HTTPStatus.OK,
        mimetype="application/json",
    )


@roles_accepted(BE_CONST.Roles2Names.Admins.value)
def get_organization_list() -> Response:
    orgs_list = db.session.query(Organization).all()
    send_list = [org.name for org in orgs_list]

    return Response(
        response=json.dumps(send_list),
        status=HTTPStatus.OK,
        mimetype="application/json",
    )


@roles_accepted(BE_CONST.Roles2Names.Admins.value)
def add_organization(name: str) -> Response:
    if not name:
        return return_json_error(Es.BR_FIELD_MISSING)

    org = db.session.query(Organization).filter(Organization.name == name).first()
    if not org:
        org = Organization(name=name, create_date=datetime.datetime.now())
        db.session.add(org)
        db.session.commit()

    return Response(status=HTTPStatus.OK)


@roles_accepted(BE_CONST.Roles2Names.Admins.value)
def update_user_org(user_email: str, org_name: str) -> Response:
    user = get_user_by_email(db, user_email)
    if user is None:
        return return_json_error(Es.BR_USER_NOT_FOUND, user_email)

    if org_name is not None:
        try:
            org_obj = db.session.query(Organization).filter(Organization.name == org_name).one()
        except NoResultFound:
            return return_json_error(Es.BR_ORG_NOT_FOUND)
        user.organizations = [org_obj]
    else:
        user.organizations = []

    db.session.commit()
    return Response(status=HTTPStatus.OK)
