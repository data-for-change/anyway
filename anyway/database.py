from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from . import config


engine = create_engine(config.SQLALCHEMY_DATABASE_URI, convert_unicode=True, echo=False)
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=True, bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()


