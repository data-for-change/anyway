import glob
import json
import logging
import os
import re
import shutil
import traceback
from collections import OrderedDict, defaultdict
from datetime import datetime

import math
import pandas as pd
from sqlalchemy import or_, event
from typing import Dict, List

from anyway.parsers.cbs import preprocessing_cbs_files
from anyway import field_names, localization
from anyway.backend_constants import BE_CONST
from anyway.models import (
    AccidentMarker,
    Involved,
    Vehicle,
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
    ProviderCode,
    VehicleDamage,
    AccidentMarkerView,
    InvolvedView,
    InvolvedMarkerView,
    VehiclesView,
    VehicleMarkerView,
    City,
)
from anyway.parsers.cbs.exceptions import CBSParsingFailed
from anyway.utilities import ItmToWGS84, time_delta, ImporterUI, truncate_tables, delete_all_rows_from_table, \
    chunks, run_query_and_insert_to_table_in_chunks
from anyway.db_views import VIEWS
from anyway.app_and_db import db
from anyway.parsers.cbs.s3 import S3DataRetriever
from anyway.views.safety_data import sd_utils

street_map_type: Dict[int, List[dict]]

failed_dirs = OrderedDict()

CONTENT_ENCODING = "cp1255"
ACCIDENT_TYPE_REGEX = re.compile(r"accidents_type_(?P<type>\d)")
ACCIDENTS_TYPE_PREFIX = "accidents_type"

ACCIDENTS = "accidents"
CITIES = "cities"
STREETS = "streets"
ROADS = "roads"
URBAN_INTERSECTION = "urban_intersection"
NON_URBAN_INTERSECTION = "non_urban_intersection"
NON_URBAN_INTERSECTION_HEBREW = "non_urban_intersection_hebrew"
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
    VEHICLES: "VehData.csv",
}

DICTCOLUMN1 = "MS_TAVLA"
DICTCOLUMN2 = "KOD"
DICTCOLUMN3 = "TEUR"

CLASSES_DICT = {
    0: ColumnsDescription,
    1: PoliceUnit,
    2: RoadType,
    4: AccidentSeverity,
    5: AccidentType,
    9: RoadShape,
    10: OneLane,
    11: MultiLane,
    12: SpeedLimit,
    13: RoadIntactness,
    14: RoadWidth,
    15: RoadSign,
    16: RoadLight,
    17: RoadControl,
    18: Weather,
    19: RoadSurface,
    21: RoadObjecte,
    22: ObjectDistance,
    23: DidntCross,
    24: CrossMode,
    25: CrossLocation,
    26: CrossDirection,
    28: DrivingDirections,
    30: VehicleStatus,
    31: InvolvedType,
    34: SafetyMeasures,
    35: InjurySeverity,
    37: DayType,
    38: DayNight,
    39: DayInWeek,
    40: TrafficLight,
    43: VehicleAttribution,
    45: VehicleType,
    50: InjuredType,
    52: InjuredPosition,
    60: AccidentMonth,
    66: PopulationType,
    67: Sex,
    68: GeoArea,
    77: Region,
    78: MunicipalStatus,
    79: District,
    80: NaturalArea,
    81: YishuvShape,
    92: AgeGroup,
    93: AccidentHourRaw,
    111: EngineVolume,
    112: TotalWeight,
    200: HospitalTime,
    201: MedicalType,
    202: ReleaseDest,
    203: SafetyMeasuresUse,
    204: LateDeceased,
    205: LocationAccuracy,
    229: VehicleDamage,
    245: VehicleType,
}

TABLES_DICT = {
    0: "columns_description",
    1: "police_unit",
    2: "road_type",
    4: "accident_severity",
    5: "accident_type",
    9: "road_shape",
    10: "one_lane",
    11: "multi_lane",
    12: "speed_limit",
    13: "road_intactness",
    14: "road_width",
    15: "road_sign",
    16: "road_light",
    17: "road_control",
    18: "weather",
    19: "road_surface",
    21: "road_object",
    22: "object_distance",
    23: "didnt_cross",
    24: "cross_mode",
    25: "cross_location",
    26: "cross_direction",
    28: "driving_directions",
    30: "vehicle_status",
    31: "involved_type",
    34: "safety_measures",
    35: "injury_severity",
    37: "day_type",
    38: "day_night",
    39: "day_in_week",
    40: "traffic_light",
    43: "vehicle_attribution",
    45: "vehicle_type",
    50: "injured_type",
    52: "injured_position",
    60: "accident_month",
    66: "population_type",
    67: "sex",
    68: "geo_area",
    77: "region",
    78: "municipal_status",
    79: "district",
    80: "natural_area",
    81: "yishuv_shape",
    92: "age_group",
    93: "accident_hour_raw",
    111: "engine_volume",
    112: "total_weight",
    200: "hospital_time",
    201: "medical_type",
    202: "release_dest",
    203: "safety_measures_use",
    204: "late_deceased",
    205: "location_accuracy",
    229: "vehicle_damage",
    245: "vehicle_type",
}

