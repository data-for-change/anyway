# pylint: disable=no-member
import logging
import os
import shutil
from datetime import datetime

import math
import pandas as pd
from sqlalchemy import or_, not_, and_

from anyway.backend_constants import BE_CONST
from anyway.models import (
    AccidentMarker,
    Involved,
    SchoolWithDescription,
    InjuredAroundSchool,
    InjuredAroundSchoolAllData,
)
from anyway.utilities import time_delta, chunks
from anyway.app_and_db import db

SUBTYPE_ACCIDENT_WITH_PEDESTRIAN = 1
LOCATION_ACCURACY_PRECISE = True
LOCATION_ACCURACY_PRECISE_INT = 1
INJURED_TYPE_PEDESTRIAN = 1
YISHUV_SYMBOL_NOT_EXIST = -1
CONTENT_ENCODING = "utf-8"
HEBREW_ENCODING = "cp1255"
ANYWAY_UI_FORMAT_MAP_ONLY = "https://www.anyway.co.il/?zoom=17&start_date={start_date}&end_date={end_date}&lat={latitude}&lon={longitude}&show_fatal=1&show_severe=1&show_light=1&approx={location_approx}&accurate={location_accurate}&show_markers=1&show_discussions=0&show_urban=3&show_intersection=3&show_lane=3&show_day=7&show_holiday=0&show_time=24&start_time=25&end_time=25&weather=0&road=0&separation=0&surface=0&acctype={acc_type}&controlmeasure=0&district=0&case_type=0&show_rsa=0&age_groups=1234&map_only=true"
ANYWAY_UI_FORMAT_WITH_FILTERS = "https://www.anyway.co.il/?zoom=17&start_date={start_date}&end_date={end_date}&lat={latitude}&lon={longitude}&show_fatal=1&show_severe=1&show_light=1&approx={location_approx}&accurate={location_accurate}&show_markers=1&show_discussions=0&show_urban=3&show_intersection=3&show_lane=3&show_day=7&show_holiday=0&show_time=24&start_time=25&end_time=25&weather=0&road=0&separation=0&surface=0&acctype={acc_type}&controlmeasure=0&district=0&case_type=0&show_rsa=0&age_groups=1234"
DATE_INPUT_FORMAT = "%d-%m-%Y"
DATE_URL_FORMAT = "%Y-%m-%d"


def get_bounding_box(latitude, longitude, distance_in_km):
    latitude = math.radians(latitude)
    longitude = math.radians(longitude)

    radius = 6371
    # Radius of the parallel at given latitude
    parallel_radius = radius * math.cos(latitude)

    lat_min = latitude - distance_in_km / radius
    lat_max = latitude + distance_in_km / radius
    lon_min = longitude - distance_in_km / parallel_radius
    lon_max = longitude + distance_in_km / parallel_radius
    rad2deg = math.degrees

    return rad2deg(lat_min), rad2deg(lon_min), rad2deg(lat_max), rad2deg(lon_max)


