import sqlalchemy as sa
from sqlalchemy import or_, not_, and_
from flask_sqlalchemy import SQLAlchemy
import math
from ..utilities import init_flask, time_delta, chunks
from ..models import AccidentMarker, Involved, School, SchoolWithDescription, InjuredAroundSchool
from ..constants import CONST
import pandas as pd
import os
from datetime import datetime
import logging


SUBTYPE_ACCIDENT_WITH_PEDESTRIAN = 1
LOCATION_ACCURACY_PRECISE = True
LOCATION_ACCURACY_PRECISE_INT = 1
INJURED_TYPE_PEDESTRIAN = 1
YISHUV_SYMBOL_NOT_EXIST = -1
CONTENT_ENCODING = 'utf-8'
HEBREW_ENCODING = 'cp1255'
ANYWAY_UI_FORMAT_MAP_ONLY = "https://www.anyway.co.il/?zoom=17&start_date={start_date}&end_date={end_date}&lat={latitude}&lon={longitude}&show_fatal=1&show_severe=1&show_light=1&approx={location_approx}&accurate={location_accurate}&show_markers=1&show_discussions=0&show_urban=3&show_intersection=3&show_lane=3&show_day=7&show_holiday=0&show_time=24&start_time=25&end_time=25&weather=0&road=0&separation=0&surface=0&acctype={acc_type}&controlmeasure=0&district=0&case_type=0&show_rsa=0&age_groups=1,2,3,4&map_only=true"
ANYWAY_UI_FORMAT_WITH_FILTERS = "https://www.anyway.co.il/?zoom=17&start_date={start_date}&end_date={end_date}&lat={latitude}&lon={longitude}&show_fatal=1&show_severe=1&show_light=1&approx={location_approx}&accurate={location_accurate}&show_markers=1&show_discussions=0&show_urban=3&show_intersection=3&show_lane=3&show_day=7&show_holiday=0&show_time=24&start_time=25&end_time=25&weather=0&road=0&separation=0&surface=0&acctype={acc_type}&controlmeasure=0&district=0&case_type=0&show_rsa=0&age_groups=1,2,3,4"
DATE_INPUT_FORMAT = '%d-%m-%Y'
DATE_URL_FORMAT = '%Y-%m-%d'


app = init_flask()
db = SQLAlchemy(app)
injury_severity_dict = {1: 'קטלנית',
                        2: 'קשה',
                        3: 'קלה'}


def get_bounding_box(latitude, longitude, distance_in_km):

    latitude = math.radians(latitude)
    longitude = math.radians(longitude)

    radius = 6371
    # Radius of the parallel at given latitude
    parallel_radius = radius*math.cos(latitude)

    lat_min = latitude - distance_in_km/radius
    lat_max = latitude + distance_in_km/radius
    lon_min = longitude - distance_in_km/parallel_radius
    lon_max = longitude + distance_in_km/parallel_radius
    rad2deg = math.degrees

    return rad2deg(lat_min), rad2deg(lon_min), rad2deg(lat_max), rad2deg(lon_max)

