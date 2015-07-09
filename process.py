# -*- coding: utf-8 -*-
from __future__ import print_function
import glob
import os
import argparse
import json
from flask.ext.sqlalchemy import SQLAlchemy
import field_names
from models import Marker,Involved,Vehicle
import models
from utilities import ProgressSpinner, ItmToWGS84, init_flask, CsvReader
import itertools
import localization
import re
from datetime import datetime
from collections import OrderedDict

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
INVOLVED = "involved"
VEHICLES = "vehicles"

lms_files = {
    ACCIDENTS: "AccData.csv",
    URBAN_INTERSECTION: "IntersectUrban.csv",
    NON_URBAN_INTERSECTION: "IntersectNonUrban.csv",
    STREETS: "DicStreets.csv",
    DICTIONARY: "Dictionary.csv",
    INVOLVED: "InvData.csv",
    VEHICLES: "VehData.csv"
}

acc_years = []
coordinates_converter = ItmToWGS84()
app = init_flask(__name__)
db = SQLAlchemy(app)
acc_years = []


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
    omerxx: added "km" parameter to the calculation to only show the right junction,
    every non-urban accident shows nearest junction with distance and direction
    :return: returns the junction or None if it wasn't found
    """
    if accident["KM"] is not None and accident[field_names.non_urban_intersection] is None:
        min_dist = 100000
        key = (), ()
        junc_km = 0
        for option in roads:
            if accident[field_names.road1] == option[0] and abs(accident["KM"]-option[2]) < min_dist:
                min_dist = abs(accident["KM"]-option[2])
                key = accident[field_names.road1], option[1], option[2]
                junc_km = option[2]
        junction = roads.get(key, None)
        if junction:
            if accident["KM"] - junc_km > 0:
                direction = u"צפונית" if accident[field_names.road1] % 2 == 0 else u"מזרחית"
            else:
                direction = u"דרומית" if accident[field_names.road1] % 2 == 0 else u"מערבית"
            if abs(float(accident["KM"] - junc_km)/10) >= 1:
                string = str(abs(float(accident["KM"])-junc_km)/10) + u" ק״מ " + direction + u" ל" + \
                    junction.decode(content_encoding)
            elif 0 < abs(float(accident["KM"] - junc_km)/10) < 1:
                string = str(int((abs(float(accident["KM"])-junc_km)/10)*1000)) + u" מטרים " + direction + u" ל" + \
                    junction.decode(content_encoding)
            else:
                string = junction.decode(content_encoding)
            return string
        else:
            return u""

    elif accident[field_names.non_urban_intersection] is not None:
        key = accident[field_names.road1], accident[field_names.road2], accident["KM"]
        junction = roads.get(key, None)
        return junction.decode(content_encoding) if junction else u""
    else:
        return u""


def parse_date(accident):
    """
    parses an accident's date
    """
    year = accident[field_names.accident_year]
    month = accident[field_names.accident_month]
    day = accident[field_names.accident_day]

    '''
    hours calculation explanation - The value of the hours is between 1 to 96.
    These values represent 15 minutes each that start at 00:00 so 1 equals 00:00, 2 equals 00:15, 3 equals 00:30 and so on. .
    '''
    minutes = accident[field_names.accident_hour] * 15 - 15
    hours = int(minutes // 60)
    minutes %= 60
    accident_date = datetime(year, month, day, hours, minutes, 0)
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
        # if we have a localized field for that particular field, save the field value
        # it will be fetched we deserialized
        if accident[field] and localization.get_field(field, accident[field]):
            extra_fields[field] = accident[field]

    return extra_fields


def get_data_value(value):
    """
    :returns: value for parameters which are not mandatory in an accident data
    OR -1 if the parameter value does not exist
    """
    return int(value) if value else -1


def create_years_list():
    """
    Edits 'years.js', a years structure ready to be presented in app.js
    as user's last-4-years filter choices.
    """
    acc_years_dict = OrderedDict()
    for i, year in enumerate(reversed(acc_years)):
        if i < 4:
            acc_years_dict["שנת" + " %s" % year] = ["01/01/%s" % year, "31/12/%s" % year]
    with open('static/js/years.js', 'w') as outfile:
        outfile.write("var ACCYEARS = ")
        json.dump(acc_years_dict, outfile, encoding='utf-8')
        outfile.write(";\n")


def import_accidents(provider_code, accidents, streets, roads, **kwargs):
    global acc_years
    print("reading accidents from file %s" % (accidents.name(),))
    for accident in accidents:
        if field_names.x_coordinate not in accident or field_names.y_coordinate not in accident:
            raise ValueError("x and y coordinates are missing from the accidents file!")
        if not accident[field_names.x_coordinate] or not accident[field_names.y_coordinate]:
            continue
        lng, lat = coordinates_converter.convert(accident[field_names.x_coordinate], accident[field_names.y_coordinate])
        main_street, secondary_street = get_streets(accident, streets)
        if accident[field_names.accident_year] not in acc_years:
            acc_years.append(accident[field_names.accident_year])

        marker = {
            "id": int(accident[field_names.id]),
            "provider_code": int(provider_code),
            "title": "Accident",
            "description": json.dumps(load_extra_data(accident, streets, roads), encoding=models.db_encoding),
            "address": get_address(accident, streets),
            "latitude": lat,
            "longitude": lng,
            "subtype": int(accident[field_names.accident_type]),
            "severity": int(accident[field_names.accident_severity]),
            "created": parse_date(accident),
            "locationAccuracy": int(accident[field_names.igun]),
            "roadType": int(accident[field_names.road_type]),
            "roadShape": int(accident[field_names.road_shape]),
            "dayType": int(accident[field_names.day_type]),
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

def import_involved(provider_code, involved, **kwargs):
    print("reading involved data from file %s" % (involved.name(),))
    for involve in involved:
        if not involve[field_names.id]:
            continue
        involved_item = {
            "accident_id": int(involve[field_names.id]),
            "provider_code": int(provider_code),
            "involved_type": int(involve[field_names.involved_type]),
            "license_acquiring_date": int(involve[field_names.license_acquiring_date]),
            "age_group": int(involve[field_names.age_group]),
            "sex": get_data_value(involve[field_names.sex]),
            "car_type": get_data_value(involve[field_names.car_type]),
            "safety_measures": get_data_value(involve[field_names.safety_measures]),
            "home_city": get_data_value(involve[field_names.home_city]),
            "injury_severity": get_data_value(involve[field_names.injury_severity]),
            "injured_type": get_data_value(involve[field_names.injured_type]),
            "Injured_position": get_data_value(involve[field_names.injured_position]),
            "population_type": get_data_value(involve[field_names.population_type]),
            "home_district": get_data_value(involve[field_names.home_district]),
            "home_nafa": get_data_value(involve[field_names.home_nafa]),
            "home_area": get_data_value(involve[field_names.home_area]),
            "home_municipal_status": get_data_value(involve[field_names.home_municipal_status]),
            "home_residence_type":  get_data_value(involve[field_names.home_residence_type]),
            "hospital_time":  get_data_value(involve[field_names.hospital_time]),
            "medical_type":  get_data_value(involve[field_names.medical_type]),
            "release_dest":  get_data_value(involve[field_names.release_dest]),
            "safety_measures_use":  get_data_value(involve[field_names.safety_measures_use]),
            "late_deceased":  get_data_value(involve[field_names.late_deceased]),
        }
        yield involved_item
    involved.close()


def import_vehicles(provider_code, vehicles, **kwargs):
    print("reading involved data from file %s" % (vehicles.name(),))
    for vehicle in vehicles:
        vehicle_item = {
            "accident_id": int(vehicle[field_names.id]),
            "provider_code": int(provider_code),
            "engine_volume": int(vehicle[field_names.engine_volume]),
            "manufacturing_year": get_data_value(vehicle[field_names.manufacturing_year]),
            "driving_directions": get_data_value(vehicle[field_names.driving_directions]),
            "vehicle_status": get_data_value(vehicle[field_names.vehicle_status]),
            "vehicle_attribution": get_data_value(vehicle[field_names.vehicle_attribution]),
            "vehicle_type": get_data_value(vehicle[field_names.vehicle_type]),
            "seats": get_data_value(vehicle[field_names.seats]),
            "total_weight": get_data_value(vehicle[field_names.total_weight]),
        }
        yield vehicle_item
    vehicles.close()

def get_files(directory):
    for name, filename in lms_files.iteritems():

        if name not in (STREETS, NON_URBAN_INTERSECTION, ACCIDENTS, INVOLVED, VEHICLES):
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
            roads = {(x[field_names.road1], x[field_names.road2], x["KM"]): x[field_names.junction_name] for x in csv if
                     field_names.road1 in x and field_names.road2 in x}
            csv.close()
            yield ROADS, roads
        elif name == ACCIDENTS:
            yield name, csv
        elif name == INVOLVED:
            yield name, csv
        elif name == VEHICLES:
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
        involved = list(import_involved(provider_code=provider_code, **files_from_lms))
        db.session.execute(Involved.__table__.insert(), involved)
        db.session.commit()
        vehicles = list(import_vehicles(provider_code=provider_code, **files_from_lms))
        db.session.execute(Vehicle.__table__.insert(), vehicles)
        db.session.commit()
        took = int((datetime.now() - now).total_seconds())
        print("imported {0} items from directory: {1} in {2} seconds".format(len(accidents)+len(involved)+len(vehicles),
                                                                             directory, took))
    except ValueError as e:
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', type=str, default="static/data/lms")
    parser.add_argument('--batch_size', type=int, default=100)
    parser.add_argument('--delete_all', dest='delete_all', action='store_true', default=True)
    parser.add_argument('--provider_code', type=int)
    args = parser.parse_args()
    # wipe all the Markers and Involved data first
    if args.delete_all:
        tables = (Vehicle, Involved, Marker)
        for table in tables:
            print("deleting table: " + table.__name__)
            db.session.query(table).delete()
            db.session.commit()

    for directory in glob.glob("{0}/*/*".format(args.path)):
        parent_directory = os.path.basename(os.path.dirname(os.path.join(os.pardir, directory)))
        provider_code = args.provider_code if args.provider_code else get_provider_code(parent_directory)
        import_to_datastore(directory, provider_code, args.batch_size)

    failed = ["{0}: {1}".format(directory, fail_reason) for directory, fail_reason in
              directories_not_processes.iteritems()]
    print("finished processing all directories, except: %s" % "\n".join(failed))
    create_years_list()

if __name__ == "__main__":
    main()
