import sqlalchemy as sa
from sqlalchemy import or_
from flask_sqlalchemy import SQLAlchemy
import math
from anyway.utilities import init_flask
from anyway.models import AccidentMarker, Involved, School
from anyway.constants import CONST
import pandas as pd
import os


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
        .filter(or_((AccidentMarker.provider_code == CONST.CBS_ACCIDENT_TYPE_1_CODE), (AccidentMarker.provider_code == CONST.CBS_ACCIDENT_TYPE_3_CODE))) \
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
    ui_url_map_only = ANYWAY_UI_FORMAT_MAP_ONLY.format(latitude=school['latitude'],
                                     longitude=school['longitude'],
                                     start_date=start_date.strftime(DATE_URL_FORMAT),
                                     end_date=end_date.strftime(DATE_URL_FORMAT),
                                     acc_type=SUBTYPE_ACCIDENT_WITH_PEDESTRIAN,
                                     location_accurate=location_accurate,
                                     location_approx=location_approx)

    ui_url_with_filters = ANYWAY_UI_FORMAT_WITH_FILTERS.format(latitude=school['latitude'],
                                     longitude=school['longitude'],
                                     start_date=start_date.strftime(DATE_URL_FORMAT),
                                     end_date=end_date.strftime(DATE_URL_FORMAT),
                                     acc_type=SUBTYPE_ACCIDENT_WITH_PEDESTRIAN,
                                     location_accurate=location_accurate,
                                     location_approx=location_approx)

    df['anyway_link'] = ui_url_map_only
    df['anyway_link_with_filters'] = ui_url_with_filters
    df['school_id'] = school['id']
    df['school_name'] = school['school_name']
    df['school_yishuv_symbol'] = school['yishuv_symbol']
    df['school_yishuv_name'] = school['yishuv_name']
    df['school_longitude'] = school['longitude']
    df['school_latitude'] = school['latitude']

    return df


