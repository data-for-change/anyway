try:
    from anyway.app_and_db import db

    Base = db.Model
except ModuleNotFoundError:
    from sqlalchemy.ext.declarative.api import declarative_base

    Base = declarative_base()
