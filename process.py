# -*- coding: utf-8 -*-
from __future__ import print_function
import glob
import os
import argparse
import json
from flask.ext.sqlalchemy import SQLAlchemy
import field_names
from models import Marker
import models
from utilities import ProgressSpinner, ItmToWGS84, init_flask, CsvReader
import itertools
import localization
import re
from datetime import datetime

directories_not_processes = {}

progress_wheel = ProgressSpinner()
content_encoding = 'cp1255'
accident_type_regex = re.compile("Accidents Type (?P<type>\d)")

ACCIDENTS = 'accidents'
CITIES = 'cities'
STREETS = 'streets'
ROADS = "roads"
URBAN_INTERSECTION = 'urban_intersection'
NON_URBAN_INTERSECTION = 'non_urban_intersection'
DICTIONARY = "dictionary"

lms_files = {ACCIDENTS: "AccData.csv",
             URBAN_INTERSECTION: "IntersectUrban.csv",
             NON_URBAN_INTERSECTION: "IntersectNonUrban.csv",
             STREETS: "DicStreets.csv",
             DICTIONARY: "Dictionary.csv",
}

coordinates_converter = ItmToWGS84()
app = init_flask(__name__)
db = SQLAlchemy(app)


def get_street(settlement_sign, street_sign, streets):
    """
    extracts the street name using the settlement id and street id
    """
    if settlement_sign not in streets:
        return None
    street_name = [x[field_names.street_name].decode(content_encoding) for x in streets[settlement_sign] if
                   x[field_names.street_sign] == street_sign]
    # there should be only one street name, or none if it wasn't found.
    return street_name[0] if len(street_name) == 1 else None


def get_address(accident, streets):
    """
    extracts the address of the main street.
    tries to build the full address: <street_name> <street_number>, <settlement>,
    but might return a partial one if unsuccessful.
    """
    street = get_street(accident[field_names.settlement_sign], accident[field_names.street1], streets)
    if not street:
        return u""

    # the home field is invalid if it's empty or if it contains 9999
    home = accident[field_names.home] if accident[field_names.home] != 9999 else None
    settlement = localization.get_city_name(accident[field_names.settlement_sign])

    if not home and not settlement:
        return street
    if not home and settlement:
        return u"{}, {}".format(street, settlement)
    if home and not settlement:
        return u"{} {}".format(street, home)

    return u"{} {}, {}".format(street, home, settlement)


def get_streets(accident, streets):
    """
    extracts the streets the accident occurred in.
    every accident has a main street and a secondary street.
    :return: a tuple containing both streets.
    """
    main_street = get_address(accident, streets)
    secondary_street = get_street(accident[field_names.settlement_sign], accident[field_names.street2], streets)
    return main_street, secondary_street


def get_junction(accident, roads):
    """
    extracts the junction from an accident
    :return: returns the junction or None if it wasn't found
    """
    key = accident[field_names.road1], accident[field_names.road2]
    junction = roads.get(key, None)
    return junction.decode(content_encoding) if junction else None


def parse_date(accident):
    """
    parses an accident's date
    """
    year = accident[field_names.accident_year]
    month = accident[field_names.accident_month]
    day = accident[field_names.accident_day]
    hour = accident[field_names.accident_hour] % 24
    accident_date = datetime(year, month, day, hour, 0, 0)
    return accident_date


def load_extra_data(accident, streets, roads):
    """
    loads more data about the accident
    :return: a dictionary containing all the extra fields and their values
    :rtype: dict
    """
    extra_fields = {}
    # if the accident occurred in an urban setting
    if bool(accident[field_names.urban_intersection]):
        main_street, secondary_street = get_streets(accident, streets)
        if main_street:
            extra_fields[field_names.street1] = main_street
        if secondary_street:
            extra_fields[field_names.street2] = secondary_street

    # if the accident occurred in a non urban setting (highway, etc')
    if bool(accident[field_names.non_urban_intersection]):
        junction = get_junction(accident, roads)
        if junction:
            extra_fields[field_names.junction_name] = junction

    # localize static accident values
    for field in localization.get_supported_tables():
        if accident[field]:
            # if we have a localized field for that particular field, save the field value
            # it will be fetched we deserialized
            if localization.get_field(field, accident[field]):
                extra_fields[field] = accident[field]

    return extra_fields


