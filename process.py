# -*- coding: utf-8 -*-
from __future__ import print_function
import glob
import os
import argparse
import json
from flask.ext.sqlalchemy import SQLAlchemy
import field_names
from models import Marker, MarkerIndex
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
        # Changed to return blank string instead of None for correct presentation (Omer)
        return u""
    street_name = [x[field_names.street_name].decode(content_encoding) for x in streets[settlement_sign] if
                   x[field_names.street_sign] == street_sign]
    # there should be only one street name, or none if it wasn't found.
    return street_name[0] if len(street_name) == 1 else u""


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
    return junction.decode(content_encoding) if junction else u""


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


def get_data_value(value):
    """
    :returns: value for parameters which are not mandatory in an accident data
    OR zero if the parameter value does not exist
    """
    return int(value) if value else 0


def import_accidents(provider_code, accidents, streets, roads):
    print("reading accidents from file %s" % (accidents.name(),))
    for accident in accidents:
        if field_names.x_coordinate not in accident or field_names.y_coordinate not in accident:
            raise ValueError("x and y coordinates are missing from the accidents file!")
        if not accident[field_names.x_coordinate] or not accident[field_names.y_coordinate]:
            continue
        lng, lat = coordinates_converter.convert(accident[field_names.x_coordinate], accident[field_names.y_coordinate])
        main_street, secondary_street = get_streets(accident, streets)

        marker = {
            "id":int("{0}{1}".format(provider_code, accident[field_names.id])),
            "title":"Accident",
            "description":json.dumps(load_extra_data(accident, streets, roads), encoding=models.db_encoding),
            "address":get_address(accident, streets),
            "latitude":lat,
            "longitude":lng,
            "subtype":int(accident[field_names.accident_type]),
            "severity":int(accident[field_names.accident_severity]),
            "created":parse_date(accident),
            "locationAccuracy":int(accident[field_names.igun]),
            "roadType": int(accident[field_names.road_type]),
            # subtype
            "roadShape": int(accident[field_names.road_shape]),
            # severity
            "dayType": int(accident[field_names.day_type]),
            # locationAccuracy
            "unit": int(accident[field_names.unit]),
            "mainStreet": main_street,
            "secondaryStreet": secondary_street,
            "junction": get_junction(accident, roads),
            "one_lane": get_data_value(accident[field_names.one_lane]),
            "multi_lane": get_data_value(accident[field_names.multi_lane]),
            "speed_limit": get_data_value(accident[field_names.speed_limit]),
            "intactness": get_data_value(accident[field_names.intactness]),
            "road_width": get_data_value(accident[field_names.road_width]),
            "road_sign": get_data_value(accident[field_names.road_sign]),
            "road_light": get_data_value(accident[field_names.road_light]),
            "road_control": get_data_value(accident[field_names.road_control]),
            "weather": get_data_value(accident[field_names.weather]),
            "road_surface": get_data_value(accident[field_names.road_surface]),
            "road_object": get_data_value(accident[field_names.road_object]),
            "object_distance": get_data_value(accident[field_names.object_distance]),
            "didnt_cross": get_data_value(accident[field_names.didnt_cross]),
            "cross_mode": get_data_value(accident[field_names.cross_mode]),
            "cross_location": get_data_value(accident[field_names.cross_location]),
            "cross_direction": get_data_value(accident[field_names.cross_direction]),
        }

        yield marker
    accidents.close()


def get_files(directory):
    for name, filename in lms_files.iteritems():

        if name not in [STREETS, NON_URBAN_INTERSECTION, ACCIDENTS]:
            continue

        files = filter(lambda path: filename.lower() in path.lower(), os.listdir(directory))
        amount = len(files)
        if amount == 0:
            raise ValueError("file not found in directory: " + filename)
        if amount > 1:
            raise ValueError("there are too many matches: " + filename)

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


def import_to_datastore(directory, provider_code, batch_size):
    """
    goes through all the files in a given directory, parses and commits them
    """
    try:
        files_from_lms = dict(get_files(directory))
        if len(files_from_lms) == 0:
            return
        print("importing data from directory: {}".format(directory))
        now = datetime.now()
        accidents = list(import_accidents(provider_code=provider_code, **files_from_lms))
        db.session.execute(Marker.__table__.insert(), accidents)
        db.session.commit()
        took = int((datetime.now() - now).total_seconds())
        print("imported {0} items from directory: {1} in {2} seconds".format(len(accidents), directory, took))
        return accidents;
    except Exception as e:
        directories_not_processes[directory] = e.message


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

# update the RTree, marker index table, for given markers
# markers: if None, pulls all markers from the DB, and update by them. else - a list of id, lat, lng objects, or list of Markers, generation handles both 
def update_markers_index_table(markers=None):
    from sqlalchemy.orm import load_only

    if not markers:
        markers = Marker.query.options(load_only("id", "longitude", "latitude")).all()
        MarkerIndex.delete_indexes()

    marker_indexes = list(_generate_marker_index_list(markers))
    MarkerIndex.insert_indexes(marker_indexes)

def _generate_marker_index_list(markers):
    try:
        for i, marker in enumerate(markers):
            marker_index = {
                # getting the marker data as: marker.id or marker["id"], for Marker object and raw object respectively 
                "id": getattr(marker, "id", marker["id"]),
                "minLng": getattr(marker, "longitude", marker["longitude"]),
                "maxLng": getattr(marker, "longitude", marker["longitude"]),
                "minLat": getattr(marker, "latitude", marker["latitude"]),
                "maxLat": getattr(marker, "latitude", marker["latitude"])
            }
            yield marker_index
    except AttributeError:
        print ("Could not generate marker indexes, unappropriate marker object struture!")
        raise


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
        MarkerIndex.delete_indexes()

    accidents = []
    for directory in glob.glob("{0}/*/*".format(args.path)):
        parent_directory = os.path.basename(os.path.dirname(os.path.join(os.pardir, directory)))
        provider_code = args.provider_code if args.provider_code else get_provider_code(parent_directory)
        imported_accidents = import_to_datastore(directory, provider_code, args.batch_size)
        if imported_accidents != None:
         accidents += imported_accidents 

    failed = ["{0}: {1}".format(directory, fail_reason) for directory, fail_reason in
              directories_not_processes.iteritems()]
    print("finished processing all directories, except: %s" % "\n".join(failed))
    print("creating the respective marker index table using the imported data")
    update_markers_index_table(accidents);


if __name__ == "__main__":
    main()
