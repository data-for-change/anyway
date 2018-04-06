# -*- coding: utf-8 -*-
import glob
import os
import json
from collections import OrderedDict
import itertools
import re
from datetime import datetime
import six
from six import iteritems
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_

from .. import field_names, localization
from ..models import AccidentMarker, Involved, Vehicle
from .. import models
from ..utilities import ItmToWGS84, init_flask, CsvReader, time_delta, decode_hebrew,ImporterUI,truncate_tables
from functools import partial
import logging

failed_dirs = OrderedDict()

CONTENT_ENCODING = 'cp1255'
ACCIDENT_TYPE_REGEX = re.compile(r"Accidents Type (?P<type>\d)")

ACCIDENTS = 'accidents'
CITIES = 'cities'
STREETS = 'streets'
ROADS = "roads"
URBAN_INTERSECTION = 'urban_intersection'
NON_URBAN_INTERSECTION = 'non_urban_intersection'
DICTIONARY = "dictionary"
INVOLVED = "involved"
VEHICLES = "vehicles"

cbs_files = {
    ACCIDENTS: "AccData.csv",
    URBAN_INTERSECTION: "IntersectUrban.csv",
    NON_URBAN_INTERSECTION: "IntersectNonUrban.csv",
    STREETS: "DicStreets.csv",
    DICTIONARY: "Dictionary.csv",
    INVOLVED: "InvData.csv",
    VEHICLES: "VehData.csv"
}

coordinates_converter = ItmToWGS84()
app = init_flask()
db = SQLAlchemy(app)

json_dumps = partial(json.dumps, encoding=models.db_encoding) if six.PY2 else json.dumps

