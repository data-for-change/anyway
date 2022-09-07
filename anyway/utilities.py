import argparse
import logging
import os
import re
import sys
import threading
import typing
from contextlib import contextmanager
from csv import DictReader
from datetime import datetime
from functools import partial
from urllib.parse import urlparse
from sqlalchemy import MetaData, Table


import phonenumbers
from dateutil.relativedelta import relativedelta

try:
    from flask import Flask
except ModuleNotFoundError:
    pass

from phonenumbers import NumberParseException

try:
    from pyproj import Transformer
except ModuleNotFoundError:
    pass

try:
    from validate_email import validate_email
except ModuleNotFoundError:
    pass

from anyway import config

# Headless servers cannot use GUI file dialog and require raw user input
_fileDialogExist = True
try:
    import tkFileDialog
except (ValueError, ImportError):
    _fileDialogExist = False

DATE_INPUT_FORMAT = "%d-%m-%Y"
_PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")


def init_flask():
    """
    initializes a Flask instance with default values
    """
    app = Flask(
        "anyway",
        template_folder=os.path.join(_PROJECT_ROOT, "templates"),
        static_folder=os.path.join(_PROJECT_ROOT, "static"),
    )
    app.config.from_object(config)
    app.config["BABEL_TRANSLATION_DIRECTORIES"] = os.path.join(_PROJECT_ROOT, "translations")
    if os.environ.get("PROXYFIX_X_FOR"):
        from werkzeug.middleware.proxy_fix import ProxyFix

        app.wsgi_app = ProxyFix(
            app.wsgi_app,
            x_for=int(os.environ["PROXYFIX_X_FOR"]),
            x_host=int(os.environ.get("PROXYFIX_X_HOST", "0")),
            x_port=int(os.environ.get("PROXYFIX_X_PORT", "0")),
            x_prefix=int(os.environ.get("PROXYFIX_X_PREFIX", "0")),
            x_proto=int(os.environ.get("PROXYFIX_X_PROTO", "0")),
        )
    return app


class ProgressSpinner(object):
    def __init__(self):
        self.counter = 0
        self.chars = ["|", "/", "-", "\\"]

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

    _digit_pattern = re.compile(r"^-?\d*(\.\d+)?$")

    def __init__(self, filename, encoding=None):
        self._file = open(filename, encoding=encoding)
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
        if value == "" or value is None:
            return None
        # the isdigit function doesn't match negative numbers
        if CsvReader._digit_pattern.match(value):
            return int(float(value))
        return value

    def __iter__(self):
        for line in DictReader(self._file):
            converted = dict([(key.upper(), self._convert(val)) for key, val in line.items()])
            yield converted


class ItmToWGS84(object):
    def __init__(self):
        # initializing WGS84 (epsg: 4326) and Israeli TM Grid (epsg: 2039) projections.
        # for more info: https://epsg.io/<epsg_num>/
        self.transformer = Transformer.from_proj(2039, 4326, always_xy=True)

    def convert(self, x, y):
        """
        converts ITM to WGS84 coordinates
        :type x: float
        :type y: float
        :rtype: tuple
        :return: (longitude,latitude)
        """
        longitude, latitude = self.transformer.transform(x, y)
        return longitude, latitude


def time_delta(since):
    delta = relativedelta(datetime.now(), since)
    attrs = ["years", "months", "days", "hours", "minutes", "seconds"]
    return " ".join(
        "%d %s" % (getattr(delta, attr), getattr(delta, attr) > 1 and attr or attr[:-1])
        for attr in attrs
        if getattr(delta, attr)
    )


def decode_hebrew(s):
    return s


open_utf8 = partial(open, encoding="utf-8")


def truncate_tables(db, tables):
    logging.info("Deleting tables: " + ", ".join(table.__name__ for table in tables))
    for table in tables:
        db.session.query(table).delete()
        db.session.commit()


def order_query_by_columns(query, keys):
    for primary_key in keys:
        query = query.order_by(primary_key)
    return query


def split_query_to_chunks(base_query, primary_keys, chunk_size):
    items_read = chunk_size
    offset = 0
    query = order_query_by_columns(base_query, primary_keys)
    while items_read == chunk_size:
        chunk = query \
            .slice(offset, offset + chunk_size) \
            .all()
        items_read = len(chunk)
        offset += items_read
        yield [row._asdict() for row in chunk]

