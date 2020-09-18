# -*- coding: utf-8 -*-
import os
from anyway import secrets
#
# This is the configuration file of the application
#
# Please make sure you don't store here any secret information and use environment
# variables
#

SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "postgresql://postgres@localhost/anyway")
SQLALCHEMY_TRACK_MODIFICATIONS = True
ENTRIES_PER_PAGE = int(secrets.get_with_default("ENTRIES_PER_PAGE", "1000"))
SQLALCHEMY_ENGINE_OPTIONS = {}

# available languages
LANGUAGES = {"en": "English", "he": "עברית"}
