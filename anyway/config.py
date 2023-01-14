# -*- coding: utf-8 -*-
import os

#
# This is the configuration file of the application
#
# Please make sure you don't store here any secret information and use environment
# variables
#

SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "postgresql://postgres@localhost/anyway")
SQLALCHEMY_TRACK_MODIFICATIONS = True
ENTRIES_PER_PAGE = os.environ.get("ENTRIES_PER_PAGE", 1000)
SQLALCHEMY_ENGINE_OPTIONS = {}
# SQLALCHEMY_ECHO = True
# available languages
LANGUAGES = {"en": "English", "he": "עברית"}

# The SERVER_ENV is used to determine if we are in https://dev.anyway.co.il/ server or in https://www.anyway.co.il/ server
# and FLASK_ENV is used to determine if we are development state (of the backend server) or not.
#
# In the https://dev.anyway.co.il/ server SERVER_ENV=dev and FLASK_ENV is not set,
# In the https://anyway.co.il/ server SERVER_ENV=prod and FLASK_ENV is not set,
# on the local system SERVER_ENV is not set and FLASK_ENV=development.
#
# *https://dev.anyway.co.il/ is for the FE team development.
SERVER_ENV = os.getenv("SERVER_ENV", "prod")
