import io
import logging
from datetime import datetime
import math
import json
import os
import numpy as np
import pandas as pd
from io import BytesIO
from flask_sqlalchemy import SQLAlchemy
from ..models import SchoolWithDescription2020
from ..utilities import init_flask, time_delta, chunks, ItmToWGS84
from anyway.parsers.cbs.s3.base import S3DataClass

school_fields = {
    "school_id": "SEMEL_MOSAD",
    "school_name": "SHEM_MOSAD",
    "yishuv_name": "SHEM_YISHUV",
    "institution_type": "TEUR_TAT_SUG_MISGERET",
    "x": "X",
    "y": "Y",
}

S3_BUCKET = "dfc-anyway"
S3_SCHOOLS_FILE_PATH = "schools_report/schools/schools.xlsx"
S3_OUTPUT_DIR = 'schools_report/output'
INSTITUTION_TYPES = [
            "בית ספר",
            "תלמוד תורה",
            "ישיבה קטנה",
            'בי"ס תורני',
            "ישיבה תיכונית",
            'בי"ס חקלאי',
            'בי"ס רפואי',
            'בי"ס כנסייתי',
            "אולפנה",
            'בי"ס אקסטרני',
            'בי"ס קיבוצי',
            "תלמוד תורה ליד מעיין חינוך התורני",
            'בי"ס מושבי',
            'בי"ס - הילה חסות',
            'מחוננים',
        ]

app = init_flask()
db = SQLAlchemy(app)
coordinates_converter = ItmToWGS84()


def get_numeric_value(value, func):
    """
    :returns: value if parameter value exists OR None if the parameter value does not exist
    """
    return func(value) if value and not np.isnan(value) else None


def get_str_value(value):
    """
    :returns: value if parameter value exists OR None if the parameter value does not exist
    """
    return value if value and value not in ["nan", "Nan", "NaN", "NAN"] else None


def get_schools_with_description():
    institution_types_seen = set()
    logging.info("\tReading schools description data from S3")
    s3_data_object = S3DataClass(s3_bucket_name=S3_BUCKET)
    file_stream = BytesIO(s3_data_object.s3_bucket.Object(S3_SCHOOLS_FILE_PATH).get()['Body'].read())
    df_schools = pd.read_excel(file_stream, engine="openpyxl")
    logging.info("\tDone reading schools description data from S3")
    schools = []
    df_schools = df_schools.drop_duplicates(school_fields["school_id"])
    df_schools = df_schools.sort_values(school_fields["school_id"], ascending=True)
    all_schools_tuples = []
    for _, school in df_schools.iterrows():
        school_id = get_numeric_value(school[school_fields["school_id"]], int)
        if not school_id:
            continue
        try:
            school_name = get_str_value(school[school_fields["school_name"]]).strip('"')
        except AttributeError:
            continue
        x_coord = get_numeric_value(school[school_fields["x"]], float)
        y_coord = get_numeric_value(school[school_fields["y"]], float)
        if x_coord and not math.isnan(x_coord) and y_coord and not math.isnan(y_coord):
            longitude, latitude = coordinates_converter.convert(x_coord, y_coord)
        else:
            longitude, latitude = (
                None,
                None,
            )
        school_tuple = (school_name, x_coord, y_coord)
        if school_tuple in all_schools_tuples:
            continue
        else:
            all_schools_tuples.append(school_tuple)
        school = {
            "school_id": get_numeric_value(school[school_fields["school_id"]], int),
            "school_name": school_name,
            "municipality_name": None,
            "yishuv_name": get_str_value(school.get(school_fields["yishuv_name"])),
            "institution_type": get_str_value(school[school_fields["institution_type"]]),
            "lowest_grade": None,
            "highest_grade": None,
            "location_accuracy": None,
            "longitude": longitude,
            "latitude": latitude,
            "x": x_coord,
            "y": y_coord,
        }
        if school["institution_type"] in INSTITUTION_TYPES:
            schools.append(school)
            institution_types_seen.add(school["institution_type"])
    logging.info(f"Found {len(schools)} schools with description")
    logging.info(f"All institution types seen: {institution_types_seen}")
    logging.info(f"Expected institution types: {INSTITUTION_TYPES}")
    logging.info(f"All institution types seen match expected: {len(institution_types_seen) == len(INSTITUTION_TYPES)}")
    return schools


def truncate_schools_with_description():
    curr_table = "schools_with_description2020"
    sql_truncate = "TRUNCATE TABLE " + curr_table
    db.session.execute(sql_truncate)
    db.session.commit()
    logging.info("Truncated table " + curr_table)


def import_to_datastore(batch_size):
    try:
        assert batch_size > 0
        started = datetime.now()
        schools = get_schools_with_description()
        truncate_schools_with_description()
        new_items = 0
        logging.info("inserting " + str(len(schools)) + " new schools")
        for schools_chunk in chunks(schools, batch_size):
            db.session.bulk_insert_mappings(SchoolWithDescription2020, schools_chunk)
            db.session.commit()
        new_items += len(schools)
        logging.info(f"\t{new_items} items in {time_delta(started)}")
        return new_items
    except Exception as exception:
        error = f"Schools import succeeded partially with {new_items} schools. Got exception : {exception}"
        raise Exception(error)


def export_schools_to_json():
    schools = db.session.query(SchoolWithDescription2020).all()
    school_list = []
    for school in schools:
        if school.longitude is not None and school.latitude is not None:
            school_dict = {
                "school_id": school.school_id,
                "school_name": school.school_name,
                "yishuv_name": school.yishuv_name,
                "longitude": school.longitude,
                "latitude": school.latitude,
            }
            school_list.append(school_dict)
    s3_bucket = S3DataClass(s3_bucket_name=S3_BUCKET).s3_bucket
    with io.BytesIO() as json_buffer:
        json_buffer.write(json.dumps(school_list, ensure_ascii=False, indent=2).encode('utf-8'))
        json_buffer.seek(0)
        s3_bucket.upload_fileobj(json_buffer, os.path.join(S3_OUTPUT_DIR,'schools_names.json'))


def parse(batch_size):
    started = datetime.now()
    total = import_to_datastore(
        batch_size=batch_size,
    )
    db.session.execute(
        "UPDATE schools_with_description2020 SET geom = ST_SetSRID(ST_MakePoint(longitude,latitude),4326)\
                           WHERE geom IS NULL;"
    )
    db.session.commit()
    export_schools_to_json()
    logging.info("Total: {0} schools in {1}".format(total, time_delta(started)))
