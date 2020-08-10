# -*- coding: utf-8 -*-
import csv
import glob
import logging
import os
import re
from datetime import datetime
from anyway.models import RegisteredVehicle, City
from anyway.utilities import (
    time_delta,
    CsvReader,
    ImporterUI,
    truncate_tables,
    decode_hebrew,
)
from anyway.app_and_db import db


COLUMN_CITY_NAME_ENG = 0
COLUMN_CITY_TOTAL_MOTORCYCLE = 1
COLUMN_CITY_TOTAL_SPECIAL = 2
COLUMN_CITY_TOTAL_TAXI = 3
COLUMN_CITY_TOTAL_BUS = 4
COLUMN_CITY_TOTAL_MINIBUS = 5
COLUMN_CITY_TOTAL_TRUCK_OVER3500 = 6
COLUMN_CITY_TOTAL_TRUCK_UPTO3500 = 7
COLUMN_CITY_TOTAL_PRIVATE = 9
COLUMN_CITY_TOTAL = 10
COLUMN_CITY_TOTAL_POPULATION = 11
COLUMN_CITY_NAME_HEB = 12

_manual_assign_on_city_name = {
    "הרצלייה": "הרצליה",
    "תל אביב-יפו": "תל אביב -יפו",
    "אפרתה": "אפרת",
    "באקה-ג'ת": "באקה אל-גרביה",
    "בוקעאתה": "בוקעאתא",
    "ג'ש (גוש חלב)": "ג'ש )גוש חלב(",
    "דבורייה": "דבוריה",
    "טובא-זנגרייה": "טובא-זנגריה",
    "יהוד": "יהוד-מונוסון",
    "יהוד-נווה אפרים": "יהוד-מונוסון",
    "כאוכב אבו אל- היג'א": "כאוכב אבו אל-היג'א",
    "כעביה-טבאש- חג'אג'רה": "כעביה-טבאש-חג'אג'רה",
    "מודיעין-מכבים- רעות": "מודיעין-מכבים-רעות",
    "נהרייה": "נהריה",
    "פקיעין (בוקייעה)": "פקיעין )בוקייעה(",
    "פרדסייה": "פרדסיה",
    "קציר-חריש": "קציר",
    "שבלי-אום אל-גנם": "שבלי - אום אל-גנם",
}


class CvsRawReader(CsvReader):
    def __iter__(self):
        for line in csv.reader(self._file):
            yield line


class DatastoreImporter(object):
    def __init__(self):
        self._report_year = 0
        self._population_year = 0

    def import_file(self, inputfile):
        total = 0
        elements = os.path.basename(inputfile).split("_")
        self._report_year = self.as_int(elements[0])
        csvreader = CvsRawReader(inputfile, encoding="utf-8")
        row_count = 1
        inserts = []
        for row in csvreader:
            if row_count > 12:  # header contains exactly 12 rows
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
        return row[0].strip() and row[1].strip()

    def row_parse(self, row):
        name = row[COLUMN_CITY_NAME_HEB].strip()
        name = re.sub(" +", " ", name).replace("קריית", "קרית").replace("\n", "")
        search_name = name
        if name in _manual_assign_on_city_name:
            search_name = _manual_assign_on_city_name[name]

        return {
            "year": self._report_year,
            "name": decode_hebrew(name),
            "name_eng": row[COLUMN_CITY_NAME_ENG].strip(),
            "search_name": decode_hebrew(search_name),
            "motorcycle": self.as_int(row[COLUMN_CITY_TOTAL_MOTORCYCLE]),
            "special": self.as_int(row[COLUMN_CITY_TOTAL_SPECIAL]),
            "taxi": self.as_int(row[COLUMN_CITY_TOTAL_TAXI]),
            "bus": self.as_int(row[COLUMN_CITY_TOTAL_BUS]),
            "minibus": self.as_int(row[COLUMN_CITY_TOTAL_MINIBUS]),
            "truck_over3500": self.as_int(row[COLUMN_CITY_TOTAL_TRUCK_OVER3500]),
            "truck_upto3500": self.as_int(row[COLUMN_CITY_TOTAL_TRUCK_UPTO3500]),
            "private": self.as_int(row[COLUMN_CITY_TOTAL_PRIVATE]),
            "total": self.as_int(row[COLUMN_CITY_TOTAL]),
            "population": self.as_int(row[COLUMN_CITY_TOTAL_POPULATION]),
            "population_year": self._population_year,
        }

    @staticmethod
    def as_int(value):
        value = value.strip().replace(",", "")
        try:
            return int(value)
        except ValueError:
            return 0

    def header_row(self, row):
        if row[1].strip() == "cycle":
            self._population_year = self.as_int(row[11])


def main(specific_folder, delete_all, path):
    import_ui = ImporterUI(path, specific_folder, delete_all)
    dir_name = import_ui.source_path()

    # wipe all data first
    if import_ui.is_delete_all():
        truncate_tables(db, (RegisteredVehicle,))

    importer = DatastoreImporter()
    total = 0
    dir_files = glob.glob("{0}/*.csv".format(dir_name))
    started = datetime.now()
    for fname in dir_files:
        total += importer.import_file(fname)

    db.session.commit()
    db.engine.execute(
        "UPDATE {0} SET city_id = (SELECT id FROM {1} WHERE {0}.search_name = {1}.search_heb) WHERE city_id IS NULL".format(
            RegisteredVehicle.__tablename__, City.__tablename__
        )
    )
    logging.info("Total: {0} items in {1}".format(total, time_delta(started)))
