import os

#
# This is the configuration file of the application
#
# Please make sure you don't store here any secret information and use environment
# variables
#


SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
SQLALCHEMY_POOL_RECYCLE = 60


SECRET_KEY = 'aiosdjsaodjoidjioewnioewfnoeijfoisdjf'