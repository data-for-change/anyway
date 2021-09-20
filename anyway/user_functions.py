import typing
from typing import Optional

from flask import Request
from flask_login import current_user
from flask_principal import RoleNeed, Permission
from flask_sqlalchemy import SQLAlchemy

from anyway.models import Users, RolesToAPI, Roles


def get_user_by_email(db: SQLAlchemy, email: str) -> Users:
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


def is_current_user_have_permission(db: SQLAlchemy, request: Request) -> bool:
    allowed_roles = db.session.query(RolesToAPI).filter(RolesToAPI.api_name == request.path).all()
    for role_to_api_obj in allowed_roles:
        role = role_id_to_role_obj(db, role_to_api_obj.role_id)
        role_prem = Permission(RoleNeed(role.name))
        if role_prem.can():
            return True
    return False


def role_id_to_role_obj(db: SQLAlchemy, role_id: int) -> typing.Optional[Roles]:
    return db.session.query(Roles).filter(Roles.id == role_id).first()
