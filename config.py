import os

#
# This is the configuration file of the application
#
# Please make sure you don't store here any secret information and use environment
# variables
#


SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
SENDGRID_USERNAME = os.environ.get('SENDGRID_USERNAME')
SENDGRID_PASSWORD = os.environ.get('SENDGRID_PASSWORD')
SQLALCHEMY_POOL_RECYCLE = 60

# The default path is SQLite file as it's the development environment DB
_build_marker_file_path = os.environ.get('BUILD_MARKER_INDEX_SQL_FILE') or './static/data/sql/sqlite-buildrtreeindex.sql'
BUILD_MARKER_INDEX_SQL_FILE = os.path.join(_build_marker_file_path)
MARKER_INDEX_PROVIDER_TYPE = os.environ.get('DATABASE_TYPE') or 'SQLite' #TODO: extract the database type from DATABASE_URL address


SECRET_KEY = 'aiosdjsaodjoidjioewnioewfnoeijfoisdjf'

