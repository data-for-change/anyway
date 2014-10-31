#!/usr/bin/env python
# -*- coding: utf-8 -*-
import csv
import glob
import json
import sys
import os
import argparse
import subprocess
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
import datetime
from tables_lms import *
import field_names
from models import Marker
import pyproj

directories_not_processes = []
import re

accident_type_regex = re.compile("Accidents Type (?P<type>\d)")


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
        :rtype: dict
        :return: {'lat': 26.06199702841902, 'lng': 33.01173637265791}
        """
        longitude, latitude = pyproj.transform(self.itm, self.wgs84, x, y)
        return {"lat": latitude, "lng": longitude}
6

app = Flask(__name__)
# app.config['SQLALCHEMY_ECHO'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('CLEARDB_DATABASE_URL')
db = SQLAlchemy(app)


def show_progress_spinner():
    d = show_progress_spinner.counter % 4
    chars = ('|', '/', '-', '\\')
    s = chars[d]
    sys.stderr.write("\r%s" % s)
    show_progress_spinner.counter += 1


show_progress_spinner.counter = 0

ACCIDENTS = 'accidents'
CITIES = 'cities'
STREETS = 'streets'
URBAN_INTERSECTION = 'urban_intersection'
NON_URBAN_INTERSECTION = 'non_urban_intersection'
DICTIONARY = "dictionary_data"

cities = list(csv.DictReader(open(os.path.join("static/data/cities.csv"))))
cities_dict = {x[field_names.sign]: x[field_names.name] for x in cities}


def number(value, *kargs, **kwargs):
    return int(value) if value else None


def fixed_table(param, value, *kargs, **kwargs):
    """
    takes a parameter and a value and if found, returns it with '!' at the beginning
    the reason behind this change is to reduce the amount of data that's saved into the db.
    instead of saving a localized string that corresponds to the param/value tuple,
    only the value number is saved and when serialized, we recognize localized values with the '!' character
    and localize them.
    :return: if found, returns the value with ! at the start of the string
    """
    return "!%s" % value if value and int(value) in TABLES[param] else None


def dictionary(csv, param, value, *kargs, **kwargs):
    for item in csv:
        if field_names.table_number not in item or field_names.code not in item:
            print("cannot parse dictionary data from csv")
            return ""
        if item[field_names.table_number] == param and item[field_names.code] == value:
            return dictionary_data[2]

    return None


def boolean(value, *kargs, **kwargs):
    return True if value == 1 else False


def cities_map(value, *kargs, **kwargs):
    return cities_dict[value] if value in cities_dict else ""


def streets_map(csv, value, accident, *kargs, **kwargs):
    for street in csv:
        if field_names.settlement not in street or field_names.settlement_sign not in accident:
            print("could not parse street data")
            return None
        if street[field_names.settlement] == accident[field_names.settlement_sign] and value == street[
            field_names.street_sign]:
            return street[field_names.street_name]


def urban_intersection_map(value, *kargs, **kwargs):
    return value


def non_urban_intersection_map(value, *kargs, **kwargs):
    return value


FIELD_FUNCTIONS = {
    "pk_teuna_fikt": ("מזהה", number, None),
    "SUG_DEREH": ("סוג דרך", fixed_table, "SUG_DEREH"),
    "SEMEL_YISHUV": ("ישוב", cities_map, None),  # from dictionary
    "REHOV1": ("רחוב 1", streets_map, None),  # from dicstreets (with SEMEL_YISHUV)
    "REHOV2": ("רחוב 2", streets_map, None),  # from dicstreets (with SEMEL_YISHUV)
    "BAYIT": ("מספר בית", number, None),
    "ZOMET_IRONI": ("צומת עירוני", urban_intersection_map, None),  # from intersect urban dictionary
    "KVISH1": ("כביש 1", urban_intersection_map, None),  # from intersect urban dictionary
    "KVISH2": ("כביש 2", urban_intersection_map, None),  # from intersect urban dictionary
    "ZOMET_LO_IRONI": ("צומת לא עירוני", non_urban_intersection_map, None),  # from non urban dictionary
    "YEHIDA": ("יחידה", fixed_table, "YEHIDA"),
    "SUG_YOM": ("סוג יום", fixed_table, "SUG_YOM"),
    "RAMZOR": ("רמזור", boolean, None),
    "HUMRAT_TEUNA": ("חומרת תאונה", fixed_table, "HUMRAT_TEUNA"),
    "SUG_TEUNA": ("סוג תאונה", fixed_table, "SUG_TEUNA"),
    "ZURAT_DEREH": ("צורת דרך", fixed_table, "ZURAT_DEREH"),
    "HAD_MASLUL": ("חד מסלול", fixed_table, "HAD_MASLUL"),
    "RAV_MASLUL": ("רב מסלול", fixed_table, "RAV_MASLUL"),
    "MEHIRUT_MUTERET": ("מהירות מותרת", fixed_table, "MEHIRUT_MUTERET"),
    "TKINUT": ("תקינות", fixed_table, "TKINUT"),
    "ROHAV": ("רוחב", fixed_table, "ROHAV"),
    "SIMUN_TIMRUR": ("סימון תמרור", fixed_table, "SIMUN_TIMRUR"),
    "TEURA": ("תאורה", fixed_table, "TEURA"),
    "BAKARA": ("בקרה", fixed_table, "BAKARA"),
    "MEZEG_AVIR": ("מזג אוויר", fixed_table, "MEZEG_AVIR"),
    "PNE_KVISH": ("פני כביש", fixed_table, "PNE_KVISH"),
    "SUG_EZEM": ("סוג עצם", fixed_table, "SUG_EZEM"),
    "MERHAK_EZEM": ("מרחק עצם", fixed_table, "MERHAK_EZEM"),
    "LO_HAZA": ("לא חצה", fixed_table, "LO_HAZA"),
    "OFEN_HAZIYA": ("אופן חציה", fixed_table, "OFEN_HAZIYA"),
    "MEKOM_HAZIYA": ("מקום חציה", fixed_table, "MEKOM_HAZIYA"),
    "KIVUN_HAZIYA": ("כיוון חציה", fixed_table, "KIVUN_HAZIYA"),
    "STATUS_IGUN": ("עיגון", fixed_table, "STATUS_IGUN"),
    "MAHOZ": ("מחוז", dictionary, 77),
    "NAFA": ("נפה", dictionary, 79),
    "EZOR_TIVI": ("אזור טבעי", dictionary, 80),
    "MAAMAD_MINIZIPALI": ("מעמד מוניציפלי", dictionary, 78),
    "ZURAT_ISHUV": ("צורת יישוב", dictionary, 81),
}

FIELDS_NOT_IN_DESCRIPTION = [
    "SHNAT_TEUNA",
    "HODESH_TEUNA",
    "YOM_BE_HODESH",
    "SHAA",
    "REHOV1",
    "REHOV2",
    "BAYIT",
    "SEMEL_YISHUV",
    "X",
    "Y",
]

FIELD_LIST = FIELD_FUNCTIONS.keys()


def processor_extra_args(processor, files):
    if processor == streets_map:
        return {"csv": list(csv.DictReader(files[STREETS]))}
    if processor == cities_map:
        return {"csv": cities}
    if processor == non_urban_intersection_map:
        return {"csv": list(csv.DictReader(files[NON_URBAN_INTERSECTION]))}
    if processor == urban_intersection_map:
        return {"csv": list(csv.DictReader(files[URBAN_INTERSECTION]))}
    if processor == dictionary:
        return {"csv": list(csv.DictReader(files[DICTIONARY]))}
    return {}


def import_accident(files):
    print "reading accidents from file %s" % (files[ACCIDENTS].name,)
    accidents_csv = csv.DictReader(files[ACCIDENTS])
    # accidents_gps_coordinates = json.loads(open(general_path+"gps.json").read())
    gps = ItmToWGS84()
    for accident in accidents_csv:
        output_line = {}
        output_fields = {}
        extra_fields = {}
        for field in FIELD_LIST:
            field_name, processor, parameter = FIELD_FUNCTIONS[field]
            extra_args = processor_extra_args(processor, files)
            output_line[field] = processor(param=parameter, value=accident[field], accident=accident, **extra_args)
            if output_line[field] and parameter and field and not field in FIELDS_NOT_IN_DESCRIPTION:
                extra_fields[field] = output_line[field]

        if not accident["X"] or not accident["Y"]:
            continue

        accident_date = datetime.datetime(int(accident["SHNAT_TEUNA"]), int(accident["HODESH_TEUNA"]),
                                          int(accident["YOM_BE_HODESH"]), int(accident["SHAA"]) % 24, 0, 0)
        address = "%s%s, %s" % (
            output_line["REHOV1"], " %s" % output_line["BAYIT"] if output_line["BAYIT"] != 9999 else "",
            output_line["SEMEL_YISHUV"])
        output_fields["date"] = accident_date
        output_fields["description"] = json.dumps(extra_fields, encoding='utf-8')
        output_fields["id"] = accident["pk_teuna_fikt"]
        output_fields["severity"] = int(accident["HUMRAT_TEUNA"])
        output_fields["subType"] = int(accident["SUG_TEUNA"])
        output_fields["address"] = address
        output_fields["locationAccuracy"] = int(accident["STATUS_IGUN"])

        converted = gps.convert(accident['X'], accident['Y'])
        output_fields["lat"] = converted['lat']
        output_fields["lng"] = converted['lng']
        yield output_fields


def find_and_open_csv(directory, filename, files):
    path = os.path.join(directory, filter(lambda path: filename.lower() in path.lower(), files)[0])
    return open(path)


def check_integrity(directory):
    needed_files = ["AccData.csv", "IntersectUrban.csv", "DicStreets.csv", "Dictionary.csv", "IntersectNonUrban.csv"]
    files_in_directory = [x for x in os.listdir(directory)]
    for needed in needed_files:
        amount = len(filter(lambda path: needed.lower() in path.lower(), files_in_directory))
        if amount == 0:
            print(
                "file doesn't exist directory, cannot parse it; directory: {0};filename: {1}".format(directory, needed))
            return False
        if amount > 1:
            print("there are too many files in the directory, cannot parse!;directory: {0};filename: {1}"
                  .format(directory, needed))
            return False
    return True


def import_data(directory):
    if not check_integrity(directory):
        print "directory cannot be proccessed: {}".format(directory)
        directories_not_processes.append(directory)
        return

    files_in_dir = os.listdir(directory)
    files = {ACCIDENTS: find_and_open_csv(directory, "AccData.csv", files_in_dir),
             URBAN_INTERSECTION: find_and_open_csv(directory, "IntersectUrban.csv", files_in_dir),
             NON_URBAN_INTERSECTION: find_and_open_csv(directory, "IntersectNonUrban.csv", files_in_dir),
             STREETS: find_and_open_csv(directory, "DicStreets.csv", files_in_dir),
             DICTIONARY: find_and_open_csv(directory, "Dictionary.csv", files_in_dir)
    }

    for accident in import_accident(files):
        yield accident

    for csv in files.values():
        csv.close()


def import_to_datastore(directory, provider_code, ratio=1):
    print "importing with ratio = %s" % (ratio,)
    i = 0

    commit_every = 500

    for irow, data in enumerate(import_data(directory)):
        show_progress_spinner()
        if irow % ratio == 0:
            id = int("{0}{1}".format(provider_code, data['id']))

            marker = Marker(
                user=None,
                id=id,
                title="Accident",
                description=data["description"].decode("utf8"),
                address=data["address"].decode("cp1255"),
                latitude=data["lat"],
                longitude=data["lng"],
                type=Marker.MARKER_TYPE_ACCIDENT,
                subtype=data["subType"],
                severity=data["severity"],
                created=data["date"],
                locationAccuracy=data["locationAccuracy"],
            )

            db.session.add(marker)
            i += 1

            if i % commit_every == 0:
                print "committing (%d items done)..." % (i,)
                db.session.commit()
                print "done."

    if i % commit_every != 0:  # we still have data in our transaction, flush it
        print "committing..."
        db.session.commit()
        print "done."

    print "imported %d items" % (i,)


def get_provider_code(directory_name=None):
    if directory_name:
        match = accident_type_regex.match(directory_name)
        if match:
            return int(match.groupdict()['type'])

    ans = ""
    while not ans.isdigit():
        ans = raw_input("directory provider code is invalid, please enter a valid code: ")
        if ans.isdigit():
            return int(ans)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', type=str, default=None)
    parser.add_argument('--ratio', type=int, metavar='n', default=1,
                        help='Import ratio 1:n')
    parser.add_argument('--delete_all', dest='delete_all', action='store_true')
    parser.add_argument('--no_delete_all', dest='delete_all', action='store_false',
                        help='Load markers on top of existing markers (no update, just add)')
    parser.add_argument('--provider_code', dest='provider_code', type=int)
    parser.set_defaults(delete_all=True)

    args = parser.parse_args()

    # wipe all the Markers first
    if args.delete_all:
        ans = ""
        while ans not in ["y", "n"]:
            ans = raw_input("are you sure you want to delete all? (y/n)")
        if ans == "y":
            print ("deleting the entire db!")
            db.session.query(Marker).delete()
            db.session.commit()

    if args.path:
        if not args.provider_code:
            print "provider code is mandatory when using a specific directory"
            return
        import_to_datastore(args.path, args.provider_code, args.ratio)
    else:
        for directory in glob.glob("static/data/lms/*/*"):
            parent_directory = os.path.basename(os.path.dirname(os.path.join(os.pardir, directory)))
            provider_code = args.provider_code if args.provider_code else get_provider_code(parent_directory)
            import_to_datastore(directory, provider_code, args.ratio)

    print("finished processing all directories, except: %s" % directories_not_processes)


if __name__ == "__main__":
    main()