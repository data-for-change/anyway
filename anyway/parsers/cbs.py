# -*- coding: utf-8 -*-
import glob
import os
import json
from collections import OrderedDict, defaultdict
import re
from datetime import datetime
import six
from six import iteritems
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
import pandas as pd
import math
from .. import field_names, localization
from ..models import (AccidentMarker,
                      Involved,
                      Vehicle,
                      AccidentsNoLocation,
                      InvolvedNoLocation,
                      VehicleNoLocation,
                      ColumnsDescription,
                      PoliceUnit,
                      RoadType,
                      AccidentSeverity,
                      AccidentType,
                      RoadShape,
                      OneLane,
                      MultiLane,
                      SpeedLimit,
                      RoadIntactness,
                      RoadWidth,
                      RoadSign,
                      RoadLight,
                      RoadControl,
                      Weather,
                      RoadSurface,
                      RoadObjecte,
                      ObjectDistance,
                      DidntCross,
                      CrossMode,
                      CrossLocation,
                      CrossDirection,
                      DrivingDirections,
                      VehicleStatus,
                      InvolvedType,
                      SafetyMeasures,
                      InjurySeverity,
                      DayType,
                      DayNight,
                      DayInWeek,
                      TrafficLight,
                      VehicleAttribution,
                      VehicleType,
                      InjuredType,
                      InjuredPosition,
                      AccidentMonth,
                      PopulationType,
                      Sex,
                      GeoArea,
                      Region,
                      MunicipalStatus,
                      District,
                      NaturalArea,
                      YishuvShape,
                      AgeGroup,
                      AccidentHourRaw,
                      EngineVolume,
                      TotalWeight,
                      HospitalTime,
                      MedicalType,
                      ReleaseDest,
                      SafetyMeasuresUse,
                      LateDeceased,
                      LocationAccuracy,
                      ProviderCode)

from .. import models
from ..constants import CONST
from ..views import VIEWS
from ..utilities import ItmToWGS84, init_flask, time_delta,ImporterUI,truncate_tables,chunks
from functools import partial
import logging

failed_dirs = OrderedDict()

CONTENT_ENCODING = 'cp1255'
ACCIDENT_TYPE_REGEX = re.compile(r"accidents_type_(?P<type>\d)")

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

DICTCOLUMN1 = "MS_TAVLA"
DICTCOLUMN2 = "KOD"
DICTCOLUMN3 = "TEUR"

CLASSES_DICT = {0:   ColumnsDescription,
               1:   PoliceUnit,
               2:   RoadType,
               4:   AccidentSeverity,
               5:   AccidentType,
               9:   RoadShape,
               10:  OneLane,
               11:  MultiLane,
               12:  SpeedLimit,
               13:  RoadIntactness,
               14:  RoadWidth,
               15:  RoadSign,
               16:  RoadLight,
               17:  RoadControl,
               18:  Weather,
               19:  RoadSurface,
               21:  RoadObjecte,
               22:  ObjectDistance,
               23:  DidntCross,
               24:  CrossMode,
               25:  CrossLocation,
               26:  CrossDirection,
               28:  DrivingDirections,
               30:  VehicleStatus,
               31:  InvolvedType,
               34:  SafetyMeasures,
               35:  InjurySeverity,
               37:  DayType,
               38:  DayNight,
               39:  DayInWeek,
               40:  TrafficLight,
               43:  VehicleAttribution,
               45:  VehicleType,
               50:  InjuredType,
               52:  InjuredPosition,
               60:  AccidentMonth,
               66:  PopulationType,
               67:  Sex,
               68:  GeoArea,
               77:  Region,
               78:  MunicipalStatus,
               79:  District,
               80:  NaturalArea,
               81:  YishuvShape,
               92:  AgeGroup,
               93:  AccidentHourRaw,
               111: EngineVolume,
               112: TotalWeight,
               200: HospitalTime,
               201: MedicalType,
               202: ReleaseDest,
               203: SafetyMeasuresUse,
               204: LateDeceased,
               205: LocationAccuracy,
}

