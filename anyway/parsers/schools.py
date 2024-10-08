import logging
from datetime import datetime

import pandas as pd

from static.data.schools import school_fields
from anyway.models import School
from anyway.utilities import time_delta, chunks
from anyway.app_and_db import db


def get_data_value(value):
    """
    :returns: value for parameters which are not mandatory in an accident data
    OR -1 if the parameter value does not exist
    """
    return int(value) if value else -1


def get_schools(filepath):
    logging.info("\tReading schools data from '%s'..." % filepath)
    schools = []
    df = pd.read_csv(filepath)
    for _, school in df.iterrows():
        longitude, latitude = (
            float(school[school_fields.longitude]),
            float(school[school_fields.latitude]),
        )
        point_str = "SRID=4326;POINT({0} {1})".format(longitude, latitude)
        school = {
            "id": int(school[school_fields.id]),
            "fcode_type": int(school[school_fields.fcode_type]),
            "yishuv_symbol": int(school[school_fields.yishuv_symbol]),
            "yishuv_name": school[school_fields.yishuv_name],
            "school_name": school[school_fields.school_name],
            "school_latin_name ": school[school_fields.school_latin_name],
            "usg": int(school[school_fields.usg]),
            "usg_code": int(school[school_fields.usg_code]),
            "e_ord": float(school[school_fields.e_ord]),
            "n_ord": float(school[school_fields.n_ord]),
            "longitude": longitude,
            "latitude": latitude,
            "geom": point_str,
            "data_year": get_data_value(school[school_fields.data_year]),
            "prdct_ver": None,
            "x": float(school[school_fields.x]),
            "y": float(school[school_fields.y]),
        }
        schools.append(school)

    return schools


def import_to_datastore(filepath, batch_size):
    try:
        assert batch_size > 0
        started = datetime.now()
        schools = get_schools(filepath)
        new_items = 0
        all_existing_schools_ids = set(map(lambda x: x[0], db.session.query(School.id).all()))
        schools = [school for school in schools if school["id"] not in all_existing_schools_ids]
        logging.info(f"inserting {len(schools)} new schools")
        for schools_chunk in chunks(schools, batch_size):
            db.session.bulk_insert_mappings(School, schools_chunk)
            db.session.commit()
        new_items += len(schools)
        logging.info(f"\t{new_items} items in {time_delta(started)}")
        return new_items
    except Exception as exception:
        error = f"Schools import succeeded partially with {new_items} schools. Got exception : {exception}"
        raise Exception(error)


def parse(filepath, batch_size):
    started = datetime.now()
    total = import_to_datastore(filepath, batch_size)
    logging.info("Total: {0} schools in {1}".format(total, time_delta(started)))
