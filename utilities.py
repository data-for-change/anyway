from __future__ import print_function
import os
from csv import DictReader
from flask import Flask
import pyproj
import threading
import sys


def init_flask(name):
    app = Flask(name)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('CLEARDB_DATABASE_URL')
    return app


class ProgressSpinner(object):
    def __init__(self):
        self.counter = 0
        self.chars = ['|', '/', '-', '\\']

    def show(self):
        current_char = self.counter % len(self.chars)
        sys.stderr.write("\r%s" % self.chars[current_char])
        self.counter += 1


class CsvReader(object):
    def __init__(self, filename):
        self.file = open(filename)
        self._lock = threading.RLock()
        self._closed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        with self._lock:
            if not self._closed:
                self.file.close()

    def name(self):
        return self.file.name

    def close(self):
        with self._lock:
            if not self._closed:
                self.file.close()

    def _convert(self, value):
        if value.isdigit():
            return int(value)
        if value == "":
            return None

        return value

    def __iter__(self):
        for line in DictReader(self.file):
            converted = dict([(key.upper(), self._convert(val)) for key, val in line.iteritems()])
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