def main(start_date, end_date, distance, output_path):
    schools_query = sa.select([School])
    df_schools = pd.read_sql_query(schools_query, db.session.bind)
    df_total = pd.DataFrame()
    df_schools = df_schools.drop_duplicates(['yishuv_name', 'longitude', 'latitude']) # pylint: disable=no-member
    df_schools.dropna(subset=['yishuv_name'] ,inplace=True)
    df_schools = df_schools[df_schools.yishuv_symbol != 0]
    df_schools.to_csv(os.path.join(output_path,'df_schools.csv'), encoding=CONTENT_ENCODING)

    for _, school in df_schools.iterrows():
        df_total = pd.concat([df_total,
                             acc_inv_query(longitude=school['longitude'],
                                           latitude=school['latitude'],
                                           distance=distance,
                                           start_date=start_date,
                                           end_date=end_date,
                                           school=school)],
                             axis=0)


    df_total.to_csv(os.path.join(output_path,'df_total.csv'), encoding=CONTENT_ENCODING)

    df_total_involved_count = (df_total.groupby(['school_name', 'school_longitude', 'school_latitude', 'school_yishuv_symbol', 'school_yishuv_name', 'anyway_link', 'school_id', ])
                                       .size()
                                       .reset_index(name='injured_count')
                                       .sort_values('injured_count', ascending=False))
    df_total_involved_count.reset_index().to_csv(os.path.join(output_path,'df_total_involved_count.csv'), encoding=CONTENT_ENCODING, header=True)

    df_total_involved_by_injury = (df_total.groupby(['school_id', 'school_name', 'school_longitude', 'school_latitude', 'school_yishuv_symbol', 'school_yishuv_name','involved_injury_severity', 'anyway_link', ])
                                           .size()
                                           .reset_index(name='injured_count')
                                           .sort_values('injured_count', ascending=False))
    df_total_involved_by_injury.reset_index().to_csv(os.path.join(output_path,'df_total_involved_by_injury.csv'), encoding=CONTENT_ENCODING, header=True)

    df_total_involved_injiry_severity_1_2 = (df_total[(df_total.involved_injury_severity == 1)|(df_total.involved_injury_severity == 2)].groupby(['school_id', 'school_name', 'anyway_link', 'school_longitude', 'school_latitude', 'school_yishuv_symbol', 'school_yishuv_name'])
                                           .size()
                                           .reset_index(name='injured_count')
                                           .sort_values('injured_count', ascending=False))
    df_total_involved_injiry_severity_1_2.reset_index().to_csv(os.path.join(output_path,'df_total_involved_injiry_severity_1_2.csv'), encoding=CONTENT_ENCODING, header=True)

    df_total_accident_count = (df_total.drop_duplicates(['school_id', 'school_name', 'anyway_link', 'school_longitude', 'school_latitude', 'school_yishuv_symbol', 'school_yishuv_name','provider_and_id'])
                                        .groupby(['school_id', 'school_name', 'school_yishuv_symbol', 'school_yishuv_name'])
                                        .size()
                                        .reset_index(name='accidents_count')
                                        .sort_values('accidents_count', ascending=False))
    df_total_accident_count.reset_index().to_csv(os.path.join(output_path,'df_total_accident_count.csv'), encoding=CONTENT_ENCODING, header=True)

    df_total_involved_count_by_yishuv = (df_total.groupby(['school_yishuv_name', 'school_id', 'school_name', 'anyway_link_with_filters', 'school_longitude', 'school_latitude', 'involved_injury_severity'])
                                       .size()
                                       .reset_index(name='injured_count')
                                       .loc[:,['school_yishuv_name', 'school_name', 'anyway_link_with_filters', 'involved_injury_severity', 'injured_count', 'school_longitude', 'school_latitude', 'school_id']])
    df_total_involved_count_by_yishuv = df_total_involved_count_by_yishuv.set_index(['school_yishuv_name', 'school_name', 'anyway_link_with_filters','school_longitude', 'school_latitude', 'school_id', 'involved_injury_severity']).unstack(-1)

    df_total_involved_count_by_yishuv.fillna({'injured_count': 0, 'total_injured_count': 0}, inplace=True)
    df_total_involved_count_by_yishuv.loc[:,(slice('injured_count'), slice(None))] = df_total_involved_count_by_yishuv.loc[:,(slice('injured_count'), slice(None))].apply(lambda x: x.apply(int))
    df_total_involved_count_by_yishuv['total_injured_count'] = (df_total_involved_count_by_yishuv.loc[:,['injured_count']].sum(axis=1)).apply(int)

    groups = df_total_involved_count_by_yishuv.loc[:,['school_yishuv_name', 'school_name', 'school_longitude', 'school_latitude' , 'school_id', 'total_injured_count']].groupby(['school_yishuv_name'])
    rank_in_yishuv = groups['total_injured_count'].rank(method='dense', ascending=False)
    rank_in_yishuv.name = 'rank'
    rank_in_yishuv = rank_in_yishuv.apply(int)
    rank_in_yishuv = rank_in_yishuv.to_frame(name='rank_in_yishuv').reset_index()

    joined_df = pd.merge(df_total_involved_count_by_yishuv.reset_index(), rank_in_yishuv, on=['school_yishuv_name', 'school_name', 'school_longitude', 'school_latitude' ], how='left')
    joined_df.sort_values(['school_yishuv_name', 'rank_in_yishuv'], ascending=True, inplace=True)
    joined_df.columns = [col if type(col)==str else '_'.join(map(str, col)) for col in joined_df.columns.values]
    joined_df = joined_df.loc[:,['school_yishuv_name', 'school_name', 'rank_in_yishuv', 'school_longitude', 'school_latitude', 'injured_count_1', 'injured_count_2', 'injured_count_3', 'total_injured_count_', 'anyway_link_with_filters', 'school_id']]
    joined_df.columns = ['school_yishuv_name', 'school_name', 'rank_in_yishuv', 'school_longitude', 'school_latitude', 'killed_count', 'severly_injured_count', 'light_injured_count', 'total_injured_killed_count', 'anyway_link', 'school_id']
    joined_df.to_csv(os.path.join(output_path,'df_total_involved_count_by_yishuv.csv'), encoding=CONTENT_ENCODING, header=True)