import os
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# engine = create_engine('mysql://b224c5f58888c8:b33706db@us-cdbr-east-04.cleardb.com/heroku_90761df1db0de24?charset=utf8', convert_unicode=True, echo=True)

db_connection_string = os.environ.get('CLEARDB_DATABASE_URL')
# raise(Exception("db conn: <%s>"%db_connection_string))
engine = create_engine(db_connection_string, convert_unicode=True, echo=False)

# engine = create_engine('sqlite:///local.db', convert_unicode=True, echo=True)

db_session = scoped_session(sessionmaker(autocommit=True, autoflush=True, bind=engine))
Base = declarative_base()

Base.query = db_session.query_property()
