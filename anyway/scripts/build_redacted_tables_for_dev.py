from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from anyway.config import SQLALCHEMY_DATABASE_URI
from anyway.models import Users, users_to_roles, Roles

"""This is a separated script that create the User system tables and all the default data in them.
To use the script you need:
1.Have a running docker environment of Anyway
2.Set the following environment variables for the script:
SERVER_ENV=dev
DATABASE_URL=postgresql://{username}:{password}@{ip}:{port}/anyway
FLASK_ENV=development
3.Run this script
"""
ADMIN_EMAIL = "anyway@anyway.co.il"


def create_db():
    engine = create_engine(SQLALCHEMY_DATABASE_URI, echo=False)
    Users.metadata.create_all(engine)

    role_admins = Roles(
        name="admins",
        description="This is the default admin role.",
        create_date=datetime.now(),
    )
    Session = sessionmaker(bind=engine)
    session = Session()
    admin_role = (
        session.query(Roles).with_entities(Roles.name).filter(Roles.name == "admins").first()
    )
    if admin_role is None:
        session.add(role_admins)
    user = session.query(Users).filter(Users.email == ADMIN_EMAIL).first()
    if user is None:
        user = Users(
            user_register_date=datetime.now(),
            user_last_login_date=datetime.now(),
            email=ADMIN_EMAIL,
            oauth_provider_user_name=ADMIN_EMAIL,
            is_active=True,
            oauth_provider="google",
            is_user_completed_registration=True,
            oauth_provider_user_id="unknown-manual-insert",
        )
        session.add(user)

    user_id = (
        session.query(Users).with_entities(Users.id).filter(Users.email == ADMIN_EMAIL).first()
    )

    role_id = session.query(Roles).with_entities(Roles.id).filter(Roles.name == "admins").first()
    admin_role = (
        session.query(users_to_roles)
        .filter(users_to_roles.columns.user_id == user.id)
        .filter(users_to_roles.columns.role_id == role_id)
        .first()
    )
    if admin_role is None:
        insert_users_to_roles = users_to_roles.insert().values(
            user_id=user_id.id,
            role_id=role_id.id,
            create_date=datetime.now(),
        )
        session.execute(insert_users_to_roles)
    session.commit()


if __name__ == "__main__":
    create_db()
