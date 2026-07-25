import glob
import json
import logging
import os
import re
import shutil
import traceback
import zipfile
from collections import OrderedDict
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
from anyway.parsers.cbs.dictionary_tables import read_dictionary, fill_dictionary_tables

street_map_type: Dict[int, List[dict]]

failed_dirs = OrderedDict()

# CBS Hebrew files are encoded in Windows-1255.
CONTENT_ENCODING = "cp1255"


def is_xlsx_file(file_path: str) -> bool:
    if not zipfile.is_zipfile(file_path):
        return False

    with zipfile.ZipFile(file_path) as zf:
        names = set(zf.namelist())

    return (
        "[Content_Types].xml" in names
        and "xl/workbook.xml" in names
    )


def read_cbs_file(file_path: str) -> pd.DataFrame:
    if is_xlsx_file(file_path):
        return pd.read_excel(file_path)

    return pd.read_csv(file_path, encoding=CONTENT_ENCODING)


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

REQUIRED_CBS_FILE_TYPES = (STREETS, ACCIDENTS, INVOLVED, VEHICLES, DICTIONARY)
CBS_PROVIDER_CODES = (
    BE_CONST.CBS_ACCIDENT_TYPE_1_CODE,
    BE_CONST.CBS_ACCIDENT_TYPE_3_CODE,
)


new_to_old_accident_columns = {
    "TeunaID_FKT": "pk_teuna_fikt",
    "SemelSugTikLMS": "sug_tik",
    "IsYosh": "THUM_GEOGRAFI",
    "KodSugMakom": "SUG_DEREH",
    "SemelYishuv1": "SEMEL_YISHUV",
    "SemelRechov1": "REHOV1",
    "SemelRechov2": "REHOV2",
    "Bait": "BAYIT",
    "SemelTzometLMS": "INTERSECTION",
    "SemelKvish1": "KVISH1",
    "SemelKvish2": "KVISH2",
    "Kilometer": "KM",
    "shnatTeuna": "SHNAT_TEUNA",
    "chodeshTeuna": "HODESH_TEUNA",
    "yomBeChodesh": "YOM_BE_HODESH",
    "SemelShaaMekubaz": "SHAA",
    "SugYom": "SUG_YOM",
    "YomLayla": "YOM_LAYLA",
    "YomBashavua": "YOM_BASHAVUA",
    "Merumzar": "RAMZOR",
    "KodChumratTeunaMeshulvet": "HUMRAT_TEUNA",
    "KodSugTeuna": "SUG_TEUNA",
    "KodDerechChadMaslulit": "HAD_MASLUL",
    "KodDerechDuMaslulit": "RAV_MASLUL",
    "KodMehirutMuteret": "MEHIRUT_MUTERET",
    "KodTkinutHaDerech": "TKINUT",
    "KodRochavHakvishBeMeter": "ROHAV",
    "KodTeura": "TEURA",
    "KodTamrurRamzorBetzomet": "BAKARA",
    "KodMezegAvir": "MEZEG_AVIR",
    "KodMatzavPneiHakvish": "PNE_KVISH",
    "KodHitnagshutImEtzemDomem": "SUG_EZEM",
    "KodMerchakHaEtzemMisfatHakvish": "MERHAK_EZEM",
    "SemelMahoz": "MAHOZ",
    "SemelNafa": "NAFA",
    "SemelEzorTivi": "EZOR_TIVI",
    "SemelMaamadMuniOMoeza": "MAAMAD_MINIZIPALI",
    "SemelZuratYeshuvShotef": "ZURAT_ISHUV",
    "StatusIgunMekubatzLMS": "STATUS_IGUN",
    "X_LMS": "X",
    "Y_LMS": "Y",
}

new_to_old_vehicles_columns = {
    "TeunaID_FKT": "pk_teuna_fikt",
    "MisparRechev_FKT": "mispar_rehev_fikt",
    "shnatTeuna": "SHNAT_TEUNA",
    "chodeshTeuna": "HODESH_TEUNA",
    "Nefah": "NEFAH",
    "ShnatYitzurMSV": "SHNAT_YITZUR",
    "KodKivuneNesia": "KIVUNE_NESIA",
    "KodSugLuchit": "SHIYUH_REHEV_LMS",
    "KodChumratHanezek": "NEZEK",
    "SugRechevMekubatzLMS": "SUG_REHEV_LMS",
    "MekomotYeshivaLMS": "MEKOMOT_YESHIVA_LMS",
    "MishkalKolelLMS": "MISHKAL_KOLEL_LMS",
    "SemelSugTikLMS": "SUG_TIK",
}

