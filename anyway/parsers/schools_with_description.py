import logging
from datetime import datetime
from ..utilities import init_flask, time_delta, chunks, ItmToWGS84
from flask_sqlalchemy import SQLAlchemy
from ..models import SchoolWithDescription
import pandas as pd
import numpy as np
import math

school_fields = {
    'data_year': 'שנה',
    'symbol_id': 'סמל_מוסד',
    'school_name': 'שם_מוסד',
    'students_number': 'סהכ_תלמידים_במוסד',
    'municipality_name': 'שם_רשות',
    'yishuv_name': 'שם_ישוב',
    'sector': 'מגזר',
    'inspection': 'פיקוח',
    'legal_status': 'מעמד_משפטי',
    'reporter': 'גורם_מדווח',
    'geo_district': 'מחוז_גאוגרפי',
    'education_type': 'סוג_חינוך_מוסד',
    'school_type': 'סוג_מסגרת_אירגונית',
    'institution_type': 'סוג_מוסד',
    'lowest_grade': 'משכבה',
    'highest_grade': 'עד_שכבה',
    'foundation_year': 'שנת_יסוד',
    'location_accuracy': 'רמת_דיוק_מיקום',
    'x': 'X',
    'y': 'Y'
}

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
    return value if value and value not in ['nan', 'Nan', 'NaN', 'NAN'] else None

def get_schools_with_description(schools_description_filepath,
                                 schools_coordinates_filepath):

    logging.info("\tReading schools description data from '%s'..." % schools_description_filepath)
    df_schools = pd.read_excel(schools_description_filepath)
    logging.info("\tReading schools coordinates data from '%s'..." % schools_coordinates_filepath)
    df_coordinates = pd.read_excel(schools_coordinates_filepath)
    schools = []
    max_year = df_schools[school_fields['data_year']].astype(int).max()
    df_schools = df_schools[df_schools[school_fields['data_year']] == max_year]
    for _, school in df_schools.iterrows():
        symbol_id = get_numeric_value(school[school_fields['symbol_id']], int)
        if symbol_id in list(df_coordinates[school_fields['symbol_id']].values):
            x_coord = df_coordinates.loc[df_coordinates[school_fields['symbol_id']] == symbol_id, school_fields['x']].values[0]
            y_coord = df_coordinates.loc[df_coordinates[school_fields['symbol_id']] == symbol_id, school_fields['y']].values[0]
            location_accuracy = get_str_value(df_coordinates.loc[df_coordinates[school_fields['symbol_id']] == symbol_id,
                                                                school_fields['location_accuracy']].values[0])
        else:
            x_coord = None
            y_coord = None
            location_accuracy = None
        if x_coord and not math.isnan(x_coord) and y_coord and not math.isnan(y_coord):
            longitude, latitude = coordinates_converter.convert(x_coord, y_coord)
        else:
            longitude, latitude = None, None # otherwise yield will produce: UnboundLocalError: local variable referenced before assignment
        school = {
            'data_year': get_numeric_value(school[school_fields['data_year']], int),
            'symbol_id': get_numeric_value(school[school_fields['symbol_id']], int),
            'school_name': get_str_value(school[school_fields['school_name']]),
            'students_number': get_numeric_value(school[school_fields['students_number']], int),
            'municipality_name': get_str_value(school[school_fields['municipality_name']]),
            'yishuv_name': get_str_value(school[school_fields['yishuv_name']]),
            'sector': get_str_value(school[school_fields['sector']]),
            'inspection': get_str_value(school[school_fields['inspection']]),
            'legal_status': get_str_value(school[school_fields['legal_status']]),
            'reporter': get_str_value(school[school_fields['reporter']]),
            'geo_district': get_str_value(school[school_fields['geo_district']]),
            'education_type': get_str_value(school[school_fields['education_type']]),
            'school_type': get_str_value(school[school_fields['school_type']]),
            'institution_type': get_str_value(school[school_fields['institution_type']]),
            'lowest_grade': get_numeric_value(school[school_fields['lowest_grade']], int),
            'highest_grade': get_numeric_value(school[school_fields['highest_grade']], int),
            'foundation_year': get_numeric_value(school[school_fields['foundation_year']], int),
            'location_accuracy': location_accuracy,
            'longitude': longitude,
            'latitude': latitude,
            'x': x_coord,
            'y': y_coord,
        }
        schools.append(school)

    return schools

def import_to_datastore(schools_description_filepath,
                        schools_coordinates_filepath,
                        batch_size):
    try:
        assert batch_size > 0
        started = datetime.now()
        schools = get_schools_with_description(schools_description_filepath, schools_coordinates_filepath)
        new_items = 0
        all_existing_schools_symbol_ids = set(map(lambda x: x[0],
                                             db.session.query(SchoolWithDescription.symbol_id).all()))
        schools = [school for school in schools if school['symbol_id'] not in all_existing_schools_symbol_ids]
        logging.info('inserting ' + str(len(schools)) + ' new schools')
        for schools_chunk in chunks(schools, batch_size):
            db.session.bulk_insert_mappings(SchoolWithDescription, schools_chunk)
            db.session.commit()
        new_items += len(schools)
        logging.info("\t{0} items in {1}".format(new_items, time_delta(started)))
        return new_items
    except:
        error = "Schools import succeded partially with " + new_items + " schools"
        raise Exception(error)

def parse(schools_description_filepath,
          schools_coordinates_filepath,
          batch_size):
    started = datetime.now()
    total = import_to_datastore(schools_description_filepath=schools_description_filepath,
                                schools_coordinates_filepath=schools_coordinates_filepath,
                                batch_size=batch_size)
    db.session.execute('UPDATE schools_with_description SET geom = ST_SetSRID(ST_MakePoint(longitude,latitude),4326)\
                           WHERE geom IS NULL;')
    logging.info("Total: {0} schools in {1}".format(total, time_delta(started)))