def get_street(settlement_sign, street_sign, streets):
    """
    extracts the street name using the settlement id and street id
    """
    if settlement_sign not in streets:
        # Changed to return blank string instead of None for correct presentation (Omer)
        return u""
    street_name = [decode_hebrew(x[field_names.street_name]) for x in streets[settlement_sign] if
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
                    decode_hebrew(junction)
            elif 0 < abs(float(accident["KM"] - junc_km)/10) < 1:
                string = str(int((abs(float(accident["KM"])-junc_km)/10)*1000)) + u" מטרים " + direction + u" ל" + \
                    decode_hebrew(junction)
            else:
                string = decode_hebrew(junction)
            return string
        else:
            return u""

    elif accident[field_names.non_urban_intersection] is not None:
        key = accident[field_names.road1], accident[field_names.road2], accident["KM"]
        junction = roads.get(key, None)
        return decode_hebrew(junction) if junction else u""
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
    These values represent 15 minutes each that start at 00:00:
    1 equals 00:00, 2 equals 00:15, 3 equals 00:30 and so on.
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


def import_accidents(provider_code, accidents, streets, roads, **kwargs):
    logging.info("\tReading accident data from '%s'..." % os.path.basename(accidents.name()))
    markers = []
    for accident in accidents:
        if field_names.x_coordinate not in accident or field_names.y_coordinate not in accident:
            raise ValueError("Missing x and y coordinates")
        if accident[field_names.x_coordinate] and accident[field_names.y_coordinate]:
            lng, lat = coordinates_converter.convert(accident[field_names.x_coordinate],
                                                     accident[field_names.y_coordinate])
        else:
            lng, lat = None, None   # Must insert everything to avoid foreign key failure
        main_street, secondary_street = get_streets(accident, streets)

        assert(int(provider_code) == int(accident[field_names.file_type]))

        marker = {
            "id": int(accident[field_names.id]),
            "provider_code": int(provider_code),
            "title": "Accident",
            "description": json_dumps(load_extra_data(accident, streets, roads)),
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
            "road1": get_data_value(accident[field_names.road1]),
            "road2": get_data_value(accident[field_names.road2]),
            "km": float(accident[field_names.km]) if accident[field_names.km] else None,
            "yishuv_symbol": get_data_value(accident[field_names.yishuv_symbol]),
            "geo_area": get_data_value(accident[field_names.geo_area]),
            "day_night": get_data_value(accident[field_names.day_night]),
            "day_in_week": get_data_value(accident[field_names.day_in_week]),
            "traffic_light": get_data_value(accident[field_names.traffic_light]),
            "region": get_data_value(accident[field_names.region]),
            "district": get_data_value(accident[field_names.district]),
            "natural_area": get_data_value(accident[field_names.natural_area]),
            "minizipali_status": get_data_value(accident[field_names.minizipali_status]),
            "yishuv_shape": get_data_value(accident[field_names.yishuv_shape]),
            "geom": None,
        }

        markers.append(marker)

    return markers


def import_involved(provider_code, involved, **kwargs):
    logging.info("\tReading involved data from '%s'..." % os.path.basename(involved.name()))
    involved_result = []
    for involve in involved:
        if not involve[field_names.id]:  # skip lines with no accident id
            continue
        involved_result.append({
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
            "home_residence_type": get_data_value(involve[field_names.home_residence_type]),
            "hospital_time": get_data_value(involve[field_names.hospital_time]),
            "medical_type": get_data_value(involve[field_names.medical_type]),
            "release_dest": get_data_value(involve[field_names.release_dest]),
            "safety_measures_use": get_data_value(involve[field_names.safety_measures_use]),
            "late_deceased": get_data_value(involve[field_names.late_deceased]),
        })
    return involved_result


def import_vehicles(provider_code, vehicles, **kwargs):
    logging.info("\tReading vehicles data from '%s'..." % os.path.basename(vehicles.name()))
    vehicles_result = []
    for vehicle in vehicles:
        vehicles_result.append({
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
        })
    return vehicles_result


def get_files(directory):
    for name, filename in iteritems(cbs_files):

        if name not in (STREETS, NON_URBAN_INTERSECTION, ACCIDENTS, INVOLVED, VEHICLES):
            continue

        files = [path for path in os.listdir(directory)
                 if filename.lower() in path.lower()]
        amount = len(files)
        if amount == 0:
            raise ValueError("Not found: '%s'" % filename)
        if amount > 1:
            raise ValueError("Ambiguous: '%s'" % filename)

        csv = CsvReader(os.path.join(directory, files[0]), encoding="cp1255")

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
        elif name in (ACCIDENTS, INVOLVED, VEHICLES):
            yield name, csv

def chunks(l, n, xrange):
    """Yield successive n-sized chunks from l."""
    for i in xrange(0, len(l), n):
        yield l[i:i + n]


def import_to_datastore(directory, provider_code, batch_size):
    """
    goes through all the files in a given directory, parses and commits them
    """
    try: xrange
    except NameError:
        xrange = range
    try:
        assert batch_size > 0

        files_from_cbs = dict(get_files(directory))
        if len(files_from_cbs) == 0:
            return 0
        logging.info("Importing '{}'".format(directory))
        started = datetime.now()

        new_items = 0

        all_existing_accidents_ids = set(map(lambda x: x[0], db.session.query(AccidentMarker.id).all()))
        accidents = import_accidents(provider_code=provider_code, **files_from_cbs)
        accidents = [accident for accident in accidents if accident['id'] not in all_existing_accidents_ids]
        new_items += len(accidents)
        for accidents_chunk in chunks(accidents, batch_size, xrange):
            db.session.bulk_insert_mappings(AccidentMarker, accidents_chunk)

        all_involved_accident_ids = set(map(lambda x: x[0], db.session.query(Involved.accident_id).all()))
        involved = import_involved(provider_code=provider_code, **files_from_cbs)
        involved = [x for x in involved if x['accident_id'] not in all_involved_accident_ids]
        for involved_chunk in chunks(involved, batch_size, xrange):
            db.session.bulk_insert_mappings(Involved, involved_chunk)
        new_items += len(involved)

        all_vehicles_accident_ids = set(map(lambda x: x[0], db.session.query(Vehicle.accident_id).all()))
        vehicles = import_vehicles(provider_code=provider_code, **files_from_cbs)
        vehicles = [x for x in vehicles if x['accident_id'] not in all_vehicles_accident_ids]
        for vehicles_chunk in chunks(vehicles, batch_size, xrange):
            db.session.bulk_insert_mappings(Vehicle, vehicles_chunk)
        new_items += len(vehicles)

        logging.info("\t{0} items in {1}".format(new_items, time_delta(started)))
        return new_items
    except ValueError as e:
        failed_dirs[directory] = str(e)
        return 0


def delete_invalid_entries():
    """
    deletes all markers in the database with null latitude or longitude
    first deletes from tables Involved and Vehicle, then from table AccidentMarker
    """

    marker_ids_to_delete = db.session.query(AccidentMarker.id).filter(or_((AccidentMarker.longitude == None),
                                                    (AccidentMarker.latitude  == None))).all()

    marker_ids_to_delete = [acc_id[0] for acc_id in marker_ids_to_delete]

    q = db.session.query(Involved).filter(Involved.accident_id.in_(marker_ids_to_delete))

    if q.all():
        print('deleting invalid entries from Involved')
        q.delete(synchronize_session='fetch')

    q = db.session.query(Vehicle).filter(Vehicle.accident_id.in_(marker_ids_to_delete))

    if q.all():
        print('deleting invalid entries from Vehicle')
        q.delete(synchronize_session='fetch')

    q = db.session.query(AccidentMarker).filter(AccidentMarker.id.in_(marker_ids_to_delete))

    if q.all():
        print('deleting invalid entries from AccidentMarker')
        q.delete(synchronize_session='fetch')

    db.session.commit()

def fill_db_geo_data():
    """
    Fills empty geometry object according to coordinates in database
    """
    db.session.execute('UPDATE markers SET geom = ST_SetSRID(ST_MakePoint(longitude,latitude),4326)\
                           WHERE geom IS NULL;')
    db.session.commit()

def get_provider_code(directory_name=None):
    if directory_name:
        match = ACCIDENT_TYPE_REGEX.match(directory_name)
        if match:
            return int(match.groupdict()['type'])

    ans = ""
    while not ans.isdigit():
        ans = six.moves.input("Directory provider code is invalid. Please enter a valid code: ")
        if ans.isdigit():
            return int(ans)


def main(specific_folder, delete_all, path, batch_size):
    import_ui = ImporterUI(path, specific_folder, delete_all)
    dir_name = import_ui.source_path()

    if specific_folder:
        dir_list = [dir_name]
    else:
        dir_list = glob.glob("{0}/*/*".format(dir_name))

    # wipe all the AccidentMarker and Vehicle and Involved data first
    if import_ui.is_delete_all():
        truncate_tables(db, (Vehicle, Involved, AccidentMarker))

    started = datetime.now()
    total = 0
    for directory in dir_list:
        parent_directory = os.path.basename(os.path.dirname(os.path.join(os.pardir, directory)))
        provider_code = get_provider_code(parent_directory)
        total += import_to_datastore(directory, provider_code, batch_size)

    delete_invalid_entries()

    fill_db_geo_data()

    failed = ["\t'{0}' ({1})".format(directory, fail_reason) for directory, fail_reason in
              iteritems(failed_dirs)]
    logging.info("Finished processing all directories{0}{1}".format(", except:\n" if failed else "",
                                                                    "\n".join(failed)))
    logging.info("Total: {0} items in {1}".format(total, time_delta(started)))