TABLES_DICT = {0:   'columns_description',
               1:   'police_unit',
               2:   'road_type',
               4:   'accident_severity',
               5:   'accident_type',
               9:   'road_shape',
               10:  'one_lane',
               11:  'multi_lane',
               12:  'speed_limit',
               13:  'road_intactness',
               14:  'road_width',
               15:  'road_sign',
               16:  'road_light',
               17:  'road_control',
               18:  'weather',
               19:  'road_surface',
               21:  'road_object',
               22:  'object_distance',
               23:  'didnt_cross',
               24:  'cross_mode',
               25:  'cross_location',
               26:  'cross_direction',
               28:  'driving_directions',
               30:  'vehicle_status',
               31:  'involved_type',
               34:  'safety_measures',
               35:  'injury_severity',
               37:  'day_type',
               38:  'day_night',
               39:  'day_in_week',
               40:  'traffic_light',
               43:  'vehicle_attribution',
               45:  'vehicle_type',
               50:  'injured_type',
               52:  'injured_position',
               60:  'accident_month',
               66:  'population_type',
               67:  'sex',
               68:  'geo_area',
               77:  'region',
               78:  'municipal_status',
               79:  'district',
               80:  'natural_area',
               81:  'yishuv_shape',
               92:  'age_group',
               93:  'accident_hour_raw',
               111: 'engine_volume',
               112: 'total_weight',
               200: 'hospital_time',
               201: 'medical_type',
               202: 'release_dest',
               203: 'safety_measures_use',
               204: 'late_deceased',
               205: 'location_accuracy',
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
    street_name = [x[field_names.street_name] for x in streets[settlement_sign] if
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
    home = int(accident[field_names.home]) if not pd.isnull(accident[field_names.home]) \
                                              and int(accident[field_names.home]) != 9999  else None
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

def get_non_urban_intersection(accident, roads):
    """
    extracts the non-urban-intersection from an accident
    """
    if accident[field_names.non_urban_intersection] is not None:
        key = accident[field_names.road1], accident[field_names.road2], accident[field_names.km]
        junction = roads.get(key, None)
        return junction if junction else u""
    return u""

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
                    junction
            elif 0 < abs(float(accident["KM"] - junc_km)/10) < 1:
                string = str(int((abs(float(accident["KM"])-junc_km)/10)*1000)) + u" מטרים " + direction + u" ל" + \
                    junction
            else:
                string = junction
            return string
        else:
            return u""

    elif accident[field_names.non_urban_intersection] is not None:
        key = accident[field_names.road1], accident[field_names.road2], accident[field_names.km]
        junction = roads.get(key, None)
        return junction if junction else u""
    else:
        return u""


def parse_date(accident):
    """
    parses an accident's date
    """
    year = int(accident[field_names.accident_year])
    month = int(accident[field_names.accident_month])
    day = int(accident[field_names.accident_day])

    '''
    hours calculation explanation - The value of the hours is between 1 to 96.
    These values represent 15 minutes each that start at 00:00:
    1 equals 00:00, 2 equals 00:15, 3 equals 00:30 and so on.
    '''
    minutes = accident[field_names.accident_hour] * 15 - 15
    hours = int(minutes // 60)
    minutes %= 60
    minutes = int(minutes)
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
    return int(value) if value and not math.isnan(value) else -1


def import_accidents(provider_code, accidents, streets, roads, **kwargs):
    markers = []
    markers_no_location = []
    for _,accident in accidents.iterrows():
        if field_names.x_coordinate not in accident or field_names.y_coordinate not in accident:
            raise ValueError("Missing x and y coordinates")
        if accident[field_names.x_coordinate] and not math.isnan(accident[field_names.x_coordinate]) \
        and accident[field_names.y_coordinate] and not math.isnan(accident[field_names.y_coordinate]):
            lng, lat = coordinates_converter.convert(accident[field_names.x_coordinate],
                                                     accident[field_names.y_coordinate])
        else:
            lng, lat = None, None   # Must insert everything to avoid foreign key failure
        main_street, secondary_street = get_streets(accident, streets)

        assert(int(provider_code) == int(accident[field_names.file_type]))
        accident_datetime = parse_date(accident)
        marker = {
            "id": int(accident[field_names.id]),
            "provider_and_id": int(str(int(provider_code)) + str(int(accident[field_names.id]))),
            "provider_code": int(provider_code),
            "title": "Accident",
            "description": json_dumps(load_extra_data(accident, streets, roads)),
            "address": get_address(accident, streets),
            "latitude": lat,
            "longitude": lng,
            "accident_type": int(accident[field_names.accident_type]),
            "accident_severity": int(accident[field_names.accident_severity]),
            "created": accident_datetime,
            "location_accuracy": int(accident[field_names.igun]),
            "road_type": int(accident[field_names.road_type]),
            "road_shape": int(accident[field_names.road_shape]),
            "day_type": int(accident[field_names.day_type]),
            "police_unit": int(accident[field_names.police_unit]),
            "mainStreet": main_street,
            "secondaryStreet": secondary_street,
            "junction": get_junction(accident, roads),
            "one_lane": get_data_value(accident[field_names.one_lane]),
            "multi_lane": get_data_value(accident[field_names.multi_lane]),
            "speed_limit": get_data_value(accident[field_names.speed_limit]),
            "road_intactness": get_data_value(accident[field_names.road_intactness]),
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
            "km": float(accident[field_names.km]) if accident[field_names.km] and not math.isnan(accident[field_names.km]) else -1,
            "yishuv_symbol": get_data_value(accident[field_names.yishuv_symbol]),
            "yishuv_name": localization.get_city_name(accident[field_names.settlement_sign]),
            "geo_area": get_data_value(accident[field_names.geo_area]),
            "day_night": get_data_value(accident[field_names.day_night]),
            "day_in_week": get_data_value(accident[field_names.day_in_week]),
            "traffic_light": get_data_value(accident[field_names.traffic_light]),
            "region": get_data_value(accident[field_names.region]),
            "district": get_data_value(accident[field_names.district]),
            "natural_area": get_data_value(accident[field_names.natural_area]),
            "municipal_status": get_data_value(accident[field_names.municipal_status]),
            "yishuv_shape": get_data_value(accident[field_names.yishuv_shape]),
            "street1": get_data_value(accident[field_names.street1]),
            "street1_hebrew": get_street(accident[field_names.settlement_sign], accident[field_names.street1], streets),
            "street2": get_data_value(accident[field_names.street2]),
            "street2_hebrew": get_street(accident[field_names.settlement_sign], accident[field_names.street2], streets),
            "home": get_data_value(accident[field_names.home]),
            "urban_intersection": get_data_value(accident[field_names.urban_intersection]),
            "non_urban_intersection": get_data_value(accident[field_names.non_urban_intersection]),
            "non_urban_intersection_hebrew": get_non_urban_intersection(accident, roads),
            "accident_year": get_data_value(accident[field_names.accident_year]),
            "accident_month": get_data_value(accident[field_names.accident_month]),
            "accident_day": get_data_value(accident[field_names.accident_day]),
            "accident_hour_raw": get_data_value(accident[field_names.accident_hour]),
            "accident_hour": accident_datetime.hour,
            "accident_minute": accident_datetime.minute,
            "x": accident[field_names.x_coordinate],
            "y": accident[field_names.y_coordinate],
            "vehicle_type_rsa": None,
            "violation_type_rsa": None,
            "geom": None,
        }

        markers.append(marker)

        if (lng, lat) == (None, None):
            markers_no_location.append(marker)
    return markers, markers_no_location


def import_involved(provider_code, involved, **kwargs):
    involved_result = []
    for _,involve in involved.iterrows():
        if not involve[field_names.id] or pd.isnull(involve[field_names.id]):  # skip lines with no accident id
            continue
        assert(int(provider_code) == int(involve[field_names.file_type]))
        involved_result.append({
            "accident_id": int(involve[field_names.id]),
            "provider_and_id": int(str(int(provider_code)) + str(int(involve[field_names.id]))),
            "provider_code": int(provider_code),
            "involved_type": int(involve[field_names.involved_type]),
            "license_acquiring_date": int(involve[field_names.license_acquiring_date]),
            "age_group": int(involve[field_names.age_group]),
            "sex": get_data_value(involve[field_names.sex]),
            "vehicle_type": get_data_value(involve[field_names.vehicle_type_involved]),
            "safety_measures": get_data_value(involve[field_names.safety_measures]),
            "involve_yishuv_symbol": get_data_value(involve[field_names.involve_yishuv_symbol]),
            "involve_yishuv_name": localization.get_city_name(involve[field_names.involve_yishuv_symbol]),
            "injury_severity": get_data_value(involve[field_names.injury_severity]),
            "injured_type": get_data_value(involve[field_names.injured_type]),
            "injured_position": get_data_value(involve[field_names.injured_position]),
            "population_type": get_data_value(involve[field_names.population_type]),
            "home_region": get_data_value(involve[field_names.home_region]),
            "home_district": get_data_value(involve[field_names.home_district]),
            "home_natural_area": get_data_value(involve[field_names.home_natural_area]),
            "home_municipal_status": get_data_value(involve[field_names.home_municipal_status]),
            "home_residence_type": get_data_value(involve[field_names.home_residence_type]),
            "hospital_time": get_data_value(involve[field_names.hospital_time]),
            "medical_type": get_data_value(involve[field_names.medical_type]),
            "release_dest": get_data_value(involve[field_names.release_dest]),
            "safety_measures_use": get_data_value(involve[field_names.safety_measures_use]),
            "late_deceased": get_data_value(involve[field_names.late_deceased]),
            "car_id": get_data_value(involve[field_names.car_id]),
            "involve_id": get_data_value(involve[field_names.involve_id]),
            "accident_year": get_data_value(involve[field_names.accident_year]),
            "accident_month": get_data_value(involve[field_names.accident_month]),

        })
    return involved_result


def import_vehicles(provider_code, vehicles, **kwargs):
    vehicles_result = []
    for _,vehicle in vehicles.iterrows():
        assert(int(provider_code) == int(vehicle[field_names.file_type]))
        vehicles_result.append({
            "accident_id": int(vehicle[field_names.id]),
            "provider_and_id": int(str(int(provider_code)) + str(int(vehicle[field_names.id]))),
            "provider_code": int(provider_code),
            "engine_volume": int(vehicle[field_names.engine_volume]),
            "manufacturing_year": get_data_value(vehicle[field_names.manufacturing_year]),
            "driving_directions": get_data_value(vehicle[field_names.driving_directions]),
            "vehicle_status": get_data_value(vehicle[field_names.vehicle_status]),
            "vehicle_attribution": get_data_value(vehicle[field_names.vehicle_attribution]),
            "vehicle_type": get_data_value(vehicle[field_names.vehicle_type_vehicles]),
            "seats": get_data_value(vehicle[field_names.seats]),
            "total_weight": get_data_value(vehicle[field_names.total_weight]),
            "car_id": get_data_value(vehicle[field_names.car_id]),
            "accident_year": get_data_value(vehicle[field_names.accident_year]),
            "accident_month": get_data_value(vehicle[field_names.accident_month]),
        })
    return vehicles_result


def get_files(directory):
    for name, filename in iteritems(cbs_files):
        if name not in (STREETS, NON_URBAN_INTERSECTION, ACCIDENTS, INVOLVED, VEHICLES, DICTIONARY):
            continue
        files = [path for path in os.listdir(directory)
                 if filename.lower() in path.lower()]
        amount = len(files)
        if amount == 0:
            raise ValueError("Not found: '%s'" % filename)
        if amount > 1:
            raise ValueError("Ambiguous: '%s'" % filename)
        file_path = os.path.join(directory, files[0])
        if name == DICTIONARY:
            yield name, read_dictionary(file_path)
        df = pd.read_csv(file_path, encoding=CONTENT_ENCODING)
        df.columns = [column.upper() for column in df.columns]
        if name == STREETS:
            streets_map = {}
            groups = df.groupby(field_names.settlement)
            for key, settlement in groups:
                streets_map[key] = [{field_names.street_sign: x[field_names.street_sign],
                                     field_names.street_name: x[field_names.street_name]} for _,x in settlement.iterrows()]

            yield name, streets_map
        elif name == NON_URBAN_INTERSECTION:
            roads = {(x[field_names.road1], x[field_names.road2], x["KM"]): x[field_names.junction_name] for _,x in df.iterrows()}
            yield ROADS, roads
        elif name in (ACCIDENTS, INVOLVED, VEHICLES):
            yield name, df

def import_to_datastore(directory, provider_code, year, batch_size):
    """
    goes through all the files in a given directory, parses and commits them
    """
    try:
        assert batch_size > 0

        files_from_cbs = dict(get_files(directory))
        if len(files_from_cbs) == 0:
            return 0
        logging.info("Importing '{}'".format(directory))
        started = datetime.now()

        # import dictionary
        fill_dictionary_tables(files_from_cbs[DICTIONARY], provider_code, year)

        new_items = 0
        accidents, accidents_no_location = import_accidents(provider_code=provider_code, **files_from_cbs)

        all_existing_accidents_ids = set(map(lambda x: x[0],
                                             db.session.query(AccidentMarker.provider_and_id).all()))
        accidents = [accident for accident in accidents if accident['provider_and_id'] not in all_existing_accidents_ids]
        logging.info('inserting ' + str(len(accidents)) + ' new accidents')
        for accidents_chunk in chunks(accidents, batch_size):
            db.session.bulk_insert_mappings(AccidentMarker, accidents_chunk)
        new_items += len(accidents)

        all_involved_accident_ids = set(map(lambda x: x[0], db.session.query(Involved.provider_and_id).all()))
        involved = import_involved(provider_code=provider_code, **files_from_cbs)
        involved = [x for x in involved if x['provider_and_id'] not in all_involved_accident_ids]

        logging.info('inserting ' + str(len(involved)) + ' new involved')
        for involved_chunk in chunks(involved, batch_size):
            db.session.bulk_insert_mappings(Involved, involved_chunk)
        new_items += len(involved)

        all_vehicles_accident_ids = set(map(lambda x: x[0], db.session.query(Vehicle.provider_and_id).all()))
        vehicles = import_vehicles(provider_code=provider_code, **files_from_cbs)
        vehicles = [x for x in vehicles if x['provider_and_id'] not in all_vehicles_accident_ids]
        logging.info('inserting ' + str(len(vehicles)) + ' new vehicles')
        for vehicles_chunk in chunks(vehicles, batch_size):
            db.session.bulk_insert_mappings(Vehicle, vehicles_chunk)
        new_items += len(vehicles)


        all_existing_accidents_ids_without_location = set(map(lambda x: x[0],
                                                              db.session.query(AccidentsNoLocation.provider_and_id).all()))
        accidents_no_location = [accident for accident in accidents_no_location \
                                if accident['provider_and_id'] not in all_existing_accidents_ids_without_location]
        accidents_no_location_ids = [accident['provider_and_id'] for accident in accidents_no_location]
        logging.info('inserting ' + str(len(accidents_no_location)) + ' accidents without location')
        for accidents_chunk in chunks(accidents_no_location, batch_size):
            db.session.bulk_insert_mappings(AccidentsNoLocation, accidents_chunk)

        involved_no_location = [x for x in involved if x['provider_and_id'] in accidents_no_location_ids]
        logging.info('inserting ' + str(len(involved_no_location)) + ' involved without accident location')
        for involved_chunk in chunks(involved_no_location, batch_size):
            db.session.bulk_insert_mappings(InvolvedNoLocation, involved_chunk)

        vehicles_no_location = [x for x in vehicles if x['provider_and_id'] in accidents_no_location_ids]
        logging.info('inserting ' + str(len(vehicles_no_location)) + ' vehicles without accident location')
        for vehicles_chunk in chunks(vehicles_no_location, batch_size):
            db.session.bulk_insert_mappings(VehicleNoLocation, vehicles_chunk)

        logging.info("\t{0} items in {1}".format(new_items, time_delta(started)))
        return new_items
    except ValueError as e:
        failed_dirs[directory] = str(e)
        if "Not found" in str(e):
            return 0
        raise(e)


def delete_invalid_entries(batch_size):
    """
    deletes all markers in the database with null latitude or longitude
    first deletes from tables Involved and Vehicle, then from table AccidentMarker
    """

    marker_ids_to_delete = db.session.query(AccidentMarker.id).filter(or_((AccidentMarker.longitude == None),
                                                    (AccidentMarker.latitude  == None))).all()

    marker_ids_to_delete = [acc_id[0] for acc_id in marker_ids_to_delete]

    logging.info('There are ' + str(len(marker_ids_to_delete)) + ' invalid accident_ids to delete')

    for ids_chunk in chunks(marker_ids_to_delete, batch_size):

        logging.info('Deleting a chunk of ' + str(len(ids_chunk)))

        q = db.session.query(Involved).filter(Involved.accident_id.in_(ids_chunk))
        if q.all():
            logging.info('deleting invalid entries from Involved')
            q.delete(synchronize_session='fetch')
            db.session.commit()

        q = db.session.query(Vehicle).filter(Vehicle.accident_id.in_(ids_chunk))
        if q.all():
            logging.info('deleting invalid entries from Vehicle')
            q.delete(synchronize_session='fetch')
            db.session.commit()

        q = db.session.query(AccidentMarker).filter(AccidentMarker.id.in_(ids_chunk))
        if q.all():
            logging.info('deleting invalid entries from AccidentMarker')
            q.delete(synchronize_session='fetch')
            db.session.commit()

def delete_cbs_entries(start_date, batch_size):
    """
    deletes all CBS markers (provider_code=1 or provider_code=3) in the database with created date >= start_date
    start_date is a string in the format of '%Y-%m-%d', for example, January 2nd 2018: start_date='2018-01-02'
    first deletes from tables Involved and Vehicle, then from table AccidentMarker
    """

    marker_ids_to_delete = db.session.query(AccidentMarker.id)\
                                     .filter(AccidentMarker.created >= datetime.strptime(start_date, '%Y-%m-%d')) \
                                     .filter(or_((AccidentMarker.provider_code == CONST.CBS_ACCIDENT_TYPE_1_CODE), \
                                             (AccidentMarker.provider_code == CONST.CBS_ACCIDENT_TYPE_3_CODE))).all()

    marker_ids_to_delete = [acc_id[0] for acc_id in marker_ids_to_delete]

    logging.info('There are ' + str(len(marker_ids_to_delete)) + ' accident ids to delete starting ' + str(start_date))

    for ids_chunk in chunks(marker_ids_to_delete, batch_size):

        logging.info('Deleting a chunk of ' + str(len(ids_chunk)))

        q = db.session.query(Involved).filter(Involved.accident_id.in_(ids_chunk))
        if q.all():
            logging.info('deleting entries from Involved')
            q.delete(synchronize_session=False)
            db.session.commit()

        q = db.session.query(Vehicle).filter(Vehicle.accident_id.in_(ids_chunk))
        if q.all():
            logging.info('deleting entries from Vehicle')
            q.delete(synchronize_session=False)
            db.session.commit()

        q = db.session.query(AccidentMarker).filter(AccidentMarker.id.in_(ids_chunk))
        if q.all():
            logging.info('deleting entries from AccidentMarker')
            q.delete(synchronize_session=False)
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


def read_dictionary(dictionary_file):
    cbs_dictionary = defaultdict(dict)
    dictionary = pd.read_csv(dictionary_file, encoding=CONTENT_ENCODING)
    for _, dic in dictionary.iterrows():
        cbs_dictionary[int(dic[DICTCOLUMN1])][int(dic[DICTCOLUMN2])] = dic[DICTCOLUMN3]
    return cbs_dictionary

def fill_dictionary_tables(cbs_dictionary, provider_code, year):
    if year < 2008:
        return
    for k,v in cbs_dictionary.iteritems():
        if k == 97:
            continue
        try:
            curr_table = TABLES_DICT[k]
            curr_class = CLASSES_DICT[k]
        except:
            logging.ERROR('A key ' + str(k) + ' was added to dictionary - update models, tables and classes')
            continue
        for inner_k,inner_v in v.iteritems():
            sql_delete = 'DELETE FROM ' + curr_table + ' WHERE provider_code=' + str(provider_code) + ' AND year=' + str(year)
            db.session.execute(sql_delete)
            db.session.commit()
            sql_insert = 'INSERT INTO ' + curr_table + ' VALUES (' + str(inner_k) + ',' +  str(year) + ',' + str(provider_code) + ',' + "'" + inner_v.replace("'",'') + "'"  + ')' + ' ON CONFLICT DO NOTHING'
            db.session.execute(sql_insert)
            db.session.commit()
        logging.info('Inserted/Updated dictionary values into table ' + curr_table)
    create_provider_code_table()

def truncate_dictionary_tables(dictionary_file):
    cbs_dictionary = read_dictionary(dictionary_file)
    for k,v in cbs_dictionary.iteritems():
        if k == 97:
            continue
        curr_table = TABLES_DICT[k]
        curr_class = CLASSES_DICT[k]
        sql_truncate = 'TRUNCATE TABLE ' + curr_table
        db.session.execute(sql_truncate)
        db.session.commit()
        logging.info('Truncated table ' + curr_table)

def create_provider_code_table():
    provider_code_table = 'provider_code'
    provider_code_class = ProviderCode
    table_entries = db.session.query(provider_code_class)
    table_entries.delete()
    provider_code_dict = {1: u'הלשכה המרכזית לסטטיסטיקה - סוג תיק 1', 2: u'איחוד הצלה', 3: u'הלשכה המרכזית לסטטיסטיקה - סוג תיק 3', 4: u'שומרי הדרך'}
    for k, v in provider_code_dict.items():
        sql_insert = 'INSERT INTO ' + provider_code_table + ' VALUES (' + str(k) + ',' + "'" + v + "'" + ')'
        db.session.execute(sql_insert)
        db.session.commit()

def create_views():
    db.session.execute('CREATE OR REPLACE VIEW markers_hebrew AS ' + VIEWS.MARKERS_HEBREW_VIEW)
    db.session.execute('CREATE OR REPLACE VIEW involved_hebrew AS ' + VIEWS.INVOLVED_HEBREW_VIEW)
    #TODO - Add vehicles_hebrew view after reloading the data
    #db.session.execute('CREATE OR REPLACE VIEW vehicles_hebrew AS ' + VIEWS.VEHICLES_HEBREW_VIEW)
    db.session.commit()

def update_dictionary_tables(path):
    import_ui = ImporterUI(path)
    dir_name = import_ui.source_path()
    dir_list = glob.glob("{0}/*/*".format(dir_name))

    for directory in sorted(dir_list, reverse=True):
        directory_name = os.path.basename(os.path.normpath(directory))
        year = directory_name[1:5] if directory_name[0] == 'H' else directory_name[0:4]
        parent_directory = os.path.basename(os.path.dirname(os.path.join(os.pardir, directory)))
        provider_code = get_provider_code(parent_directory)
        logging.info("Importing Directory " + directory)
        files_from_cbs = dict(get_files(directory))
        if len(files_from_cbs) == 0:
            return 0
        logging.info("Filling dictionary for directory '{}'".format(directory))
        fill_dictionary_tables(files_from_cbs[DICTIONARY], provider_code, int(year))

def main(specific_folder, delete_all, path, batch_size, delete_start_date, load_start_year):

    import_ui = ImporterUI(path, specific_folder, delete_all)
    dir_name = import_ui.source_path()

    if specific_folder:
        dir_list = [dir_name]
    else:
        dir_list = glob.glob("{0}/*/*".format(dir_name))

    # wipe all the AccidentMarker and Vehicle and Involved data first
    if import_ui.is_delete_all():
        truncate_tables(db, (Vehicle, Involved, AccidentMarker))
    elif delete_start_date is not None:
        delete_cbs_entries(delete_start_date, batch_size)
    started = datetime.now()
    total = 0
    for directory in sorted(dir_list, reverse=True):
        directory_name = os.path.basename(os.path.normpath(directory))
        year = directory_name[1:5] if directory_name[0] == 'H' else directory_name[0:4]
        if int(year) >= int(load_start_year):
            parent_directory = os.path.basename(os.path.dirname(os.path.join(os.pardir, directory)))
            provider_code = get_provider_code(parent_directory)
            logging.info("Importing Directory " + directory)
            total += import_to_datastore(directory, provider_code, int(year), batch_size)
        else:
            logging.info('Importing only starting year {0}. Directory {1} has year {2}'.format(load_start_year,
                                                                                               directory_name,
                                                                                               year))

    delete_invalid_entries(batch_size)

    fill_db_geo_data()

    failed = ["\t'{0}' ({1})".format(directory, fail_reason) for directory, fail_reason in
              iteritems(failed_dirs)]
    logging.info("Finished processing all directories{0}{1}".format(", except:\n" if failed else "",
                                                                    "\n".join(failed)))
    logging.info("Total: {0} items in {1}".format(total, time_delta(started)))

    create_views()