new_to_old_involved_columns = mapping = {
    "TeunaID_FKT": "pk_teuna_fikt",
    "MisparRechev_FKT": "MISPAR_REHEV_fikt",
    "MisparZehut_FKT": "ZEHUT_fikt",
    "shnatTeuna": "SHNAT_TEUNA",
    "ChodeshTeuna": "HODESH_TEUNA",
    "SugMeoravLMS": "SUG_MEORAV",
    "ShnatHozaa": "SHNAT_HOZAA",
    "SemelKvuzaGil": "KVUZA_GIL",
    "MinMSV": "MIN",
    "SugRechevMekubatzLMS": "SUG_REHEV_NASA_LMS",
    "KodEmtzaeiBetichut": "EMZAE_BETIHUT",
    "SemelYishuvMegurimLMS": "SEMEL_YISHUV_MEGURIM",
    "KodChumratPgiaMeshulevet": "HUMRAT_PGIA",
    "KodSugNifgaNekubatzLMS": "SUG_NIFGA_LMS",
    "KodPeulatNifga": "PEULAT_NIFGA_LMS",
    "KvutzatUchlusiaLMS": "KVUTZAT_OHLUSIYA_LMS",
    "SemelMahozMegurim": "MAHOZ_MEGURIM",
    "SemelNafaMegurim": "NAFA_MEGURIM",
    "SemelEzorTiviMegurim": "EZOR_TIVI_MEGURIM",
    "SemelMaamadMuniOMoezaMegurim": "MAAMAD_MINIZIPALI_MEGURIM",
    "SemelZuratYeshuvShotefMegurim": "ZURAT_ISHUV_MEGURIM",
    "SemelSugTikLMS": "SUG_TIK",
    "ShimushBeAvizareyBetihutLMS": "ShimushBeAvizareyBetihut_LMS",
}

new_to_old_column_mapping = {
    ACCIDENTS: new_to_old_accident_columns,
    VEHICLES: new_to_old_vehicles_columns,
    INVOLVED: new_to_old_involved_columns,
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
        x[field_names.streets_dict.street_name]
        for x in streets[yishuv_symbol]
        if x[field_names.streets_dict.street_sign] == street_sign
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
    if bool(accident.get(field_names.intersection) and accident.get(field_names.street1)):
        main_street, secondary_street = get_streets(accident, streets)
        if main_street:
            extra_fields[field_names.street1] = main_street
        if secondary_street:
            extra_fields[field_names.street2] = secondary_street

    # if the accident occurred in a non urban setting (highway, etc')
    if bool(accident.get(field_names.intersection) and accident.get(field_names.road1)):
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


def _get_single_cbs_filename(file_names, filename):
    files = [
        path
        for path in file_names
        if filename.lower() in path.lower() and not path.startswith(".")
    ]
    amount = len(files)
    if amount == 0:
        raise ValueError("Not found: '%s'" % filename)
    if amount > 1:
        raise ValueError("Ambiguous: '%s'" % filename)
    return files[0]


def _get_single_cbs_file(directory, filename):
    return os.path.join(
        directory,
        _get_single_cbs_filename(os.listdir(directory), filename),
    )


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
        "description": "", #json.dumps(load_extra_data(accident, streets, roads)),
        "address": get_address(accident, streets),
        "latitude": lat,
        "longitude": lng,
        "accident_type": get_data_value(accident.get(field_names.accident_type)),
        "accident_severity": get_data_value(accident.get(field_names.accident_severity)),
        "created": accident_datetime,
        "location_accuracy": get_data_value(accident.get(field_names.location_accuracy)),
        "road_type": get_data_value(accident.get(field_names.road_type)),
        "day_type": get_data_value(accident.get(field_names.day_type)),
        "mainStreet": main_street,
        "secondaryStreet": secondary_street,
        "one_lane": get_data_value(accident.get(field_names.one_lane)),
        "multi_lane": get_data_value(accident.get(field_names.multi_lane)),
        "speed_limit": get_data_value(accident.get(field_names.speed_limit)),
        "road_intactness": get_data_value(accident.get(field_names.road_intactness)),
        "road_width": get_data_value(accident.get(field_names.road_width)),
        "road_light": get_data_value(accident.get(field_names.road_light)),
        "road_control": get_data_value(accident.get(field_names.road_control)),
        "weather": get_data_value(accident.get(field_names.weather)),
        "road_surface": get_data_value(accident.get(field_names.road_surface)),
        "road_object": get_data_value(accident.get(field_names.road_object)),
        "object_distance": get_data_value(accident.get(field_names.object_distance)),
        "road1": get_data_value(accident.get(field_names.road1)),
        "road2": get_data_value(accident.get(field_names.road2)),
        "km": km,
        "km_raw": get_data_value(accident.get(field_names.km)),
        "km_accurate": km_accurate,
        "yishuv_symbol": get_data_value(accident.get(field_names.yishuv_symbol)),
        "yishuv_name": City.get_name_from_symbol_or_none(accident.get(field_names.yishuv_symbol)),
        "yishuv2_symbol": get_data_value(accident.get(field_names.yishuv2_symbol)),
        "yishuv2_name": City.get_name_from_symbol_or_none(accident.get(field_names.yishuv2_symbol)),
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
        "intersection": get_data_value(accident.get(field_names.intersection)),
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
        "entrance_exit": get_data_value(accident.get(field_names.entrance_exit)),
        "infrastructure_type": get_data_value(accident.get(field_names.infrastructure_type)),
        "road_alignment": get_data_value(accident.get(field_names.road_alignment)),
        "road_geometry": get_data_value(accident.get(field_names.road_geometry)),
    }
    return marker