def acc_inv_query(longitude, latitude, distance, start_date, end_date, school):
    lat_min, lon_min, lat_max, lon_max = get_bounding_box(latitude, longitude, distance)
    baseX = lon_min;
    baseY = lat_min;
    distanceX = lon_max;
    distanceY = lat_max;
    pol_str = 'POLYGON(({0} {1},{0} {3},{2} {3},{2} {1},{0} {1}))'.format(baseX,
                                                                          baseY,
                                                                          distanceX,
                                                                          distanceY)

    query_obj = db.session.query(Involved, AccidentMarker) \
        .join(AccidentMarker, AccidentMarker.provider_and_id == Involved.provider_and_id) \
        .filter(AccidentMarker.geom.intersects(pol_str)) \
        .filter(Involved.injured_type == INJURED_TYPE_PEDESTRIAN) \
        .filter(AccidentMarker.provider_and_id == Involved.provider_and_id) \
        .filter(or_((AccidentMarker.provider_code == CONST.CBS_ACCIDENT_TYPE_1_CODE),
                    (AccidentMarker.provider_code == CONST.CBS_ACCIDENT_TYPE_3_CODE))) \
        .filter(AccidentMarker.created >= start_date) \
        .filter(AccidentMarker.created < end_date) \
        .filter(AccidentMarker.location_accuracy == LOCATION_ACCURACY_PRECISE_INT) \
        .filter(AccidentMarker.yishuv_symbol != YISHUV_SYMBOL_NOT_EXIST) \
        .filter(Involved.age_group.in_([1,2,3,4])) #ages 0-19

    df = pd.read_sql_query(query_obj.with_labels().statement, query_obj.session.bind)
    if LOCATION_ACCURACY_PRECISE:
        location_accurate = 1
        location_approx = ''
    else:
        location_accurate = 1
        location_approx = 1
    ui_url_map_only = ANYWAY_UI_FORMAT_MAP_ONLY.format(latitude=latitude,
                                                       longitude=longitude,
                                                       start_date=start_date.strftime(DATE_URL_FORMAT),
                                                       end_date=end_date.strftime(DATE_URL_FORMAT),
                                                       acc_type=SUBTYPE_ACCIDENT_WITH_PEDESTRIAN,
                                                       location_accurate=location_accurate,
                                                       location_approx=location_approx)

    ui_url_with_filters = ANYWAY_UI_FORMAT_WITH_FILTERS.format(latitude=latitude,
                                                               longitude=longitude,
                                                               start_date=start_date.strftime(DATE_URL_FORMAT),
                                                               end_date=end_date.strftime(DATE_URL_FORMAT),
                                                               acc_type=SUBTYPE_ACCIDENT_WITH_PEDESTRIAN,
                                                               location_accurate=location_accurate,
                                                               location_approx=location_approx)

    df['school_anyway_link'] = ui_url_map_only
    df['anyway_link_with_filters'] = ui_url_with_filters
    df['school_id'] = school.school_id
    df['school_type'] = school.school_type
    df['school_name'] = school.school_name
    df['school_yishuv_name'] = school.yishuv_name
    df['school_longitude'] = school.longitude
    df['school_latitude'] = school.latitude
    df['accident_year'] = df['involved_accident_year']
    df['involved_injury_severity_hebrew'] = df['involved_injury_severity'].apply(lambda x: injury_severity_dict[x])
    return df


def get_injured_around_schools(start_date, end_date, distance):
    schools = db.session.query(SchoolWithDescription) \
                        .filter(not_(and_(SchoolWithDescription.latitude == 0, SchoolWithDescription.longitude == 0)), \
                                not_(and_(SchoolWithDescription.latitude == None, SchoolWithDescription.longitude == None)), \
                                or_(SchoolWithDescription.school_type == 'גן ילדים', SchoolWithDescription.school_type == 'בית ספר')).all()
    df_total = pd.DataFrame()
    for _, school in enumerate(schools):
        df_total = pd.concat([df_total,
                             acc_inv_query(longitude=school.longitude,
                                           latitude=school.latitude,
                                           distance=distance,
                                           start_date=start_date,
                                           end_date=end_date,
                                           school=school)],
                             axis=0)
    df_injured_per_school_year = (df_total.groupby(['school_id', 'school_name', 'school_type', 'school_longitude', 'school_latitude', 'school_yishuv_name', 'school_anyway_link', 'involved_injury_severity', 'involved_injury_severity_hebrew', 'accident_year'])
                                       .size()
                                       .reset_index(name='injured_count')
                                       .sort_values('injured_count', ascending=False))
    df_injured_per_school_year = df_injured_per_school_year.reset_index()
    df_injured_per_school_year['distance_in_km'] = distance
    injured_around_schools = df_injured_per_school_year.to_dict(orient='records')
    return injured_around_schools

def import_to_datastore(start_date,
                        end_date,
                        distance,
                        batch_size):
    try:
        assert batch_size > 0
        started = datetime.now()
        injured_around_schools = get_injured_around_schools(start_date, end_date, distance)
        new_items = 0
        all_existing_schools_symbol_ids = set(map(lambda x: x[0],
                                             db.session.query(InjuredAroundSchool.school_id).all()))
        schools = [school for school in injured_around_schools if school['school_id'] not in all_existing_schools_symbol_ids]
        logging.info('inserting ' + str(len(schools)) + ' new schools with injured around schools info')
        for schools_chunk in chunks(schools, batch_size):
            db.session.bulk_insert_mappings(InjuredAroundSchool, schools_chunk)
            db.session.commit()
        new_items += len(schools)
        logging.info("\t{0} items in {1}".format(new_items, time_delta(started)))
        return new_items
    except:
        error = "Schools import succeded partially with " + new_items + " schools"
        raise Exception(error)

def parse(start_date,
          end_date,
          distance,
          batch_size):
    started = datetime.now()
    total = import_to_datastore(start_date=start_date,
                                end_date=end_date,
                                distance=distance,
                                batch_size=batch_size)
    logging.info("Total: {0} schools in {1}".format(total, time_delta(started)))
