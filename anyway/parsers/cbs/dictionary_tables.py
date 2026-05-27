import glob
import logging
import math
import os
import re
from collections import defaultdict

from anyway.app_and_db import db
from anyway.models import ProviderCode
from anyway.utilities import ImporterUI

DICTCOLUMN1 = "ms_tavla"
DICTCOLUMN2 = "kod"
DICTCOLUMN3 = "teur"
ACCIDENT_TYPE_REGEX = re.compile(r"accidents_type_(?P<type>\d)")
DICTIONARY_FILENAME = "Dictionary.csv"

TABLES_DICT = {
    0: "columns_description",
    2: "road_type",
    3: "entrance_exit",
    4: "accident_severity",
    5: "accident_type",
    6: "road_alignment",
    7: "infrastructure_type",
    8: "road_geometry",
    10: "one_lane",
    11: "multi_lane",
    12: "speed_limit",
    13: "road_intactness",
    14: "road_width",
    16: "road_light",
    17: "road_control",
    18: "weather",
    19: "road_surface",
    20: "vehicle_purpose",
    21: "road_object",
    22: "object_distance",
    23: "didnt_cross",
    24: "cross_mode",
    25: "cross_location",
    26: "cross_direction",
    28: "driving_directions",
    29: "vehicle_damage",
    31: "involved_type",
    33: "safety_measures_use",  # need to verify if exists in new format
    34: "safety_measures",
    35: "injury_severity",
    37: "day_type",
    38: "day_night",
    39: "day_in_week",
    40: "traffic_light",
    42: "engine_volume",
    43: "vehicle_attribution",
    44: "total_weight",
    45: "vehicle_type",
    46: "late_deceased",
    47: "location_accuracy",
    48: "vehicle_type",
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
}


def read_dictionary(dictionary_file):
    from anyway.parsers.cbs.executor import read_cbs_file

    cbs_dictionary = defaultdict(dict)
    dictionary = read_cbs_file(dictionary_file)
# added by python upgrade
#    dictionary = pd.read_csv(dictionary_file, encoding="cp1255")
#    dictionary.columns = [column.strip().lower() for column in dictionary.columns]
    for _, dic in dictionary.iterrows():
        cbs_dictionary[int(dic[DICTCOLUMN1])][int(dic[DICTCOLUMN2])] = dic[DICTCOLUMN3]
    return cbs_dictionary


def fill_dictionary_tables(cbs_dictionary, provider_code, year):
    if year < 2008:
        return
    for k, v in cbs_dictionary.items():
        if k == 27:
            continue
        try:
            curr_table = TABLES_DICT[k]
        except Exception as _:
            logging.debug(
                "A key " + str(k) + " was added to dictionary - update models, tables and classes"
            )
            continue
        for inner_k, inner_v in v.items():
            curr_table = TABLES_DICT[k]
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


def update_dictionary_tables(path):
    import_ui = ImporterUI(path)
    dir_name = import_ui.source_path()
    dir_list = glob.glob("{0}/*/*".format(dir_name))

    for directory in sorted(dir_list, reverse=True):
        print(directory)
        directory_name = os.path.basename(os.path.normpath(directory))
        year = directory_name[1:5] if directory_name[0] == "H" else directory_name[0:4]
        if int(year) < 2008:
            continue
        parent_directory = os.path.basename(os.path.dirname(os.path.join(os.pardir, directory)))
        provider_code = get_provider_code(parent_directory)
        logging.debug("Importing Directory " + directory)
        dictionary_file = _get_dictionary_file(directory)
        if not dictionary_file:
            return 0
        logging.debug("Filling dictionary for directory '{}'".format(directory))
        fill_dictionary_tables(read_dictionary(dictionary_file), provider_code, int(year))


def _get_dictionary_file(directory):
    files = [
        path
        for path in os.listdir(directory)
        if DICTIONARY_FILENAME.lower() in path.lower() and not path.startswith(".")
    ]
    if not files:
        raise ValueError("Not found: '%s'" % DICTIONARY_FILENAME)
    if len(files) > 1:
        raise ValueError("Ambiguous: '%s'" % DICTIONARY_FILENAME)
    return os.path.join(directory, files[0])