coordinates_converter = ItmToWGS84()


def get_street(yishuv_symbol, street_sign, streets):
    """
    extracts the street name using the settlement id and street id
    """
    if yishuv_symbol not in streets:
        # Changed to return blank string instead of None for correct presentation (Omer)
        return ""
    street_name = [
        x[field_names.street_name]
        for x in streets[yishuv_symbol]
        if x[field_names.street_sign] == street_sign
    ]
    # there should be only one street name, or none if it wasn't found.
    return street_name[0] if len(street_name) == 1 else ""


def get_address(accident, streets):
    """
    extracts the address of the main street.
    tries to build the full address: <street_name> <street_number>, <settlement>,
    but might return a partial one if unsuccessful.
    """
    street = get_street(
        accident.get(field_names.yishuv_symbol), accident.get(field_names.street1), streets
    )
    if not street:
        return ""

    # the house_number field is invalid if it's empty or if it contains 9999
    house_number = (
        int(accident.get(field_names.house_number))
        if not pd.isnull(accident.get(field_names.house_number))
           and int(accident.get(field_names.house_number)) != 9999
        else None
    )
    settlement = City.get_name_from_symbol_or_none(accident.get(field_names.yishuv_symbol))

    if not house_number and not settlement:
        return street
    if not house_number and settlement:
        return "{}, {}".format(street, settlement)
    if house_number and not settlement:
        return "{} {}".format(street, house_number)

    return "{} {}, {}".format(street, house_number, settlement)


def get_streets(accident, streets):
    """
    extracts the streets the accident occurred in.
    every accident has a main street and a secondary street.
    :return: a tuple containing both streets.
    """
    main_street = get_address(accident, streets)
    secondary_street = get_street(
        accident.get(field_names.yishuv_symbol), accident.get(field_names.street2), streets
    )
    return main_street, secondary_street


def get_non_urban_intersection(accident, roads):
    """
    extracts the non-urban-intersection from an accident
    """
    non_urban_intersection_value = accident.get(field_names.non_urban_intersection)
    if non_urban_intersection_value is not None and not math.isnan(non_urban_intersection_value):
        road1 = accident.get(field_names.road1)
        road2 = accident.get(field_names.road2)
        km = accident.get(field_names.km)
        key = (road1, road2, km)
        junction = roads.get(key, None)
        if junction is None:
            road2 = 0 if road2 is None or math.isnan(road2) else road2
            km = 0 if km is None or math.isnan(km) else km
            if road2 == 0 or km == 0:
                key = (road1, road2, km)
                junction = roads.get(key, None)
        return junction
    return None


def get_non_urban_intersection_by_junction_number(accident, non_urban_intersection):
    non_urban_intersection_value = accident.get(field_names.non_urban_intersection)
    if non_urban_intersection_value is not None and not math.isnan(non_urban_intersection_value):
        key = accident.get(field_names.non_urban_intersection)
        junction = non_urban_intersection.get(key, None)
        return junction


def get_junction(accident, roads):
    """
    extracts the junction from an accident
    omerxx: added "km" parameter to the calculation to only show the right junction,
    every non-urban accident shows nearest junction with distance and direction
    :return: returns the junction or None if it wasn't found
    """
    if (
            accident.get(field_names.km) is not None
            and accident.get(field_names.non_urban_intersection) is None
    ):
        min_dist = 100000
        key = (), ()
        junc_km = 0
        for option in roads:
            if (
                    accident.get(field_names.road1) == option[0]
                    and abs(accident["KM"] - option[2]) < min_dist
            ):
                min_dist = abs(accident.get(field_names.km) - option[2])
                key = accident.get(field_names.road1), option[1], option[2]
                junc_km = option[2]
        junction = roads.get(key, None)
        if junction:
            if accident.get(field_names.km) - junc_km > 0:
                direction = "צפונית" if accident.get(field_names.road1) % 2 == 0 else "מזרחית"
            else:
                direction = "דרומית" if accident.get(field_names.road1) % 2 == 0 else "מערבית"
            if abs(float(accident["KM"] - junc_km) / 10) >= 1:
                string = (
                        str(abs(float(accident["KM"]) - junc_km) / 10)
                        + " ק״מ "
                        + direction
                        + " ל"
                        + junction
                )
            elif 0 < abs(float(accident["KM"] - junc_km) / 10) < 1:
                string = (
                        str(int((abs(float(accident.get(field_names.km)) - junc_km) / 10) * 1000))
                        + " מטרים "
                        + direction
                        + " ל"
                        + junction
                )
            else:
                string = junction
            return string
        else:
            return ""

    elif accident.get(field_names.non_urban_intersection) is not None:
        key = (
            accident.get(field_names.road1),
            accident.get(field_names.road2),
            accident.get(field_names.km),
        )
        junction = roads.get(key, None)
        return junction if junction else ""
    else:
        return ""


