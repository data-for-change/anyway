from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from . import config


engine = create_engine(config.SQLALCHEMY_DATABASE_URI, convert_unicode=True, echo=False)
Base = declarative_base()


