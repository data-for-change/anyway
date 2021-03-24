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

# available languages
LANGUAGES = {"en": "English", "he": "עברית"}

SERVER_ENV = os.getenv("SERVER_ENV", "prod")