def run_query_and_insert_to_table_in_chunks(query, table_inserted_to, columns_to_order_query_uniqely, chunk_size, session):
    for chunk in split_query_to_chunks(query, columns_to_order_query_uniqely, chunk_size):
        session.bulk_insert_mappings(table_inserted_to, chunk)
        session.commit()

def valid_date(date_string):
    from datetime import datetime

    try:
        return datetime.strptime(date_string, DATE_INPUT_FORMAT)
    except ValueError:
        msg = "Not a valid date: '{0}'. Date should be in the format DD-MM-YYYY".format(date_string)
        raise argparse.ArgumentTypeError(msg)


class ImporterUI(object):
    def __init__(self, source_path, specific_folder=False, delete_all=False):
        self._specific_folder = specific_folder
        self._delete_all = delete_all
        self._source_path = os.path.abspath(source_path)

    def source_path(self):
        if self._specific_folder:
            if _fileDialogExist:
                return tkFileDialog.askdirectory(
                    initialdir=self._source_path, title="Please select a directory"
                )
            else:
                return input("Please provide the directory path: ")
        return self._source_path

    def is_delete_all(self):
        if self._delete_all and self._specific_folder:
            confirm_delete_all = input(
                "Are you sure you want to delete all the current data? (y/n)\n"
            )
            if confirm_delete_all.lower() == "n":
                self._delete_all = False
        return self._delete_all


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i : i + n]


def parse_age_from_range(age_range: int) -> typing.Optional[typing.Tuple[int, int]]:
    # Convert from 'age_group' field in the table 'involved_markers_hebrew' to age range numbers
    ret_age_code_to_age_range = {
        1: (0, 4),
        2: (5, 9),
        3: (10, 14),
        4: (15, 19),
        5: (20, 24),
        6: (25, 29),
        7: (30, 34),
        8: (35, 39),
        9: (40, 44),
        10: (45, 49),
        11: (50, 54),
        12: (55, 59),
        13: (60, 64),
        14: (65, 69),
        15: (70, 74),
        16: (75, 79),
        17: (80, 84),
        18: (85, 200),
        99: None,
    }
    return ret_age_code_to_age_range[age_range]


def is_valid_number(phone: str) -> bool:
    try:
        phone_obj = phonenumbers.parse(phone, "IL")
        return phonenumbers.is_valid_number(phone_obj)
    except NumberParseException:
        return False


def is_a_safe_redirect_url(url: str) -> bool:
    url_obj = urlparse(url)
    if url_obj.scheme not in ["https", "http"]:
        return False

    netloc = url_obj.netloc
    if not netloc:
        return False

    # Note that we don't support ipv6 localhost address or ipv4 localhost full range of address
    if netloc in ["localhost", "127.0.0.1"]:
        return True
    else:  # Check localhost with port
        localhost_regex = re.compile(r"^127\.0\.0\.1:[0-9]{1,7}$|^localhost:[0-9]{1,7}$")
        if localhost_regex.match(netloc):
            return True

    if url_obj.scheme == "https" and netloc in [
        "www.anyway.co.il",
        "anyway-infographics-staging.web.app",
        "anyway-infographics.web.app",
        "anyway-infographics-demo.web.app",
    ]:
        return True

    if (
        config.SERVER_ENV == "dev"
        and url_obj.scheme == "https"
        and netloc in ["dev.anyway.co.il", "www.dev.anyway.co.il"]
    ):
        return True

    return False


def is_a_valid_email(tmp_given_user_email: str) -> bool:
    is_valid = validate_email(
        email_address=tmp_given_user_email, check_regex=True, check_mx=False, use_blacklist=False
    )
    return is_valid

class TableForTest(object):
    def __init__(self):
        self.table = None

    @contextmanager
    def create_table(self, db, table_name, metadata, *args):
        try:
            self.table = Table(table_name, metadata, *args)
            metadata.create_all(db.engine)
            yield self.table
        finally:
            db.session.close()
            if self.table is not None:
                self.table.drop(db.engine)

    @contextmanager
    def create_table_with_data(self, db, name, columns, data):
        with self.create_table(db, name, MetaData(), *columns) as table:
            with db.engine.connect() as conn:
                conn.execute(
                    table.insert().values(data)
                )
                yield table