def import_accidents(provider_code, accidents, streets, roads):
    print("reading accidents from file %s" % (accidents.name(),))
    for accident in accidents:
        if not accident[field_names.x_coordinate] or not accident[field_names.y_coordinate]:
            continue
        lng, lat = coordinates_converter.convert(accident[field_names.x_coordinate], accident[field_names.y_coordinate])

        marker = Marker(
            user=None,
            id=int("{0}{1}".format(provider_code, accident[field_names.id])),
            title="Accident",
            description=json.dumps(load_extra_data(accident, streets, roads), encoding=models.db_encoding),
            address=get_address(accident, streets),
            latitude=lat,
            longitude=lng,
            type=Marker.MARKER_TYPE_ACCIDENT,
            subtype=int(accident[field_names.accident_type]),
            severity=int(accident[field_names.accident_severity]),
            created=parse_date(accident),
            locationAccuracy=int(accident[field_names.igun]),
        )

        yield marker
    accidents.close()


def get_files(directory):
    for name, filename in lms_files.iteritems():

        if name not in [STREETS, NON_URBAN_INTERSECTION, ACCIDENTS]:
            continue

        files = filter(lambda path: filename.lower() in path.lower(), os.listdir(directory))
        amount = len(files)
        if amount == 0:
            raise ValueError(
                "file doesn't exist directory, cannot parse it; directory: {0};filename: {1}".format(directory,
                                                                                                     filename))
        if amount > 1:
            raise ValueError("there are too many files in the directory, cannot parse!;directory: {0};filename: {1}"
                             .format(directory, filename))

        csv = CsvReader(os.path.join(directory, files[0]))

        if name == STREETS:
            streets_map = {}
            for settlement in itertools.groupby(csv, lambda street: street.get(field_names.settlement, "OTHER")):
                key, val = tuple(settlement)

                streets_map[key] = [{field_names.street_sign: x[field_names.street_sign],
                                     field_names.street_name: x[field_names.street_name]} for x in val if
                                    field_names.street_name in x and field_names.street_sign in x]
            csv.close()
            yield name, streets_map
        elif name == NON_URBAN_INTERSECTION:
            roads = {(x[field_names.road1], x[field_names.road2]): x[field_names.junction_name] for x in csv if
                     field_names.road1 in x and field_names.road2 in x}
            csv.close()
            yield ROADS, roads
        elif name == ACCIDENTS:
            yield name, csv


def load_needed_files(directory):
    files = {}
    try:
        files = dict(get_files(directory))
    except ValueError as e:
        directories_not_processes[directory] = e.message
    finally:
        return files


def import_to_datastore(directory, provider_code, batch_size):
    """
    goes through all the files in a given directory, parses and commits them
    """
    imported = 0
    files_from_lms = load_needed_files(directory)
    if len(files_from_lms) == 0:
        return

    print("importing data from directory: {}".format(directory))
    now = datetime.now()
    for i, marker in enumerate(import_accidents(provider_code=provider_code, **files_from_lms)):
        imported = i
        progress_wheel.show()
        db.session.add(marker)
        if i % batch_size == 0 and i > 0:
            print("\rcommitting ({0} items done)...".format(i))
            db.session.commit()
            print("commited.")

    # commit any left sessions, if any were imported
    if imported > 0:
        db.session.commit()

    took = int((datetime.now() - now).total_seconds())
    print("imported {0} items from directory: {1} in {2} seconds".format(imported, directory, took))


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
    parser.add_argument('--path', type=str, default="static/data/lms")
    parser.add_argument('--batch_size', type=int, default=100)
    parser.add_argument('--delete_all', dest='delete_all', action='store_true', default=True)
    parser.add_argument('--provider_code', type=int)
    args = parser.parse_args()
    # wipe all the Markers first
    if args.delete_all:
        print("deleting the entire db!")
        db.session.query(Marker).delete()

        db.session.commit()

    for directory in glob.glob("{0}/*/*".format(args.path)):
        parent_directory = os.path.basename(os.path.dirname(os.path.join(os.pardir, directory)))
        provider_code = args.provider_code if args.provider_code else get_provider_code(parent_directory)
        import_to_datastore(directory, provider_code, args.batch_size)

    failed = ["{0}: {1}".format(directory, fail_reason) for directory, fail_reason in
              directories_not_processes.iteritems()]
    print("finished processing all directories, except: %s" % "\n".join(failed))


if __name__ == "__main__":
    main()