def parse_date(accident):
    """
    parses an accident's date
    """
    year = int(accident.get(field_names.accident_year))
    month = int(accident.get(field_names.accident_month))
    day = int(accident.get(field_names.accident_day))

    """
    hours calculation explanation - The value of the hours is between 1 to 96.
    These values represent 15 minutes each that start at 00:00:
    1 equals 00:00, 2 equals 00:15, 3 equals 00:30 and so on.
    """
    minutes = accident.get(field_names.accident_hour) * 15 - 15
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
    if bool(accident.get(field_names.urban_intersection)):
        main_street, secondary_street = get_streets(accident, streets)
        if main_street:
            extra_fields[field_names.street1] = main_street
        if secondary_street:
            extra_fields[field_names.street2] = secondary_street

    # if the accident occurred in a non urban setting (highway, etc')
    if bool(accident.get(field_names.non_urban_intersection)):
        junction = get_junction(accident, roads)
        if junction:
            extra_fields[field_names.junction_name] = junction

    # localize static accident values
    for field in localization.get_supported_tables():
        # if we have a localized field for that particular field, save the field value
        # it will be fetched we deserialized
        if accident.get(field) and localization.get_field(field, accident.get(field)):
            extra_fields[field] = accident.get(field)

    return extra_fields


def get_data_value(value):
    """
    :returns: value for parameters which are not mandatory in an accident data
    OR -1 if the parameter value does not exist
    """
    return None if value is None or math.isnan(value) else int(value)


def create_marker(provider_code, accident, streets, roads, non_urban_intersection):
    if field_names.x not in accident or field_names.y not in accident:
        raise ValueError("Missing x and y coordinates")
    if (
            accident.get(field_names.x)
            and not math.isnan(accident.get(field_names.x))
            and accident.get(field_names.y)
            and not math.isnan(accident.get(field_names.y))
    ):
        lng, lat = coordinates_converter.convert(
            accident.get(field_names.x), accident.get(field_names.y)
        )
    else:
        lng, lat = None, None  # Must insert everything to avoid foreign key failure
    main_street, secondary_street = get_streets(accident, streets)
    km = accident.get(field_names.km)
    km = None if km is None or math.isnan(km) else str(km)
    km_accurate = None
    if km is not None:
        km_accurate = False if "-" in km else True
        km = float(km.strip("-"))
    accident_datetime = parse_date(accident)
    file_type_police = accident.get(field_names.file_type_police)
    if file_type_police is None:
        file_type_police = provider_code
    marker = {
        "id": int(accident.get(field_names.id)),
        "provider_and_id": int(str(provider_code) + str(int(accident.get(field_names.id)))),
        "provider_code": provider_code,
        "file_type_police": file_type_police,
        "title": "Accident",
        "description": json.dumps(load_extra_data(accident, streets, roads)),
        "address": get_address(accident, streets),
        "latitude": lat,
        "longitude": lng,
        "accident_type": get_data_value(accident.get(field_names.accident_type)),
        "accident_severity": get_data_value(accident.get(field_names.accident_severity)),
        "created": accident_datetime,
        "location_accuracy": get_data_value(accident.get(field_names.location_accuracy)),
        "road_type": get_data_value(accident.get(field_names.road_type)),
        "road_shape": get_data_value(accident.get(field_names.road_shape)),
        "day_type": get_data_value(accident.get(field_names.day_type)),
        "police_unit": get_data_value(accident.get(field_names.police_unit)),
        "mainStreet": main_street,
        "secondaryStreet": secondary_street,
        "junction": get_junction(accident, roads),
        "one_lane": get_data_value(accident.get(field_names.one_lane)),
        "multi_lane": get_data_value(accident.get(field_names.multi_lane)),
        "speed_limit": get_data_value(accident.get(field_names.speed_limit)),
        "road_intactness": get_data_value(accident.get(field_names.road_intactness)),
        "road_width": get_data_value(accident.get(field_names.road_width)),
        "road_sign": get_data_value(accident.get(field_names.road_sign)),
        "road_light": get_data_value(accident.get(field_names.road_light)),
        "road_control": get_data_value(accident.get(field_names.road_control)),
        "weather": get_data_value(accident.get(field_names.weather)),
        "road_surface": get_data_value(accident.get(field_names.road_surface)),
        "road_object": get_data_value(accident.get(field_names.road_object)),
        "object_distance": get_data_value(accident.get(field_names.object_distance)),
        "didnt_cross": get_data_value(accident.get(field_names.didnt_cross)),
        "cross_mode": get_data_value(accident.get(field_names.cross_mode)),
        "cross_location": get_data_value(accident.get(field_names.cross_location)),
        "cross_direction": get_data_value(accident.get(field_names.cross_direction)),
        "road1": get_data_value(accident.get(field_names.road1)),
        "road2": get_data_value(accident.get(field_names.road2)),
        "km": km,
        "km_raw": get_data_value(accident.get(field_names.km)),
        "km_accurate": km_accurate,
        "yishuv_symbol": get_data_value(accident.get(field_names.yishuv_symbol)),
        "yishuv_name": City.get_name_from_symbol_or_none(accident.get(field_names.yishuv_symbol)),
        "geo_area": get_data_value(accident.get(field_names.geo_area)),
        "day_night": get_data_value(accident.get(field_names.day_night)),
        "day_in_week": get_data_value(accident.get(field_names.day_in_week)),
        "traffic_light": get_data_value(accident.get(field_names.traffic_light)),
        "region": get_data_value(accident.get(field_names.region)),
        "district": get_data_value(accident.get(field_names.district)),
        "natural_area": get_data_value(accident.get(field_names.natural_area)),
        "municipal_status": get_data_value(accident.get(field_names.municipal_status)),
        "yishuv_shape": get_data_value(accident.get(field_names.yishuv_shape)),
        "street1": get_data_value(accident.get(field_names.street1)),
        "street1_hebrew": get_street(
            accident.get(field_names.yishuv_symbol), accident.get(field_names.street1), streets
        ),
        "street2": get_data_value(accident.get(field_names.street2)),
        "street2_hebrew": get_street(
            accident.get(field_names.yishuv_symbol), accident.get(field_names.street2), streets
        ),
        "house_number": get_data_value(accident.get(field_names.house_number)),
        "urban_intersection": get_data_value(accident.get(field_names.urban_intersection)),
        "non_urban_intersection": get_data_value(accident.get(field_names.non_urban_intersection)),
        "non_urban_intersection_hebrew": get_non_urban_intersection(accident, roads),
        "non_urban_intersection_by_junction_number": get_non_urban_intersection_by_junction_number(
            accident, non_urban_intersection
        ),
        "accident_year": get_data_value(accident.get(field_names.accident_year)),
        "accident_month": get_data_value(accident.get(field_names.accident_month)),
        "accident_day": get_data_value(accident.get(field_names.accident_day)),
        "accident_hour_raw": get_data_value(accident.get(field_names.accident_hour)),
        "accident_hour": accident_datetime.hour,
        "accident_minute": accident_datetime.minute,
        "x": accident.get(field_names.x),
        "y": accident.get(field_names.y),
        "vehicle_type_rsa": None,
        "violation_type_rsa": None,
        "geom": None,
    }
    return marker


