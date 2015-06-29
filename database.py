import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import NoSuchTableError
from sqlalchemy.engine import reflection
from sqlalchemy.schema import Table
import config

engine = create_engine(config.SQLALCHEMY_DATABASE_URI, convert_unicode=True, echo=False)
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=True, bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()


def get_table(table_name, meta):
	insp = reflection.Inspector.from_engine(engine)

	if table_name in insp.get_table_names():
		table = Table(table_name, meta, autoload=True, autoload_with=engine)
		return table
	else:	
		logging.warning("Could not find table: {0}".format(table_name))
		return None


def insert_table(table_name, values):
	if not isinstance(values, list) and not isinstance(values, dict):
		logging.error("Trying to insert non dictionary object(s) to the table. \nUse single or list of dictionary object(s) with keys and values to insert the table. Values type: {0}".format(type(values)))
		return False

	table = get_table(table_name, Base.metadata)
	if table is not None:
		# catch unexpected values
		try:
			engine.execute(table.insert(), values)
			return True
		except Exception, e:
			logging.error("Could not execute Insert to table: {0}. Error: {2}".format(table_name, e.message))
			return False
	else:
		return False


def delete_table(table_name):
	table = get_table(table_name, Base.metadata)
	if table is not None:
		engine.execute(table.delete())
		return True
	logging.error("Error deleting table, Could not find table: {0}".format(table_name))
	return False