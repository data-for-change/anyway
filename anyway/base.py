from functools import wraps

from flask import current_app, session, Response
from flask_login import COOKIE_NAME, COOKIE_SECURE, COOKIE_HTTPONLY, COOKIE_DURATION, encode_cookie
from flask_login._compat import text_type
from datetime import timedelta, datetime


# TODO: Do we want to delete it?
def user_optional(handler):
    @wraps(handler)
    def check_login(*args, **kwargs):
        return handler(*args, **kwargs)

    return check_login

# Here I copied 2 function from flask_login/login_manager.py to preform a temporary fix for the Cross-origin problem:
# Flask-Login version 0.5.0 (the current version in the pip repo) doesn't support Cross-origin for
# the remember me cookie(setting the samesite to "none"), there is a fix for that in Flask-Login main branch
# from Feb 12, 2020 (pull request https://github.com/maxcountryman/flask-login/pull/453) but the version in pip is from
# Feb 9, 2020.
# I send an email to the repository owner with a request to release a new version.


# Based on flask_login/login_manager.py
def _set_cookie_hijack(response: Response) -> None:
    # cookie settings
    config = current_app.config
    cookie_name = config.get("REMEMBER_COOKIE_NAME", COOKIE_NAME)
    domain = config.get("REMEMBER_COOKIE_DOMAIN")
    path = config.get("REMEMBER_COOKIE_PATH", "/")
    secure = config.get("REMEMBER_COOKIE_SECURE", COOKIE_SECURE)
    httponly = config.get("REMEMBER_COOKIE_HTTPONLY", COOKIE_HTTPONLY)

    if "_remember_seconds" in session:
        duration = timedelta(seconds=session["_remember_seconds"])
    else:
        duration = config.get("REMEMBER_COOKIE_DURATION", COOKIE_DURATION)

    # prepare data
    data = encode_cookie(text_type(session["_user_id"]))
    if isinstance(duration, int):
        duration = timedelta(seconds=duration)
    try:
        expires = datetime.utcnow() + duration
    except TypeError:
        raise Exception(
            "REMEMBER_COOKIE_DURATION must be a "
            + "datetime.timedelta, instead got: {0}".format(duration)
        )

    # actually set it
    response.set_cookie(
        cookie_name,
        value=data,
        expires=expires,
        domain=domain,
        path=path,
        secure=secure,
        httponly=httponly,
        samesite="none",
    )


# Based on flask_login/login_manager.py
def _clear_cookie_hijack(response: Response) -> None:
    config = current_app.config
    cookie_name = config.get("REMEMBER_COOKIE_NAME", COOKIE_NAME)
    domain = config.get("REMEMBER_COOKIE_DOMAIN")
    path = config.get("REMEMBER_COOKIE_PATH", "/")
    secure = config.get("REMEMBER_COOKIE_SECURE", COOKIE_SECURE)
    httponly = config.get("REMEMBER_COOKIE_HTTPONLY", COOKIE_HTTPONLY)
    response.set_cookie(
        cookie_name,
        expires=0,
        max_age=0,
        domain=domain,
        path=path,
        secure=secure,
        httponly=httponly,
        samesite="none",
    )