def import_accidents(provider_code, accidents, streets, roads, non_urban_intersection, **kwargs):
    logging.debug("Importing markers")
    accidents_result = []
    for _, accident in accidents.iterrows():
        marker = create_marker(provider_code, accident, streets, roads, non_urban_intersection)
        accidents_result.append(marker)
    db.session.bulk_insert_mappings(AccidentMarker, accidents_result)
    db.session.commit()
    logging.debug("Finished Importing markers")
    logging.debug("Inserted " + str(len(accidents_result)) + " new accident markers")
    fill_db_geo_data()
    return len(accidents_result)


def import_involved(provider_code, involved, **kwargs):
    logging.debug("Importing involved")
    involved_result = []
    for _, involve in involved.iterrows():
        if not involve.get(field_names.id) or pd.isnull(
                involve.get(field_names.id)
        ):  # skip lines with no accident id
            continue
        file_type_police = involve.get(field_names.file_type_police)
        if file_type_police is None:
            file_type_police = provider_code
        involved_result.append(
            {
                "accident_id": int(involve.get(field_names.id)),
                "provider_and_id": int(str(provider_code) + str(int(involve.get(field_names.id)))),
                "provider_code": provider_code,
                "file_type_police": file_type_police,
                "involved_type": int(involve.get(field_names.involved_type)),
                "license_acquiring_date": int(involve.get(field_names.license_acquiring_date)),
                "age_group": int(involve.get(field_names.age_group)),
                "sex": get_data_value(involve.get(field_names.sex)),
                "vehicle_type": get_data_value(involve.get(field_names.vehicle_type_involved)),
                "safety_measures": get_data_value(involve.get(field_names.safety_measures)),
                "involve_yishuv_symbol": get_data_value(
                    involve.get(field_names.involve_yishuv_symbol)
                ),
                "involve_yishuv_name": City.get_name_from_symbol_or_none(
                    involve.get(field_names.involve_yishuv_symbol)
                ),
                "injury_severity": get_data_value(involve.get(field_names.injury_severity)),
                "injured_type": get_data_value(involve.get(field_names.injured_type)),
                "injured_position": get_data_value(involve.get(field_names.injured_position)),
                "population_type": get_data_value(involve.get(field_names.population_type)),
                "home_region": get_data_value(involve.get(field_names.home_region)),
                "home_district": get_data_value(involve.get(field_names.home_district)),
                "home_natural_area": get_data_value(involve.get(field_names.home_natural_area)),
                "home_municipal_status": get_data_value(
                    involve.get(field_names.home_municipal_status)
                ),
                "home_yishuv_shape": get_data_value(involve.get(field_names.home_yishuv_shape)),
                "hospital_time": get_data_value(involve.get(field_names.hospital_time)),
                "medical_type": get_data_value(involve.get(field_names.medical_type)),
                "release_dest": get_data_value(involve.get(field_names.release_dest)),
                "safety_measures_use": get_data_value(involve.get(field_names.safety_measures_use)),
                "late_deceased": get_data_value(involve.get(field_names.late_deceased)),
                "car_id": get_data_value(involve.get(field_names.car_id)),
                "involve_id": get_data_value(involve.get(field_names.involve_id)),
                "accident_year": get_data_value(involve.get(field_names.accident_year)),
                "accident_month": get_data_value(involve.get(field_names.accident_month)),
            }
        )
    db.session.bulk_insert_mappings(Involved, involved_result)
    db.session.commit()
    logging.debug("Finished Importing involved")
    return len(involved_result)