def acc_inv_query(longitude, latitude, distance, start_date, end_date, school):
    lat_min, lon_min, lat_max, lon_max = get_bounding_box(latitude, longitude, distance)
    base_x = lon_min
    base_y = lat_min
    distance_x = lon_max
    distance_y = lat_max
    pol_str = "POLYGON(({0} {1},{0} {3},{2} {3},{2} {1},{0} {1}))".format(
        base_x, base_y, distance_x, distance_y
    )

    query_obj = (
        db.session.query(InvolvedMarkerView)
        .filter(InvolvedMarkerView.geom.intersects(pol_str))
        .filter(
            or_(
                (InvolvedMarkerView.provider_code == BE_CONST.CBS_ACCIDENT_TYPE_1_CODE),
                (InvolvedMarkerView.provider_code == BE_CONST.CBS_ACCIDENT_TYPE_3_CODE),
            )
        )
        .filter(InvolvedMarkerView.accident_timestamp >= start_date)
        .filter(InvolvedMarkerView.accident_timestamp <= end_date)
        .filter(InvolvedMarkerView.location_accuracy.in_(LOCATION_ACCURACY_PRECISE_LIST))
        .filter(InvolvedMarkerView.age_group.in_(AGE_GROUPS))
        .filter(InvolvedMarkerView.injury_severity.in_(INJURY_SEVERITIES))
        .filter(
            or_(
                (InvolvedMarkerView.injured_type.in_(INJURED_TYPES)),
                (InvolvedMarkerView.involve_vehicle_type.in_(VEHICLE_TYPES)),
            )
        )
        .filter(InvolvedMarkerView.accident_hour_raw.between(SEVEN_AM_RAW, SEVEN_PM_RAW))
    )

    df = pd.read_sql_query(query_obj.with_labels().statement, query_obj.session.bind)
    if LOCATION_ACCURACY_PRECISE:
        location_accurate = 1
        location_approx = ""
    else:
        location_accurate = 1
        location_approx = 1
    ui_url_map_only = ANYWAY_UI_FORMAT_MAP_ONLY.format(
        latitude=latitude,
        longitude=longitude,
        start_date=start_date.strftime(DATE_URL_FORMAT),
        end_date=end_date.strftime(DATE_URL_FORMAT),
        acc_type=SUBTYPE_ACCIDENT_WITH_PEDESTRIAN,
        location_accurate=location_accurate,
        location_approx=location_approx,
    )

    ui_url_with_filters = ANYWAY_UI_FORMAT_WITH_FILTERS.format(
        latitude=latitude,
        longitude=longitude,
        start_date=start_date.strftime(DATE_URL_FORMAT),
        end_date=end_date.strftime(DATE_URL_FORMAT),
        acc_type=SUBTYPE_ACCIDENT_WITH_PEDESTRIAN,
        location_accurate=location_accurate,
        location_approx=location_approx,
    )

    df["school_anyway_link"] = ui_url_map_only
    df["anyway_link_with_filters"] = ui_url_with_filters
    df["school_id"] = school.school_id
    df["school_type"] = school.school_type
    df["school_name"] = school.school_name
    df["school_yishuv_name"] = school.yishuv_name
    df["school_longitude"] = school.longitude
    df["school_latitude"] = school.latitude
    df["accident_year"] = df["involved_accident_year"]
    return df


def select_columns_df_total(df):
    return df.loc[
        :,
        [
            "school_id",
            "markers_provider_and_id",
            "markers_provider_code",
            "markers_description",
            "markers_accident_type",
            "markers_accident_severity",
            "markers_address",
            "markers_location_accuracy",
            "markers_road_type",
            "markers_road_shape",
            "markers_day_type",
            "markers_police_unit",
            "markers_mainStreet",
            "markers_secondaryStreet",
            "markers_junction",
            "markers_one_lane",
            "markers_multi_lane",
            "markers_speed_limit",
            "markers_road_intactness",
            "markers_road_width",
            "markers_road_sign",
            "markers_road_light",
            "markers_road_control",
            "markers_weather",
            "markers_road_surface",
            "markers_road_object",
            "markers_object_distance",
            "markers_didnt_cross",
            "markers_cross_mode",
            "markers_cross_location",
            "markers_cross_direction",
            "markers_video_link",
            "markers_road1",
            "markers_road2",
            "markers_km",
            "markers_yishuv_symbol",
            "markers_yishuv_name",
            "markers_geo_area",
            "markers_day_night",
            "markers_day_in_week",
            "markers_traffic_light",
            "markers_region",
            "markers_district",
            "markers_natural_area",
            "markers_municipal_status",
            "markers_yishuv_shape",
            "markers_street1",
            "markers_street1_hebrew",
            "markers_street2",
            "markers_street2_hebrew",
            "markers_house_number",
            "markers_urban_intersection",
            "markers_non_urban_intersection",
            "markers_non_urban_intersection_hebrew",
            "markers_accident_year",
            "markers_accident_month",
            "markers_accident_day",
            "markers_accident_hour_raw",
            "markers_accident_hour",
            "markers_accident_minute",
            "markers_x",
            "markers_y",
            "markers_vehicle_type_rsa",
            "markers_violation_type_rsa",
            "markers_geom",
            "involved_provider_and_id",
            "involved_provider_code",
            "involved_accident_id",
            "involved_involved_type",
            "involved_license_acquiring_date",
            "involved_age_group",
            "involved_sex",
            "involved_vehicle_type",
            "involved_safety_measures",
            "involved_involve_yishuv_symbol",
            "involved_involve_yishuv_name",
            "involved_injury_severity",
            "involved_injured_type",
            "involved_injured_position",
            "involved_population_type",
            "involved_home_region",
            "involved_home_district",
            "involved_home_natural_area",
            "involved_home_municipal_status",
            "involved_home_yishuv_shape",
            "involved_hospital_time",
            "involved_medical_type",
            "involved_release_dest",
            "involved_safety_measures_use",
            "involved_late_deceased",
            "involved_car_id",
            "involved_involve_id",
            "involved_accident_year",
            "involved_accident_month",
            "involved_injury_severity_mais",
        ],
    ]


