# -*- coding: utf-8 -*-
import sys
from typing import Dict, Tuple, Iterator, List
import logging
import pandas as pd
from anyway.app_and_db import db
from anyway.models import SuburbanJunction, RoadJunctionKM, JunctionArm, Junction


SUBURBAN_JUNCTION = "suburban_junction"
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
ID = "id"
JUNCTION_HEBREW = "junction_hebrew"
JUNCTION_ID = "junction_id"
IS_SUBURBAN = "is_suburban"
KM = "km"
ROAD1 = "road1"
ARM_SYMBOL = "arm_symbol"
ARM_NAME = "arm_name"
JUNCTION_SYMBOL = "junction_symbol"
ROAD_SYMBOL = "road_symbol"
YISHUV_SYMBOL = "yishuv_symbol"
STREET_SYMBOL = "street_symbol"
suburban_junctions_dict: Dict[int, dict] = {}
# (road, junction) -> km
road_junction_km_dict: Dict[Tuple[int, int], int] = {}
junction_arms: List[Dict] = []
junctions: Dict[int, Dict] = {}

def parse(junction_arms_filename, junctions_filename):
    read_junctions_from_file(junctions_filename)
    import_junctions_into_db()
    read_junction_arms_from_file(junction_arms_filename)
    import_junction_arms_into_db()
    import_suburban_junctions_into_db()
    import_road_junction_km_into_db()

def is_empty_value(value) -> bool:
    return pd.isna(value) or value == ""

def read_junctions_from_file(filename: str):
    expected_headers = ["kod", "teur"]
    df = pd.read_csv(filename, encoding="cp1255")
    assert list(df.columns[:len(expected_headers)]) == expected_headers, "File does not have expected headers"
    first_col = expected_headers[0]
    for row in df.itertuples(index=False):
        # In order to ignore empty lines
        if is_empty_value(getattr(row, first_col)):
            continue
        junction_symbol = row[0]
        junctions[junction_symbol] = {
            JUNCTION_SYMBOL: junction_symbol,
            JUNCTION_HEBREW: row[1],
        }
    logging.debug(f"Read {len(junctions)} junctions from file")

def import_junctions_into_db():
    logging.debug(f"Writing to db: {len(junctions)} junctions")
    db.session.query(Junction).delete()
    db.session.bulk_insert_mappings(Junction, list(junctions.values()))
    db.session.commit()
    logging.debug(f"Done writing Junction.")

def import_junction_arms_into_db():
    logging.debug(f"Writing to db: {len(junction_arms)} junction arms")
    db.session.query(JunctionArm).delete()
    db.session.bulk_insert_mappings(JunctionArm, junction_arms)
    db.session.commit()
    logging.debug(f"Done writing JunctionArm.")

def read_junction_arms_from_file(filename: str):
    for j in _iter_rows(filename):
        add_junction_arm(j)
        is_suburban = j[IS_SUBURBAN]
        if is_suburban == 1:
            add_suburban_junction(j)
            add_road_junction_km(j)

    
def _iter_rows(filename) -> Iterator[dict]:
    headers_to_fields = {
        "kod": ARM_SYMBOL,
        "teur": ARM_NAME,
        "SemelTsomet": JUNCTION_SYMBOL,
        "IsLoIrony": IS_SUBURBAN,
        "MisparKvish": ROAD_SYMBOL,
        "Kilometer": KM,
        "SemelYishuv": YISHUV_SYMBOL,
        "SemelRechov": STREET_SYMBOL,
    }
    expected_headers = list(headers_to_fields.keys())
    df = pd.read_csv(filename, encoding="cp1255", usecols=expected_headers)
    assert list(df.columns[:len(expected_headers)]) == expected_headers, "File does not have expected headers"

    first_col = expected_headers[0]
    rename_headers = lambda row: {headers_to_fields[col]: row[col] for col in expected_headers}
    row_nan_to_empty = lambda row: {k: (None if pd.isna(v) else v) for k, v in row_dict.items()}

    for row in df.itertuples(index=False):
        if is_empty_value(getattr(row, first_col)): #skip empty lines
            continue
        row_dict = row._asdict()  # namedtuple -> dict
        yield rename_headers(row_nan_to_empty(row_dict))

def add_road_junction_km(junction_arm: dict):
    road_junction_km_dict[(junction_arm[ROAD_SYMBOL], junction_arm[JUNCTION_SYMBOL])] = junction_arm[KM]


def import_suburban_junctions_into_db():
    items = [
        {
            "non_urban_intersection": k,
            NON_URBAN_INTERSECTION_HEBREW: fix_name_len(v[NON_URBAN_INTERSECTION_HEBREW]),
            ROADS: v[ROADS],
        }
        for k, v in suburban_junctions_dict.items()
    ]
    logging.debug(f"Writing to db: {len(items)} suburban junctions")
    db.session.query(SuburbanJunction).delete()
    db.session.bulk_insert_mappings(SuburbanJunction, items)
    db.session.commit()
    logging.debug(f"Done writing SuburbanJunction.")


def import_road_junction_km_into_db():
    items = [
        {"road": k[0], "non_urban_intersection": k[1], "km": v}
        for k, v in road_junction_km_dict.items()
    ]
    logging.debug(f"Writing to db: {len(items)} road junction km rows")
    db.session.query(RoadJunctionKM).delete()
    db.session.bulk_insert_mappings(RoadJunctionKM, items)
    db.session.commit()
    logging.debug(f"Done writing RoadJunctionKM.")


def fix_name_len(name: str) -> str:
    if not isinstance(name, str):
        return name
    if len(name) > SuburbanJunction.MAX_NAME_LEN:
        logging.error(
            f"Suburban_junction name too long ({len(name)}>"
            f"{SuburbanJunction.MAX_NAME_LEN}):{name}."
        )
    return name[: SuburbanJunction.MAX_NAME_LEN]

def add_junction_arm(junction_arm: dict):
    junction_arms.append(junction_arm)


def add_suburban_junction(junction_arm: dict):
    j_id = junction_arm[JUNCTION_SYMBOL]
    j_name = ""
    junction = junctions.get(j_id)
    if junction:
        j_name = junction.get(JUNCTION_HEBREW)
    else:
        logging.error(f"Junction {j_id} not found in junctions")
    road1 = junction_arm[ROAD_SYMBOL]
    if j_id in suburban_junctions_dict:
        existing_junction = suburban_junctions_dict[j_id]
        existing_junction[ROADS].add(road1)
    else:
        suburban_junctions_dict[j_id] = {
            NON_URBAN_INTERSECTION_HEBREW: j_name,
            ROADS: {road1},
        }


if __name__ == "__main__":
    junction_arms_filename, junctions_filename = sys.argv[1], sys.argv[2]
    parse(junction_arms_filename, junctions_filename)