def import_vehicles(provider_code, vehicles, **kwargs):
    logging.debug("Importing vehicles")
    vehicles_result = []
    for _, vehicle in vehicles.iterrows():
        file_type_police = vehicle.get(field_names.file_type_police)
        if file_type_police is None:
            file_type_police = provider_code
        engine_volume = vehicle.get(field_names.engine_volume)
        if engine_volume is None or math.isnan(engine_volume):
            engine_volume = 0
        vehicles_result.append(
            {
                "accident_id": int(vehicle.get(field_names.id)),
                "provider_and_id": int(str(provider_code) + str(int(vehicle.get(field_names.id)))),
                "provider_code": provider_code,
                "file_type_police": file_type_police,
                "engine_volume": engine_volume,
                "manufacturing_year": get_data_value(vehicle.get(field_names.manufacturing_year)),
                "driving_directions": get_data_value(vehicle.get(field_names.driving_directions)),
                "vehicle_status": get_data_value(vehicle.get(field_names.vehicle_status)),
                "vehicle_attribution": get_data_value(vehicle.get(field_names.vehicle_attribution)),
                "vehicle_type": get_data_value(vehicle.get(field_names.vehicle_type_vehicles)),
                "seats": get_data_value(vehicle.get(field_names.seats)),
                "total_weight": get_data_value(vehicle.get(field_names.total_weight)),
                "car_id": get_data_value(vehicle.get(field_names.car_id)),
                "accident_year": get_data_value(vehicle.get(field_names.accident_year)),
                "accident_month": get_data_value(vehicle.get(field_names.accident_month)),
                "vehicle_damage": get_data_value(vehicle.get(field_names.vehicle_damage)),
            }
        )
    db.session.bulk_insert_mappings(Vehicle, vehicles_result)
    db.session.commit()
    logging.debug("Finished Importing vehicles")
    return len(vehicles_result)


def get_files(directory):
    output_files_dict = {}
    for name, filename in cbs_files.items():
        if name not in (STREETS, NON_URBAN_INTERSECTION, ACCIDENTS, INVOLVED, VEHICLES, DICTIONARY):
            continue
        files = [path for path in os.listdir(directory) if filename.lower() in path.lower()]
        amount = len(files)
        if amount == 0:
            raise ValueError("Not found: '%s'" % filename)
        if amount > 1:
            raise ValueError("Ambiguous: '%s'" % filename)
        file_path = os.path.join(directory, files[0])
        if name == DICTIONARY:
            output_files_dict[name] = read_dictionary(file_path)
        elif name in (ACCIDENTS, INVOLVED, VEHICLES):
            df = pd.read_csv(file_path, encoding=CONTENT_ENCODING)
            df.columns = [column.upper() for column in df.columns]
            output_files_dict[name] = df
        else:
            df = pd.read_csv(file_path, encoding=CONTENT_ENCODING)
            df.columns = [column.upper() for column in df.columns]
            if name == STREETS:
                streets_map = {}
                groups = df.groupby(field_names.settlement)
                for key, settlement in groups:
                    streets_map[key] = [
                        {
                            field_names.street_sign: x[field_names.street_sign],
                            field_names.street_name: str(x[field_names.street_name]),
                        }
                        for _, x in settlement.iterrows() if isinstance(x[field_names.street_name], str) \
                            or ((isinstance(x[field_names.street_name], int) or isinstance(x[field_names.street_name], float)) and x[field_names.street_name] > 0)
                    ]

                output_files_dict[name] = streets_map
            elif name == NON_URBAN_INTERSECTION:
                roads = {
                    (x[field_names.road1], x[field_names.road2], x[field_names.km]): x[
                        field_names.junction_name
                    ]
                    for _, x in df.iterrows()
                }
                non_urban_intersection = {
                    x[field_names.junction]: x[field_names.junction_name] for _, x in df.iterrows()
                }
                output_files_dict[ROADS] = roads
                output_files_dict[NON_URBAN_INTERSECTION] = non_urban_intersection
    return output_files_dict