def get_injured_around_schools(start_date, end_date, distance):
    schools = (
        db.session.query(SchoolWithDescription)
        .filter(
            not_(and_(SchoolWithDescription.latitude == 0, SchoolWithDescription.longitude == 0)),
            not_(
                and_(
                    SchoolWithDescription.latitude == None, SchoolWithDescription.longitude == None
                )
            ),
            or_(
                SchoolWithDescription.school_type == "גן ילדים",
                SchoolWithDescription.school_type == "בית ספר",
            ),
        )
        .all()
    )
    data_dir = "tmp_school_data"
    if os.path.exists(data_dir):
        shutil.rmtree(data_dir)
    os.mkdir(data_dir)
    for idx, school in enumerate(schools):
        if idx % 100 == 0:
            logging.info(idx)
        df_curr = acc_inv_query(
            longitude=school.longitude,
            latitude=school.latitude,
            distance=distance,
            start_date=start_date,
            end_date=end_date,
            school=school,
        )
        curr_csv_path = os.path.join(data_dir, str(school.school_id))
        df_curr.to_pickle(curr_csv_path)
    df_total = pd.DataFrame()
    for idx, filename in enumerate(os.listdir(data_dir)):
        curr_csv_path = os.path.join(data_dir, filename)
        df_total = pd.concat([df_total, pd.read_pickle(curr_csv_path)], axis=0)
        if idx % 100 == 0:
            logging.info(idx)
    shutil.rmtree(data_dir)

    # df_total_injured
    logging.info("create df_total_injured")
    df_total_injured = (
        df_total.groupby(
            [
                "school_yishuv_name",
                "school_id",
                "school_name",
                "school_type",
                "school_anyway_link",
                "school_longitude",
                "school_latitude",
                "accident_year",
                "involved_injury_severity",
            ]
        )
        .size()
        .reset_index(name="injured_count")
        .loc[
            :,
            [
                "school_yishuv_name",
                "school_id",
                "school_name",
                "school_type",
                "school_anyway_link",
                "involved_injury_severity",
                "injured_count",
                "school_longitude",
                "school_latitude",
                "accident_year",
            ],
        ]
    )
    df_total_injured = df_total_injured.set_index(
        [
            "school_yishuv_name",
            "school_id",
            "school_name",
            "school_type",
            "school_anyway_link",
            "school_longitude",
            "school_latitude",
            "accident_year",
            "involved_injury_severity",
        ]
    ).unstack(-1)
    df_total_injured.fillna({"injured_count": 0, "total_injured_count": 0}, inplace=True)
    df_total_injured.loc[:, (slice("injured_count"), slice(None))] = df_total_injured.loc[
        :, (slice("injured_count"), slice(None))
    ].apply(lambda x: x.apply(int))
    df_total_injured["total_injured_count"] = (
        df_total_injured.loc[:, ["injured_count"]].sum(axis=1)
    ).apply(int)

    # get rank by yishuv
    logging.info("create df_rank_by_yishuv")
    df_rank_by_yishuv = (
        df_total_injured.stack()
        .groupby(
            [
                "school_yishuv_name",
                "school_id",
                "school_name",
                "school_type",
                "school_anyway_link",
                "school_longitude",
                "school_latitude",
            ]
        )
        .sum()
        .reset_index()
    )
    df_rank_by_yishuv["total_injured_count"] = df_rank_by_yishuv["total_injured_count"].astype(int)

    groups = df_rank_by_yishuv.loc[
        :,
        [
            "school_yishuv_name",
            "school_id",
            "school_name",
            "school_type",
            "school_longitude",
            "school_latitude",
            "total_injured_count",
        ],
    ].groupby(["school_yishuv_name"])

    df_rank_by_yishuv["rank_in_yishuv"] = (
        groups["total_injured_count"].rank(method="dense", ascending=False).astype(int)
    )
    df_rank_by_yishuv = df_rank_by_yishuv.loc[
        :,
        [
            "school_yishuv_name",
            "school_id",
            "school_name",
            "school_type",
            "school_longitude",
            "school_latitude",
            "rank_in_yishuv",
        ],
    ]

    # join df_total_injured and df_rank_by_yishuv with rank by yishuv
    logging.info("join df_total_injured and df_rank_by_yishuv")

    joined_df = pd.merge(
        df_total_injured.reset_index(),
        df_rank_by_yishuv,
        on=[
            "school_yishuv_name",
            "school_id",
            "school_name",
            "school_type",
            "school_longitude",
            "school_latitude",
        ],
        how="left",
    )
    joined_df.sort_values(["school_yishuv_name", "rank_in_yishuv"], ascending=True, inplace=True)

    joined_df.columns = [
        col if type(col) == str else "_".join(map(str, col)) for col in joined_df.columns.values
    ]
    joined_df = joined_df.loc[
        :,
        [
            "school_yishuv_name",
            "school_id",
            "school_name",
            "school_type",
            "school_anyway_link_",
            "rank_in_yishuv",
            "school_longitude",
            "school_latitude",
            "accident_year_",
            "injured_count_1",
            "injured_count_2",
            "injured_count_3",
            "total_injured_count_",
        ],
    ]
    joined_df.columns = [
        "school_yishuv_name",
        "school_id",
        "school_name",
        "school_type",
        "school_anyway_link",
        "rank_in_yishuv",
        "school_longitude",
        "school_latitude",
        "accident_year",
        "killed_count",
        "severly_injured_count",
        "light_injured_count",
        "total_injured_killed_count",
    ]
    joined_df["distance_in_km"] = distance
    joined_df = joined_df.to_dict(orient="records")

    logging.info("select_columns_df_total")
    df_total = select_columns_df_total(df_total)
    df_total = df_total.to_dict(orient="records")
    logging.info("return joined_df, df_total")
    return joined_df, df_total


