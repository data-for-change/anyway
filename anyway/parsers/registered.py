# -*- coding: utf-8 -*-
import csv
import glob
import io
import logging
import os
import re
import sys
from datetime import datetime

import six
from flask.ext.sqlalchemy import SQLAlchemy

from ..models import RegisteredVehicle, City
from ..utilities import init_flask, time_delta

reload(sys)
sys.setdefaultencoding('utf8')

# Headless servers cannot use GUI file dialog and require raw user input
fileDialog = True
try:
    import tkFileDialog
except (ValueError, ImportError):
    fileDialog = False

app = init_flask()
db = SQLAlchemy(app)

_manual_assing_on_city_name = {
    'הרצלייה': 'הרצליה',
    'תל אביב-יפו': 'תל אביב -יפו',
    'אפרתה': 'אפרת',
    "באקה-ג'ת": 'באקה אל-גרביה',
    'בוקעאתה': 'בוקעאתא',
    "ג'ש (גוש חלב)": "ג'ש )גוש חלב(",
    'דבורייה': 'דבוריה',
    'טובא-זנגרייה': 'טובא-זנגריה',
    'יהוד': 'יהוד-מונוסון',
    'יהוד-נווה אפרים': 'יהוד-מונוסון',
    "כאוכב אבו אל- היג'א": "כאוכב אבו אל-היג'א",
    "כעביה-טבאש- חג'אג'רה": "כעביה-טבאש-חג'אג'רה",
    'מודיעין-מכבים- רעות' : 'מודיעין-מכבים-רעות',
    'נהרייה' : 'נהריה',
    "פקיעין (בוקייעה)" : "פקיעין )בוקייעה(",
    'פרדסייה' : 'פרדסיה',
    'קציר-חריש' : 'קציר',
    'שבלי-אום אל-גנם' : 'שבלי - אום אל-גנם',
}


class DatastoreImporter(object):
    _header_size = 12
    _in_encode = "utf-8"
    _report_year = 0
    _population_year = 0

    def import_file(self, inputfile):
        total = 0
        elements = os.path.basename(inputfile).split('_')
        self._report_year = self.as_int(elements[0])
        with io.open(inputfile, 'r', encoding=self._in_encode) as csvfile:
            csvreader = csv.reader(csvfile, delimiter=',', quotechar='"')
            row_count = 1
            inserts = []
            for row in csvreader:
                if row_count > self._header_size:
                    if self.is_process_row(row):
                        total += 1
                        inserts.append(self.row_parse(row))
                else:
                    self.header_row(row)
                row_count += 1

            db.session.bulk_insert_mappings(RegisteredVehicle, inserts)
        return total

    @staticmethod
    def is_process_row(row):
        if row[0].strip() == '' or row[1].strip() == '':
            return False
        return True

    def row_parse(self, row):
        name = row[12].strip().encode('utf-8')
        name = re.sub(' +', ' ', name).replace('קריית', 'קרית').replace("\n", '')
        search_name = name
        if name in _manual_assing_on_city_name:
            search_name = _manual_assing_on_city_name[name]

        return {
            'year': self._report_year,
            'name': name,
            'name_eng': row[0].strip(),
            'search_name' : search_name,
            'motorcycle': self.as_int(row[1]),
            'special': self.as_int(row[2]),
            'taxi': self.as_int(row[3]),
            'bus': self.as_int(row[4]),
            'minibus': self.as_int(row[5]),
            'truck_over3500': self.as_int(row[6]),
            'truck_upto3500': self.as_int(row[7]),
            'private': self.as_int(row[9]),
            'total': self.as_int(row[10]),
            'population': self.as_int(row[11]),
            'population_year': self._population_year
        }

    @staticmethod
    def as_int(value):
        value = value.strip().replace(',', '')
        try:
            return int(value)
        except ValueError:
            return 0

    def header_row(self, row):
        if row[1].strip() == "cycle":
            self._population_year = self.as_int(row[11])


def main(specific_folder, delete_all, path):
    if specific_folder:
        if fileDialog:
            dir_name = tkFileDialog.askdirectory(initialdir=os.path.abspath(path),
                                                 title='Please select a directory')
        else:
            dir_name = six.moves.input('Please provide the directory path: ')

        if delete_all:
            confirm_delete_all = six.moves.input("Are you sure you want to delete all the current data? (y/n)\n")
            if confirm_delete_all.lower() == 'n':
                delete_all = False
    else:
        dir_name = os.path.abspath(path)

    # wipe all data first
    if delete_all:
        tables = (RegisteredVehicle)
        logging.info("Deleting tables: " + ", ".join(table.__name__ for table in tables))
        for table in tables:
            db.session.query(table).delete()
            db.session.commit()

    importer = DatastoreImporter()
    total = 0
    dir_files = glob.glob("{0}/*.csv".format(dir_name))
    started = datetime.now()
    for fname in dir_files:
        total += importer.import_file(fname)

    db.session.commit()
    db.engine.execute(
        'UPDATE {0} rr SET city_id = ct.id FROM {1} ct WHERE rr.city_id IS NULL AND rr.search_name = ct.search_heb'.format(
            RegisteredVehicle.__tablename__, City.__tablename__))
    logging.info("Total: {0} items in {1}".format(total, time_delta(started)))