def import_to_datastore(directory, provider_code, year, batch_size) -> int:
    """
    goes through all the files in a given directory, parses and commits them
    Returns number of new items, and new streets dict.
    """
    try:
        assert batch_size > 0

        files_from_cbs = get_files(directory)
        if len(files_from_cbs) == 0:
            return 0, {}
        logging.debug("Importing '{}'".format(directory))
        started = datetime.now()

        # import dictionary
        fill_dictionary_tables(files_from_cbs[DICTIONARY], provider_code, year)

        new_items = 0
        accidents_count = import_accidents(provider_code=provider_code, **files_from_cbs)
        new_items += accidents_count
        involved_count = import_involved(provider_code=provider_code, **files_from_cbs)
        new_items += involved_count
        vehicles_count = import_vehicles(provider_code=provider_code, **files_from_cbs)
        new_items += vehicles_count

        logging.debug("\t{0} items in {1}".format(new_items, time_delta(started)))
        return new_items
    except ValueError as e:
        failed_dirs[directory] = str(e)
        if "Not found" in str(e):
            return 0
        raise e


def delete_invalid_entries(batch_size):
    """
    deletes all markers in the database with null latitude or longitude
    first deletes from tables Involved and Vehicle, then from table AccidentMarker
    """

    marker_ids_to_delete = (
        db.session.query(AccidentMarker.id)
        .filter(or_((AccidentMarker.longitude == None), (AccidentMarker.latitude == None)))
        .all()
    )

    marker_ids_to_delete = [acc_id[0] for acc_id in marker_ids_to_delete]

    logging.debug("There are " + str(len(marker_ids_to_delete)) + " invalid accident_ids to delete")

    for ids_chunk in chunks(marker_ids_to_delete, batch_size):

        logging.debug("Deleting a chunk of " + str(len(ids_chunk)))

        q = db.session.query(Involved).filter(Involved.accident_id.in_(ids_chunk))
        if q.all():
            logging.debug("deleting invalid entries from Involved")
            q.delete(synchronize_session="fetch")
            db.session.commit()

        q = db.session.query(Vehicle).filter(Vehicle.accident_id.in_(ids_chunk))
        if q.all():
            logging.debug("deleting invalid entries from Vehicle")
            q.delete(synchronize_session="fetch")
            db.session.commit()

        q = db.session.query(AccidentMarker).filter(AccidentMarker.id.in_(ids_chunk))
        if q.all():
            logging.debug("deleting invalid entries from AccidentMarker")
            q.delete(synchronize_session="fetch")
            db.session.commit()


def delete_cbs_entries(start_year, batch_size):
    """
    deletes all CBS markers (provider_code=1 or provider_code=3) in the database created in year and with provider code provider_code
    first deletes from tables Involved and Vehicle, then from table AccidentMarker
    """
    start_date = f"{start_year}-01-01"
    marker_ids_to_delete = (
        db.session.query(AccidentMarker.id)
        .filter(AccidentMarker.created >= datetime.strptime(start_date, "%Y-%m-%d"))
        .filter(
            or_(
                (AccidentMarker.provider_code == BE_CONST.CBS_ACCIDENT_TYPE_1_CODE),
                (AccidentMarker.provider_code == BE_CONST.CBS_ACCIDENT_TYPE_3_CODE),
            )
        )
        .all()
    )

    marker_ids_to_delete = [acc_id[0] for acc_id in marker_ids_to_delete]

    logging.debug(
        "There are "
        + str(len(marker_ids_to_delete))
        + " accident ids to delete starting "
        + str(start_date)
    )

    for ids_chunk in chunks(marker_ids_to_delete, batch_size):

        logging.debug("Deleting a chunk of " + str(len(ids_chunk)))

        q = db.session.query(Involved).filter(Involved.accident_id.in_(ids_chunk))
        if q.all():
            logging.debug("deleting entries from Involved")
            q.delete(synchronize_session=False)
            db.session.commit()

        q = db.session.query(Vehicle).filter(Vehicle.accident_id.in_(ids_chunk))
        if q.all():
            logging.debug("deleting entries from Vehicle")
            q.delete(synchronize_session=False)
            db.session.commit()

        q = db.session.query(AccidentMarker).filter(AccidentMarker.id.in_(ids_chunk))
        if q.all():
            logging.debug("deleting entries from AccidentMarker")
            q.delete(synchronize_session=False)
            db.session.commit()


def fill_db_geo_data():
    """
    Fills empty geometry object according to coordinates in database
    SRID = 4326
    """
    db.session.execute(
        "UPDATE markers SET geom = ST_SetSRID(ST_MakePoint(longitude,latitude),4326)\
                           WHERE geom IS NULL;"
    )
    db.session.commit()


