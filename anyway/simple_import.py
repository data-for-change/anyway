from __future__ import print_function

import datetime
import os

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .constants import CONST

db_connection_string = os.environ.get('CLEARDB_DATABASE_URL')
print("using connection string: %s" % db_connection_string)
engine = create_engine(db_connection_string, convert_unicode=True, echo=True)
autocommit = False  # Autocommit does not seem to work
db_session = sessionmaker(autocommit=autocommit, autoflush=True, bind=engine)
Base = declarative_base()
session = db_session()
from .models import AccidentMarker

marker = AccidentMarker(
    user=None,
    title="Accident",
    description="sample accident",
    address="sample address",
    latitude="00.33",
    longitude="00.22",
    type=CONST.MARKER_TYPE_ACCIDENT,
    accident_type="",
    created=datetime.datetime.now(),
)
session.add(marker)
if not autocommit:
    session.commit()