def import_accidents(provider_code, accidents, streets, roads=None, non_urban_intersection=None, **kwargs):
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
                "license_acquiring_date": get_data_value(involve.get(field_names.license_acquiring_date)),
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
                "didnt_cross": get_data_value(involve.get(field_names.didnt_cross)),
                "cross_mode": get_data_value(involve.get(field_names.cross_mode)),
                "cross_location": get_data_value(involve.get(field_names.cross_location)),
                "cross_direction": get_data_value(involve.get(field_names.cross_direction)),
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
                "vehicle_attribution": get_data_value(vehicle.get(field_names.vehicle_attribution)),
                "vehicle_type": get_data_value(vehicle.get(field_names.vehicle_type_vehicles)),
                "seats": get_data_value(vehicle.get(field_names.seats)),
                "total_weight": get_data_value(vehicle.get(field_names.total_weight)),
                "car_id": get_data_value(vehicle.get(field_names.car_id)),
                "accident_year": get_data_value(vehicle.get(field_names.accident_year)),
                "accident_month": get_data_value(vehicle.get(field_names.accident_month)),
                "vehicle_damage": get_data_value(vehicle.get(field_names.vehicle_damage)),
                "vehicle_purpose": get_data_value(vehicle.get(field_names.vehicle_purpose)),
            }
        )
    db.session.bulk_insert_mappings(Vehicle, vehicles_result)
    db.session.commit()
    logging.debug("Finished Importing vehicles")
    return len(vehicles_result)


def get_files(directory):
    def read_streets(df):
        fields = field_names.streets_dict
        streets_map = {}
        groups = df.groupby(field_names.settlement.upper())
        for key, settlement in groups:
            streets_map[key] = [
                {
                    fields.street_sign: x[fields.street_sign],
                    fields.street_name: str(x[fields.street_name]),
                }
                for _, x in settlement.iterrows() if isinstance(x[fields.street_name], str) \
                    or ((isinstance(x[fields.street_name], int) or isinstance(x[fields.street_name], float)) and x[field_names.street_name] > 0)
            ]
        return {STREETS: streets_map}

    def read_non_urban_intersection(df):
        roads = {
            (x[field_names.road1], x[field_names.road2], x[field_names.km]): x[
                field_names.junction_name
            ]
            for _, x in df.iterrows()
        }
        non_urban_intersection = {
            x[field_names.junction]: x[field_names.junction_name] for _, x in df.iterrows()
        }
        return {ROADS: roads, NON_URBAN_INTERSECTION: non_urban_intersection}

    custom_handlers = {
        STREETS: read_streets,
        NON_URBAN_INTERSECTION: read_non_urban_intersection,
    }
    output_files_dict = {}
    #removed NON_URBAN_INTERSECTION
    for name, filename in cbs_files.items():
        if name not in REQUIRED_CBS_FILE_TYPES:
            continue
        file_path = None
        try:
            file_path = _get_single_cbs_file(directory, filename)
            if name == DICTIONARY:
                output_files_dict[name] = read_dictionary(file_path)
            else:
                df = read_cbs_file(file_path)
                if name in new_to_old_column_mapping:
                    df.rename(columns=new_to_old_column_mapping[name], inplace=True)
                df.columns = [column.upper() for column in df.columns]
                if name in custom_handlers:
                    output = custom_handlers[name](df)
                    output_files_dict.update(output)
                else:
                    output_files_dict[name] = df
        except Exception:
            logging.exception(
                "Exception while processing file '%s'",
                file_path or filename,
            )
            raise
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