def get_provider_code(directory_name=None):
    if directory_name:
        match = ACCIDENT_TYPE_REGEX.match(directory_name)
        if match:
            return int(match.groupdict()["type"])

    ans = ""
    while not ans.isdigit():
        ans = input("Directory provider code is invalid. Please enter a valid code: ")
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
    for k, v in cbs_dictionary.items():
        if k == 97:
            continue
        try:
            curr_table = TABLES_DICT[k]
        except Exception as _:
            logging.debug(
                "A key " + str(k) + " was added to dictionary - update models, tables and classes"
            )
            continue
        for inner_k, inner_v in v.items():
            if inner_v is None or (isinstance(inner_v, float) and math.isnan(inner_v)):
                continue
            sql_delete = (
                    "DELETE FROM "
                    + curr_table
                    + " WHERE provider_code="
                    + str(provider_code)
                    + " AND year="
                    + str(year)
                    + " AND id="
                    + str(inner_k)
            )
            db.session.execute(sql_delete)
            sql_insert = (
                    "INSERT INTO "
                    + curr_table
                    + " VALUES ("
                    + str(inner_k)
                    + ","
                    + str(year)
                    + ","
                    + str(provider_code)
                    + ","
                    + "'"
                    + inner_v.replace("'", "")
                    + "'"
                    + ")"
                    + " ON CONFLICT DO NOTHING"
            )
            db.session.execute(sql_insert)
    try:
        db.session.commit()
    except Exception as e:
        logging.error(f"Error updating Dictionary tables: {e}")
        db.session.rollback()
    logging.debug("Inserted/Updated dictionary values into table " + curr_table)
    create_provider_code_table()


def truncate_dictionary_tables(dictionary_file):
    cbs_dictionary = read_dictionary(dictionary_file)
    for k, _ in cbs_dictionary.items():
        if k == 97:
            continue
        curr_table = TABLES_DICT[k]
        sql_truncate = "TRUNCATE TABLE " + curr_table
        db.session.execute(sql_truncate)
        db.session.commit()
        logging.debug("Truncated table " + curr_table)


def create_provider_code_table():
    provider_code_table = "provider_code"
    provider_code_class = ProviderCode
    table_entries = db.session.query(provider_code_class)
    table_entries.delete()
    provider_code_dict = {
        1: "הלשכה המרכזית לסטטיסטיקה - סוג תיק 1",
        2: "איחוד הצלה",
        3: "הלשכה המרכזית לסטטיסטיקה - סוג תיק 3",
        4: "שומרי הדרך",
    }
    for k, v in provider_code_dict.items():
        sql_insert = (
                "INSERT INTO " + provider_code_table + " VALUES (" + str(k) + "," + "'" + v + "'" + ")"
        )
        db.session.execute(sql_insert)
    try:
        db.session.commit()
    except Exception as e:
        logging.error(f"Error updating table {provider_code_table}: {e}")
        db.session.rollback()


def receive_rollback(conn, **kwargs):
    """listen for the 'rollback' event"""
    logging.debug(f"rollback in create_tables(). conn:{conn},kw:{kwargs}")
    print("---------------------------------------------")


def create_tables():
    chunk_size = 5000
    try:
        with db.get_engine().begin() as conn:
            event.listen(conn, "rollback", receive_rollback)
            delete_all_rows_from_table(conn, AccidentMarkerView)
            run_query_and_insert_to_table_in_chunks(VIEWS.create_markers_hebrew_view(), AccidentMarkerView,
                                                    AccidentMarker.id, chunk_size, conn)
            logging.debug("after insertion to markers_hebrew ")

            delete_all_rows_from_table(conn, InvolvedView)
            run_query_and_insert_to_table_in_chunks(VIEWS.create_involved_hebrew_view(), InvolvedView,
                                                    Involved.id, chunk_size, conn)
            logging.debug("after insertion to involved_hebrew ")

            delete_all_rows_from_table(conn, VehiclesView)
            run_query_and_insert_to_table_in_chunks(VIEWS.create_vehicles_hebrew_view(),
                                                    VehiclesView, Vehicle.id, chunk_size, conn)
            logging.debug("after insertion to vehicles_hebrew ")

            delete_all_rows_from_table(conn, VehicleMarkerView)
            run_query_and_insert_to_table_in_chunks(VIEWS.create_vehicles_markers_hebrew_view(),
                                                    VehicleMarkerView, VehiclesView.id, chunk_size, conn)
            logging.debug("after insertion to vehicles_markers_hebrew ")

            delete_all_rows_from_table(conn, InvolvedMarkerView)
            run_query_and_insert_to_table_in_chunks(VIEWS.create_involved_hebrew_markers_hebrew_view(),
                                                    InvolvedMarkerView, InvolvedView.accident_id, chunk_size, conn)
            logging.debug("after insertion to involved_markers_hebrew")
            logging.debug("Created DB Hebrew Tables")
    except Exception as e:
        logging.exception(f"Exception while creating hebrew tables, {e}", e)
        raise e


