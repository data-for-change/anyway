import typing
from flask_login import current_user

from anyway.app_and_db import db
from anyway.models import UserOAuth


def get_current_user_email() -> typing.Optional[str]:
    cur_id = current_user.get_id()
    cur_user = (
        db.session.query(UserOAuth)
        .with_entities(UserOAuth.email)
        .filter(UserOAuth.id == cur_id)
        .first()
    )
    if cur_user is not None:
        return cur_user.email
    return None


def get_current_user() -> UserOAuth:
    cur_id = current_user.get_id()
    cur_user = db.session.query(UserOAuth).filter(UserOAuth.id == cur_id).first()
    return cur_user
