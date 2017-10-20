from __future__ import print_function
from csv import DictReader
from datetime import datetime
from dateutil.relativedelta import relativedelta
from . import config
from flask import Flask
from functools import partial
import os
import pyproj
import threading
import sys
import re
import six


_PROJECT_ROOT = os.path.join(os.path.dirname(__file__), '..')

def init_flask():
    """
    initializes a Flask instance with default values
    """
    app = Flask(
        "anyway",
        template_folder=os.path.join(_PROJECT_ROOT, 'templates'),
        static_folder=os.path.join(_PROJECT_ROOT, 'static'),)
    app.config.from_object(config)
    app.config['BABEL_TRANSLATION_DIRECTORIES'] = os.path.join(_PROJECT_ROOT, 'translations')
    return app


class ProgressSpinner(object):
    def __init__(self):
        self.counter = 0
        self.chars = ['|', '/', '-', '\\']

    def show(self):
        """
        prints a rotating spinner
        """
        current_char = self.counter % len(self.chars)
        sys.stderr.write("\r%s" % self.chars[current_char])
        self.counter += 1


class CsvReader(object):
    """
    loads and handles csv files
    """
    _digit_pattern = re.compile(r'^-?\d*(\.\d+)?$')

    def __init__(self, filename, encoding=None):
        self._file = open(filename) if six.PY2 else open(filename, encoding=encoding)
        self._lock = threading.RLock()
        self._closed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        with self._lock:
            if not self._closed:
                self._file.close()

    def name(self):
        """
        the filename of the csv file
        :return:
        """
        return self._file.name

    def close(self):
        with self._lock:
            if not self._closed:
                self._file.close()

    def _convert(self, value):
        """
        converts an str value to a typed one
        """
        if value == '' or value is None:
            return None
        # the isdigit function doesn't match negative numbers
        if CsvReader._digit_pattern.match(value):
            return int(float(value))
        return value

    def __iter__(self):
        for line in DictReader(self._file):
            converted = dict([(key.upper(), self._convert(val)) for key, val in six.iteritems(line)])
            yield converted


class ItmToWGS84(object):
    def __init__(self):
        # initializing WGS84 (epsg: 4326) and Israeli TM Grid (epsg: 2039) projections.
        # for more info: http://spatialreference.org/ref/epsg/<epsg_num>/
        self.wgs84 = pyproj.Proj(init='epsg:4326')
        self.itm = pyproj.Proj(init='epsg:2039')

    def convert(self, x, y):
        """
        converts ITM to WGS84 coordinates
        :type x: float
        :type y: float
        :rtype: tuple
        :return: (long,lat)
        """
        longitude, latitude = pyproj.transform(self.itm, self.wgs84, x, y)
        return longitude, latitude


def time_delta(since):
    delta = relativedelta(datetime.now(), since)
    attrs = ['years', 'months', 'days', 'hours', 'minutes', 'seconds']
    return " ".join('%d %s' % (getattr(delta, attr),
                               getattr(delta, attr) > 1 and attr or attr[:-1])
                    for attr in attrs if getattr(delta, attr))

if six.PY3:
    def decode_hebrew(s, encoding="cp1255"):
        return s
else:
    def decode_hebrew(s, encoding="cp1255"):
        return s.decode(encoding)


open_utf8 = partial(open, encoding="utf-8") if six.PY3 else open
