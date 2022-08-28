# pylint: disable=no-member
import logging
import os
import shutil
from datetime import datetime
from typing import NoReturn
from enum import Enum
import json
import pathlib
import swifter

import math
import pandas as pd
import numpy as np
from sqlalchemy import or_, not_, and_

from anyway.backend_constants import BE_CONST
from anyway.models import SchoolWithDescription2020, InvolvedMarkerView

from anyway.utilities import time_delta, chunks
from anyway.app_and_db import db


class SchoolsJsonFile(Enum):
    MAIN_FILE = ""


SUBTYPE_ACCIDENT_WITH_PEDESTRIAN = 1
LOCATION_ACCURACY_PRECISE = False
LOCATION_ACCURACY_PRECISE_LIST = [1, 3, 4]
AGE_GROUPS = [2, 3, 4]
INJURED_TYPE_PEDESTRIAN = 1
INJURED_TYPES = [1, 6, 7]
VEHICLE_TYPES = [15, 21, 23]
CONTENT_ENCODING = "utf-8"
HEBREW_ENCODING = "cp1255"
ANYWAY_UI_FORMAT_MAP_ONLY = "https://www.anyway.co.il/?zoom=17&start_date={start_date}&end_date={end_date}&lat={latitude}&lon={longitude}&show_fatal=1&show_severe=1&show_light=1&approx={location_approx}&accurate={location_accurate}&show_markers=1&show_discussions=0&show_urban=3&show_intersection=3&show_lane=3&show_day=7&show_holiday=0&show_time=24&start_time=25&end_time=25&weather=0&road=0&separation=0&surface=0&acctype={acc_type}&controlmeasure=0&district=0&case_type=0&show_rsa=0&age_groups=234&map_only=true"
ANYWAY_UI_FORMAT_WITH_FILTERS = "https://www.anyway.co.il/?zoom=17&start_date={start_date}&end_date={end_date}&lat={latitude}&lon={longitude}&show_fatal=1&show_severe=1&show_light=1&approx={location_approx}&accurate={location_accurate}&show_markers=1&show_discussions=0&show_urban=3&show_intersection=3&show_lane=3&show_day=7&show_holiday=0&show_time=24&start_time=25&end_time=25&weather=0&road=0&separation=0&surface=0&acctype={acc_type}&controlmeasure=0&district=0&case_type=0&show_rsa=0&age_groups=234"
DATE_INPUT_FORMAT = "%d-%m-%Y"
DATE_URL_FORMAT = "%Y-%m-%d"
SEVEN_AM_RAW = 29
SEVEN_PM_RAW = 76
INJURY_SEVERITIES = [1, 2, 3]

ALL_SCHOOLS_DATA_DIR = os.path.join(
    pathlib.Path(__file__).parent.parent.parent, "static", "data", "schools", "all_schools_data"
)


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
    baseX = lon_min
    baseY = lat_min
    distanceX = lon_max
    distanceY = lat_max
    pol_str = "POLYGON(({0} {1},{0} {3},{2} {3},{2} {1},{0} {1}))".format(
        baseX, baseY, distanceX, distanceY
    )
    pol_str_for_google_csv = "POLYGON(({0} {1},{0} {3},{2} {3},{2} {1},{0} {1}))".format(
        round(baseX, 6), round(baseY, 6), round(distanceX, 6), round(distanceY, 6)
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

    df = pd.read_sql_query(query_obj.statement, query_obj.session.bind)

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
        #
        acc_type=SUBTYPE_ACCIDENT_WITH_PEDESTRIAN,
        # TODO: location_accurate, location_approx: should be modified because we've added more location
        # approaches:
        # https://github.com/hasadna/anyway/pull/2223#discussion_r945924503
        location_accurate=location_accurate,
        location_approx=location_approx,
    )

    df["school_id"] = school.school_id
    df["institution_type"] = school.institution_type
    df["school_name"] = school.school_name
    df["school_yishuv_name"] = school.yishuv_name
    df["school_longitude"] = school.longitude
    df["school_latitude"] = school.latitude
    df["school_anyway_link"] = ui_url_map_only
    df["WKT Polygon"] = pol_str_for_google_csv
    df["WKT Point_12"] = "POINT(({0} {1})".format(
        round(school.longitude, 12), round(school.latitude, 12)
    )
    df["WKT Point_6"] = "POINT(({0} {1})".format(
        round(school.longitude, 6), round(school.latitude, 6)
    )
    return df


def calculate_injured_around_schools(start_date, end_date, distance):
    schools = (
        db.session.query(SchoolWithDescription2020)
        .filter(
            not_(
                and_(
                    SchoolWithDescription2020.latitude == 0,
                    SchoolWithDescription2020.longitude == 0,
                )
            ),
            not_(
                and_(
                    SchoolWithDescription2020.latitude == None,
                    SchoolWithDescription2020.longitude == None,
                )
            ),
        )
        .all()
    )
    if os.path.exists(ALL_SCHOOLS_DATA_DIR):
        shutil.rmtree(ALL_SCHOOLS_DATA_DIR)
    os.mkdir(ALL_SCHOOLS_DATA_DIR)
    PICKELS_DATA_DIR = os.path.join(ALL_SCHOOLS_DATA_DIR, "pickels")
    CSVS_DATA_DIR = os.path.join(ALL_SCHOOLS_DATA_DIR, "csvs")
    os.mkdir(PICKELS_DATA_DIR)
    os.mkdir(CSVS_DATA_DIR)
    df_schools = pd.DataFrame(schools, columns=["schools"])

    def create_school_data(school):
        df_curr = acc_inv_query(
            longitude=school.longitude,
            latitude=school.latitude,
            distance=distance,
            start_date=start_date,
            end_date=end_date,
            school=school,
        )

        curr_pkl_path = os.path.join(PICKELS_DATA_DIR, str(school.school_id) + ".pkl")
        curr_csv_path = os.path.join(CSVS_DATA_DIR, str(school.school_id) + ".csv")
        df_curr.to_pickle(curr_pkl_path)
        df_curr.to_csv(curr_csv_path, index=False)

    df_schools["schools"].swifter.apply(lambda school: create_school_data(school))


def import_to_datastore(start_date, end_date, distance, batch_size):
    assert batch_size > 0
    started = datetime.now()
    calculate_injured_around_schools(start_date, end_date, distance)
    logging.info(f"Finished saving in {time_delta(started)}")


def parse(start_date, end_date, distance, batch_size):
    started = datetime.now()
    total = import_to_datastore(
        start_date=start_date, end_date=end_date, distance=distance, batch_size=batch_size
    )
    logging.info("Total time {1}".format(total, time_delta(started)))
