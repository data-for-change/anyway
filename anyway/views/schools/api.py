# pylint: disable=no-member

import json
import logging

import pandas as pd
from flask import Response, request
from sqlalchemy import and_, not_

from anyway.app_and_db import db
from anyway.models import School, SchoolWithDescription2020


def schools_api():
    logging.debug("getting schools")
    schools = (
        db.session.query(School)
        .filter(
            not_(and_(School.latitude == 0, School.longitude == 0)),
            not_(and_(School.latitude == None, School.longitude == None)),
        )
        .with_entities(
            School.yishuv_symbol,
            School.yishuv_name,
            School.school_name,
            School.longitude,
            School.latitude,
        )
        .all()
    )
    schools_list = [
        {
            "yishuv_symbol": x.yishuv_symbol,
            "yishuv_name": x.yishuv_name,
            "school_name": x.school_name,
            "longitude": x.longitude,
            "latitude": x.latitude,
        }
        for x in schools
    ]
    response = Response(json.dumps(schools_list, default=str), mimetype="application/json")
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response


def schools_description_api():
    # Disable all the no-member violations in this function
    # pylint: disable=no-member
    logging.debug("getting schools with description")
    query_obj = (
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
        .with_entities(
            SchoolWithDescription2020.school_id,
            SchoolWithDescription2020.school_name,
            SchoolWithDescription2020.municipality_name,
            SchoolWithDescription2020.yishuv_name,
            SchoolWithDescription2020.institution_type,
            SchoolWithDescription2020.location_accuracy,
            SchoolWithDescription2020.longitude,
            SchoolWithDescription2020.latitude,
        )
    )
    df = pd.read_sql_query(query_obj.statement, query_obj.session.bind)
    schools_list = df.to_dict(orient="records")
    response = Response(json.dumps(schools_list, default=str), mimetype="application/json")
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response


def schools_yishuvs_api():
    logging.debug("getting schools yishuvs")
    schools_yishuvs = (
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
        .group_by(SchoolWithDescription2020.yishuv_name)
        .with_entities(SchoolWithDescription2020.yishuv_name)
        .all()
    )
    schools_yishuvs_list = sorted([x[0] for x in schools_yishuvs])
    response = Response(json.dumps(schools_yishuvs_list, default=str), mimetype="application/json")
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response


def schools_names_api():
    # Disable all the no-member violations in this function
    # pylint: disable=no-member
    logging.debug("getting schools names")
    schools_data = json.load(open("static/data/schools/schools_names.json"))
    response = Response(json.dumps(schools_data, default=str), mimetype="application/json")
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response


def injured_around_schools_api():
    # Disable all the no-member violations in this function
    # pylint: disable=no-member
    logging.debug("getting injured around schools api")
    school_id = request.values.get("school_id")
    all_data = json.load(open("static/data/schools/injured_around_schools_api_2022.json"))
    school_data = all_data[school_id]
    response = Response(json.dumps(school_data, default=str), mimetype="application/json")
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response


def injured_around_schools_sex_graphs_data_api():
    # Disable all the no-member violations in this function
    # pylint: disable=no-member
    logging.debug("getting injured around schools sex graphs data api")
    school_id = request.values.get("school_id")
    all_data = json.load(
        open("static/data/schools/injured_around_schools_sex_graphs_data_api_2022.json")
    )
    school_data = all_data[school_id]
    response = Response(json.dumps(school_data, default=str), mimetype="application/json")
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response


def injured_around_schools_months_graphs_data_api():
    logging.debug("getting injured around schools months graphs data api")
    school_id = request.values.get("school_id")
    all_data = json.load(
        open("static/data/schools/injured_around_schools_months_graphs_data_api_2022.json")
    )
    school_data = all_data[school_id]
    response = Response(json.dumps(school_data, default=str), mimetype="application/json")
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response