def truncate_injured_around_schools():
    curr_table = "injured_around_school"
    sql_truncate = "TRUNCATE TABLE " + curr_table
    db.session.execute(sql_truncate)
    db.session.commit()
    logging.info("Truncated table " + curr_table)

    curr_table = "injured_around_school_all_data"
    sql_truncate = "TRUNCATE TABLE " + curr_table
    db.session.execute(sql_truncate)
    db.session.commit()
    logging.info("Truncated table " + curr_table)


def import_to_datastore(start_date, end_date, distance, batch_size):
    try:
        assert batch_size > 0
        started = datetime.now()
        injured_around_schools, df_total = get_injured_around_schools(
            start_date, end_date, distance
        )
        truncate_injured_around_schools()
        new_items = 0
        logging.info(
            f"inserting {len(injured_around_schools)} new rows about to injured_around_school"
        )
        for chunk_idx, schools_chunk in enumerate(chunks(injured_around_schools, batch_size)):
            if chunk_idx % 10 == 0:
                logging_chunk = f"Chunk idx in injured_around_schools: {chunk_idx}"
                logging.info(logging_chunk)
            db.session.bulk_insert_mappings(InjuredAroundSchool, schools_chunk)
            db.session.commit()
        logging.info(f"inserting {len(df_total)} new rows injured_around_school_all_data")
        for chunk_idx, schools_chunk in enumerate(chunks(df_total, batch_size)):
            if chunk_idx % 10 == 0:
                logging_chunk = f"Chunk idx in injured_around_school_all_data: {chunk_idx}"
                logging.info(logging_chunk)
            db.session.bulk_insert_mappings(InjuredAroundSchoolAllData, schools_chunk)
            db.session.commit()
        new_items += len(injured_around_schools) + len(df_total)
        logging.info(f"\t{new_items} items in {time_delta(started)}")
        return new_items
    except Exception as exception:
        logging.info(f"\tExecution took {time_delta(started)}")
        error = (
            f"Schools import succeeded partially with {new_items} schools. Got error : {exception}"
        )
        raise Exception(error)


def parse(start_date, end_date, distance, batch_size):
    started = datetime.now()
    total = import_to_datastore(
        start_date=start_date, end_date=end_date, distance=distance, batch_size=batch_size
    )
    logging.info("Total: {0} rows in {1}".format(total, time_delta(started)))
