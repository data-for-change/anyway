from typing import Optional

from flask_login import current_user
from flask_sqlalchemy import SQLAlchemy

from anyway.models import Users


def get_user_by_email(db: SQLAlchemy, email: str) -> Optional[Users]:
    if not email:
        return None
    user = db.session.query(Users).filter(Users.email == email).first()
    return user


def get_current_user_email() -> Optional[str]:
    if current_user.is_anonymous:
        return None
    return current_user.email


def get_current_user() -> Optional[Users]:
    if current_user.is_anonymous:
        return None
    return current_user
