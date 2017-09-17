# -*- coding: utf-8 -*-
import os

#
# This is the configuration file of the application
#
# Please make sure you don't store here any secret information and use environment
# variables
#

SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
if SQLALCHEMY_DATABASE_URI is None:
    raise Exception('Please, set the DATABASE_URL environment variable to be sqlite:///local.db')
SQLALCHEMY_TRACK_MODIFICATIONS = True
SENDGRID_USERNAME = os.environ.get('SENDGRID_USERNAME')
SENDGRID_PASSWORD = os.environ.get('SENDGRID_PASSWORD')
ENTRIES_PER_PAGE = os.environ.get('ENTRIES_PER_PAGE', 100)
SQLALCHEMY_POOL_RECYCLE = 60


SECRET_KEY = 'aiosdjsaodjoidjioewnioewfnoeijfoisdjf'

# available languages
LANGUAGES = {
    'en': 'English',
    'he': 'עברית',
}