def update_dictionary_tables(path):
    import_ui = ImporterUI(path)
    dir_name = import_ui.source_path()
    dir_list = glob.glob("{0}/*/*".format(dir_name))

    for directory in sorted(dir_list, reverse=True):
        directory_name = os.path.basename(os.path.normpath(directory))
        year = directory_name[1:5] if directory_name[0] == "H" else directory_name[0:4]
        if int(year) < 2008:
            continue
        parent_directory = os.path.basename(os.path.dirname(os.path.join(os.pardir, directory)))
        provider_code = get_provider_code(parent_directory)
        logging.debug("Importing Directory " + directory)
        files_from_cbs = dict(get_files(directory))
        if len(files_from_cbs) == 0:
            return 0
        logging.debug("Filling dictionary for directory '{}'".format(directory))
        fill_dictionary_tables(files_from_cbs[DICTIONARY], provider_code, int(year))


def get_file_type_and_year(file_path):
    df = pd.read_csv(file_path, encoding=CONTENT_ENCODING)
    provider_code = df.iloc[0][field_names.file_type.lower()]
    year = df.loc[:, field_names.accident_year].mode().values[0]
    return int(provider_code), int(year)

def recreate_table_for_location_extraction():
    db.session.execute("""TRUNCATE cbs_locations""")
    db.session.execute("""INSERT INTO cbs_locations
            (SELECT ROW_NUMBER() OVER (ORDER BY road1) as id, LOCATIONS.*
            FROM
            (SELECT DISTINCT road1,
                road2,
                non_urban_intersection_hebrew,
                yishuv_name,
                street1_hebrew,
                street2_hebrew,
                district_hebrew,
                region_hebrew,
                road_segment_name,
                longitude,
                latitude
            FROM markers_hebrew
            WHERE (provider_code=1
                    OR provider_code=3)
                AND (longitude is not null
                    AND latitude is not null)) LOCATIONS)"""
                            )
    db.session.commit()


def main(batch_size, source, load_start_year=None):
    try:
        total = 0
        started = datetime.now()
        if source == "s3":
            if load_start_year is None:
                now = datetime.now()
                load_start_year = now.year - 1
            logging.debug("Importing data from s3...")
            s3_data_retriever = S3DataRetriever()
            s3_data_retriever.get_files_from_s3(start_year=load_start_year)
            delete_cbs_entries(load_start_year, batch_size)
            for provider_code in [
                BE_CONST.CBS_ACCIDENT_TYPE_1_CODE,
                BE_CONST.CBS_ACCIDENT_TYPE_3_CODE,
            ]:
                logging.info(
                    f"Loading min year {s3_data_retriever.min_year} Loading max year {s3_data_retriever.max_year}"
                )
                for year in range(s3_data_retriever.min_year, s3_data_retriever.max_year + 1):
                    cbs_files_dir = os.path.join(
                        s3_data_retriever.local_files_directory,
                        ACCIDENTS_TYPE_PREFIX + "_" + str(provider_code),
                        str(year),
                    )
                    logging.debug("Importing Directory " + cbs_files_dir)
                    preprocessing_cbs_files.update_cbs_files_names(cbs_files_dir)
                    num_new = import_to_datastore(
                        cbs_files_dir, provider_code, year, batch_size
                    )
                    total += num_new
            shutil.rmtree(s3_data_retriever.local_temp_directory)
        elif source == "local_dir_for_tests_only":
            path = "static/data/cbs"
            import_ui = ImporterUI(path)
            dir_name = import_ui.source_path()
            dir_list = glob.glob("{0}/*/*".format(dir_name))

            # wipe all the AccidentMarker and Vehicle and Involved data first
            if import_ui.is_delete_all():
                truncate_tables(db, (Vehicle, Involved, AccidentMarker))
            for directory in sorted(dir_list, reverse=False):
                directory_name = os.path.basename(os.path.normpath(directory))
                year = directory_name[1:5] if directory_name[0] == "H" else directory_name[0:4]
                parent_directory = os.path.basename(
                    os.path.dirname(os.path.join(os.pardir, directory))
                )
                provider_code = get_provider_code(parent_directory)
                logging.debug("Importing Directory " + directory)
                num_new = import_to_datastore(
                    directory, provider_code, int(year), batch_size
                )
                total += num_new

        fill_db_geo_data()
        failed = [
            "\t'{0}' ({1})".format(directory, fail_reason)
            for directory, fail_reason in failed_dirs.items()
        ]
        logging.debug(
            "Finished processing all directories{0}{1}".format(
                ", except:\n" if failed else "", "\n".join(failed)
            )
        )
        logging.debug("Total: {0} items in {1}".format(total, time_delta(started)))
        create_tables()
        logging.debug("Finished Creating Hebrew DB Tables")
        recreate_table_for_location_extraction()
        logging.debug("Finished Recreating tables for location extraction")
        logging.debug("Loading safety data tables")
        sd_utils.load_data()
        logging.debug("Completed load of safety data tables")
    except Exception as ex:
        print("Traceback: {0}".format(traceback.format_exc()))
        raise CBSParsingFailed(message=str(ex))
        # Todo - send an email that an exception occured
