from flask import session, redirect
from flask import request
from .models import User
from functools import wraps

def set_user(user):
    session["user"] = user.id

def get_user():
    if "user" in session:
        return User.query.filter(User.id == session["user"]).scalar()
    else:
        return None

def user_optional(handler):

    @wraps(handler)
    def check_login(*args, **kwargs):
        return handler(*args, **kwargs)

    return check_login

def user_required(handler):

    @wraps(handler)
    def check_login(*args, **kwargs):
        user = get_user()
        if not user:
            session["last_page_before_login"] = request.path + "?" + request.query_string
            return redirect("/")
        else:
            return handler(*args, **kwargs)

        return check_login
