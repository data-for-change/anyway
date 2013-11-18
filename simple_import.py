import os
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

db_connection_string = os.environ.get('CLEARDB_DATABASE_URL')
print "using connection string: %s"%db_connection_string
engine = create_engine(db_connection_string, convert_unicode=True, echo=True)
autocommit = False
db_session = sessionmaker(autocommit=autocommit, autoflush=True, bind=engine)
Base = declarative_base()
session = db_session()
from models import Marker
marker = Marker(
            user = None,
            title = "Accident",
            description = "sample accident",
            address = "sample address",
            latitude = "00.44",
            longitude = "00.22",
            type = Marker.MARKER_TYPE_ACCIDENT,
            subtype = "",
            created = "",
        )
session.add(marker)
if not autocommit:
    session.commit()
