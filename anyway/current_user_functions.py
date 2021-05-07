from typing import Optional

from flask_login import current_user

from anyway.models import Users


def get_current_user_email() -> Optional[str]:
    if current_user.is_anonymous:
        return None
    return current_user.email


def get_current_user() -> Optional[Users]:
    if current_user.is_anonymous:
        return None
    return current_user