def get_file_type_and_year(file_path):
    df = read_cbs_file(file_path)
    logging.debug(f"df: {df.columns}")
    provider_code = df.iloc[0][field_names.new_file_type]
    year = df.loc[:, field_names.new_accident_year].mode().values[0]
    return int(provider_code), int(year)

def recreate_table_for_location_extraction():
    db.session.execute("""TRUNCATE cbs_locations""")
    db.session.execute("""INSERT INTO cbs_locations
            (SELECT ROW_NUMBER() OVER (ORDER BY road1) as id, LOCATIONS.*
            FROM
            (SELECT DISTINCT road1,
                road2,
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


def _validate_s3_files(s3_data_retriever, load_start_year, allow_missing):
    if (
        s3_data_retriever.min_year is None
        or s3_data_retriever.max_year is None
    ):
        raise ValueError("No CBS files were downloaded from S3")

    validation_errors = []
    for provider_code in CBS_PROVIDER_CODES:
        for year in range(int(load_start_year), s3_data_retriever.current_year + 1):
            cbs_files_dir = os.path.join(
                s3_data_retriever.local_files_directory,
                ACCIDENTS_TYPE_PREFIX + "_" + str(provider_code),
                str(year),
            )
            if not os.path.isdir(cbs_files_dir):
                if allow_missing:
                    logging.warning(
                        "CBS files directory does not exist; skipping validation: %s",
                        cbs_files_dir,
                    )
                else:
                    validation_errors.append(
                        "{}: directory not found".format(cbs_files_dir)
                    )
                continue

            preprocessing_cbs_files.update_cbs_files_names(cbs_files_dir)
            for file_type in REQUIRED_CBS_FILE_TYPES:
                try:
                    _get_single_cbs_file(cbs_files_dir, cbs_files[file_type])
                except ValueError as error:
                    validation_errors.append(
                        "{}: {}".format(cbs_files_dir, error)
                    )

    if validation_errors:
        raise ValueError(
            "Required CBS files validation failed:\n{}".format(
                "\n".join(validation_errors)
            )
        )


def _validate_required_files_in_s3(
    s3_data_retriever,
    load_start_year,
    load_end_year,
    allow_missing=False,
):
    validation_errors = []
    for provider_code in CBS_PROVIDER_CODES:
        for year in range(load_start_year, load_end_year + 1):
            s3_directory = (
                f"{ACCIDENTS_TYPE_PREFIX}_{provider_code}/{year}/"
            )
            file_names = s3_data_retriever.get_file_names_from_s3(
                provider_code,
                year,
            )
            if not file_names:
                if allow_missing:
                    logging.warning(
                        "CBS S3 directory does not exist or is empty; "
                        "skipping validation: %s",
                        s3_directory,
                    )
                else:
                    validation_errors.append(
                        "{}: directory not found or empty".format(s3_directory)
                    )
                continue

            file_names = [
                preprocessing_cbs_files.get_updated_cbs_file_name(file_name)
                for file_name in file_names
            ]
            for file_type in REQUIRED_CBS_FILE_TYPES:
                try:
                    _get_single_cbs_filename(
                        file_names,
                        cbs_files[file_type],
                    )
                except ValueError as error:
                    validation_errors.append(
                        "{}: {}".format(s3_directory, error)
                    )

    if validation_errors:
        raise ValueError(
            "Required CBS files validation in S3 failed:\n{}".format(
                "\n".join(validation_errors)
            )
        )

    logging.info(
        "Validated required CBS files in S3 for years %s-%s",
        load_start_year,
        load_end_year,
    )


def validate_required_files_in_s3(load_start_year=None, load_end_year=None):
    s3_data_retriever = S3DataRetriever()
    if load_start_year is None:
        load_start_year = s3_data_retriever.current_year - 1
    if load_end_year is None:
        load_end_year = s3_data_retriever.current_year

    load_start_year = int(load_start_year)
    load_end_year = int(load_end_year)
    if load_start_year > load_end_year:
        raise ValueError("load_start_year must not be after load_end_year")

    _validate_required_files_in_s3(
        s3_data_retriever,
        load_start_year,
        load_end_year,
    )


def _import_from_s3(batch_size, load_start_year, allow_missing):
    if load_start_year is None:
        load_start_year = datetime.now().year - 1
    logging.debug("Importing data from s3...")
    s3_data_retriever = S3DataRetriever()
    _validate_required_files_in_s3(
        s3_data_retriever,
        int(load_start_year),
        s3_data_retriever.current_year,
        allow_missing=allow_missing,
    )
    s3_data_retriever.get_files_from_s3(start_year=load_start_year)
    _validate_s3_files(s3_data_retriever, load_start_year, allow_missing)
    delete_cbs_entries(load_start_year, batch_size)

    total = 0
    for provider_code in CBS_PROVIDER_CODES:
        logging.info(
            f"Loading min year {s3_data_retriever.min_year} Loading max year {s3_data_retriever.max_year}"
        )
        for year in range(s3_data_retriever.min_year, s3_data_retriever.max_year + 1):
            cbs_files_dir = os.path.join(
                s3_data_retriever.local_files_directory,
                ACCIDENTS_TYPE_PREFIX + "_" + str(provider_code),
                str(year),
            )
            if allow_missing and not os.path.exists(cbs_files_dir):
                logging.warning(
                    "CBS files directory does not exist; skipping: %s", cbs_files_dir
                )
                continue
            logging.debug("Importing Directory " + cbs_files_dir)
            preprocessing_cbs_files.update_cbs_files_names(cbs_files_dir)
            total += import_to_datastore(cbs_files_dir, provider_code, year, batch_size)

    shutil.rmtree(s3_data_retriever.local_temp_directory)
    return total


def _import_from_local_dir(batch_size):
    path = "static/data/cbs"
    import_ui = ImporterUI(path)
    dir_name = import_ui.source_path()
    dir_list = glob.glob("{0}/*/*".format(dir_name))

    if import_ui.is_delete_all():
        truncate_tables(db, (Vehicle, Involved, AccidentMarker))

    total = 0
    for directory in sorted(dir_list, reverse=False):
        directory_name = os.path.basename(os.path.normpath(directory))
        year = directory_name[1:5] if directory_name[0] == "H" else directory_name[0:4]
        parent_directory = os.path.basename(
            os.path.dirname(os.path.join(os.pardir, directory))
        )
        provider_code = get_provider_code(parent_directory)
        logging.debug("Importing Directory " + directory)
        total += import_to_datastore(directory, provider_code, int(year), batch_size)
    return total


def _log_import_summary(total, started):
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


def _build_hebrew_tables_and_derived_data():
    fill_db_geo_data()
    create_tables()
    logging.debug("Finished Creating Hebrew DB Tables")
    recreate_table_for_location_extraction()
    logging.debug("Finished Recreating tables for location extraction")
    logging.debug("Loading safety data tables")
    sd_utils.load_data()
    logging.debug("Completed load of safety data tables")


def main(batch_size, source, load_start_year=None, allow_missing=False):
    try:
        started = datetime.now()

        if source == "s3":
            total = _import_from_s3(batch_size, load_start_year, allow_missing)
        elif source == "local_dir_for_tests_only":
            total = _import_from_local_dir(batch_size)
        else:
            raise ValueError(f"Unsupported source: {source}")

        _log_import_summary(total, started)
        _build_hebrew_tables_and_derived_data()
    except Exception as ex:
        print("Traceback: {0}".format(traceback.format_exc()))
        raise CBSParsingFailed(message=str(ex))
        # Todo - send an email that an exception occured



