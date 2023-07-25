try:
    from anyway.app_and_db import db, app
    with app.app_context():
        Base = db.Model
except ModuleNotFoundError:
    from sqlalchemy.ext.declarative.api import declarative_base

    Base = declarative_base()
