from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

engine = create_engine('mysql://b224c5f58888c8:b33706db@us-cdbr-east-04.cleardb.com/heroku_90761df1db0de24?charset=utf8', convert_unicode=True, echo=True)
db_session = scoped_session(sessionmaker(autocommit=True, autoflush=True, bind=engine))
Base = declarative_base()

Base.query = db_session.query_property()
