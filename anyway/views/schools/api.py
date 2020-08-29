# pylint: disable=no-member

import json
import logging

import pandas as pd
from flask import Response, request
from sqlalchemy import and_, not_, or_, func

from anyway.base import db, user_optional
from anyway.models import (
    School,
    SchoolWithDescription,
    InjuredAroundSchool,
    Sex,
    InjuredAroundSchoolAllData,
    AccidentMonth,
    InjurySeverity,
)


@user_optional
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


@user_optional
def schools_description_api():
    # Disable all the no-member violations in this function
    # pylint: disable=no-member
    logging.debug("getting schools with description")
    query_obj = (
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
        .with_entities(
            SchoolWithDescription.school_id,
            SchoolWithDescription.school_name,
            SchoolWithDescription.students_number,
            SchoolWithDescription.municipality_name,
            SchoolWithDescription.yishuv_name,
            SchoolWithDescription.geo_district,
            SchoolWithDescription.school_type,
            SchoolWithDescription.foundation_year,
            SchoolWithDescription.location_accuracy,
            SchoolWithDescription.longitude,
            SchoolWithDescription.latitude,
        )
    )
    df = pd.read_sql_query(query_obj.statement, query_obj.session.bind)
    schools_list = df.to_dict(orient="records")
    response = Response(json.dumps(schools_list, default=str), mimetype="application/json")
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response


@user_optional
def schools_yishuvs_api():
    logging.debug("getting schools yishuvs")
    schools_yishuvs = (
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
        .group_by(SchoolWithDescription.yishuv_name)
        .with_entities(SchoolWithDescription.yishuv_name)
        .all()
    )
    schools_yishuvs_list = sorted([x[0] for x in schools_yishuvs])
    response = Response(json.dumps(schools_yishuvs_list, default=str), mimetype="application/json")
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response


@user_optional
def schools_names_api():
    # Disable all the no-member violations in this function
    # pylint: disable=no-member
    logging.debug("getting schools names")
    query_obj = (
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
        .with_entities(
            SchoolWithDescription.yishuv_name,
            SchoolWithDescription.school_name,
            SchoolWithDescription.longitude,
            SchoolWithDescription.latitude,
            SchoolWithDescription.school_id,
        )
    )
    df = pd.read_sql_query(query_obj.statement, query_obj.session.bind)
    df = df.groupby(["yishuv_name", "school_name", "longitude", "latitude"]).min()
    df = df.reset_index(drop=False)
    schools_names_ids = df.to_dict(orient="records")
    response = Response(json.dumps(schools_names_ids, default=str), mimetype="application/json")
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response


@user_optional
def injured_around_schools_api():
    # Disable all the no-member violations in this function
    # pylint: disable=no-member
    report_years = [2014, 2015, 2016, 2017, 2018]
    logging.debug("getting injured around schools api")
    school_id = request.values.get("school_id")
    if school_id is not None:
        query_obj = (
            db.session.query(InjuredAroundSchool)
            .filter(InjuredAroundSchool.school_id == school_id)
            .with_entities(
                InjuredAroundSchool.school_id,
                InjuredAroundSchool.accident_year,
                InjuredAroundSchool.killed_count,
                InjuredAroundSchool.severly_injured_count,
                InjuredAroundSchool.light_injured_count,
                InjuredAroundSchool.total_injured_killed_count,
                InjuredAroundSchool.rank_in_yishuv,
            )
        )
        df = pd.read_sql_query(query_obj.statement, query_obj.session.bind)
        if not df.empty:
            for year in report_years:
                if year not in list(df.accident_year.unique()):
                    df = df.append(
                        {
                            "school_id": df.school_id.values[0],
                            "accident_year": year,
                            "killed_count": 0,
                            "severly_injured_count": 0,
                            "light_injured_count": 0,
                            "total_injured_killed_count": 0,
                            "rank_in_yishuv": df.rank_in_yishuv.values[0],
                        },
                        ignore_index=True,
                    )
            final_list = df.to_dict(orient="records")
            response = Response(json.dumps(final_list, default=str), mimetype="application/json")
            response.headers.add("Access-Control-Allow-Origin", "*")
            return response
        else:
            query_obj = (
                db.session.query(SchoolWithDescription)
                .filter(SchoolWithDescription.school_id == school_id)
                .with_entities(SchoolWithDescription.school_id)
            )
            df_school_id = pd.read_sql_query(query_obj.statement, query_obj.session.bind)
            if not df_school_id.empty:
                final_list = []
                for year in report_years:
                    final_list.append(
                        {
                            "school_id": school_id,
                            "accident_year": year,
                            "killed_count": 0,
                            "severly_injured_count": 0,
                            "light_injured_count": 0,
                            "total_injured_killed_count": 0,
                            "rank_in_yishuv": None,
                        }
                    )
                response = Response(
                    json.dumps(final_list, default=str), mimetype="application/json"
                )
                response.headers.add("Access-Control-Allow-Origin", "*")
                return response

        response = Response(status=404)
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response
    school_yishuv_name = request.values.get("school_yishuv_name")
    if school_yishuv_name is not None:
        query_obj = (
            db.session.query(InjuredAroundSchool)
            .filter(InjuredAroundSchool.school_yishuv_name == school_yishuv_name)
            .with_entities(
                InjuredAroundSchool.school_id,
                InjuredAroundSchool.accident_year,
                InjuredAroundSchool.killed_count,
                InjuredAroundSchool.severly_injured_count,
                InjuredAroundSchool.light_injured_count,
                InjuredAroundSchool.total_injured_killed_count,
                InjuredAroundSchool.rank_in_yishuv,
            )
        )
        df = pd.read_sql_query(query_obj.statement, query_obj.session.bind)
        final_list = df.to_dict(orient="records")
        if not df.empty:
            response = Response(json.dumps(final_list, default=str), mimetype="application/json")
            response.headers.add("Access-Control-Allow-Origin", "*")
            return response
        response = Response(status=404)
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response
    query_obj = db.session.query(InjuredAroundSchool).with_entities(
        InjuredAroundSchool.school_id,
        InjuredAroundSchool.accident_year,
        InjuredAroundSchool.killed_count,
        InjuredAroundSchool.severly_injured_count,
        InjuredAroundSchool.light_injured_count,
        InjuredAroundSchool.total_injured_killed_count,
        InjuredAroundSchool.rank_in_yishuv,
    )
    df = pd.read_sql_query(query_obj.statement, query_obj.session.bind)
    final_list = df.to_dict(orient="records")
    response = Response(json.dumps(final_list, default=str), mimetype="application/json")
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response


@user_optional
def injured_around_schools_sex_graphs_data_api():
    # Disable all the no-member violations in this function
    # pylint: disable=no-member
    logging.debug("getting injured around schools sex graphs data api")
    school_id = request.values.get("school_id")
    if school_id is not None:
        query_obj = (
            db.session.query(InjuredAroundSchoolAllData)
            .filter(InjuredAroundSchoolAllData.school_id == school_id)
            .join(
                Sex,
                and_(
                    InjuredAroundSchoolAllData.involved_sex == Sex.id,
                    InjuredAroundSchoolAllData.markers_accident_year == Sex.year,
                    InjuredAroundSchoolAllData.markers_provider_code == Sex.provider_code,
                ),
            )
            .with_entities(
                InjuredAroundSchoolAllData.school_id,
                Sex.sex_hebrew,
                func.count(InjuredAroundSchoolAllData.school_id),
            )
            .group_by(InjuredAroundSchoolAllData.school_id, Sex.sex_hebrew)
        )
        df = pd.read_sql_query(query_obj.statement, query_obj.session.bind)
        query_obj = db.session.query(Sex).with_entities(Sex.sex_hebrew)
        df_sex = pd.read_sql_query(query_obj.statement, query_obj.session.bind)
        df_sex = df_sex.groupby(["sex_hebrew"]).size().reset_index(name="count")
        query_obj = (
            db.session.query(SchoolWithDescription)
            .filter(SchoolWithDescription.school_id == school_id)
            .with_entities(SchoolWithDescription.school_id)
        )
        df_school_id = pd.read_sql_query(query_obj.statement, query_obj.session.bind)
        if not df.empty:
            for sex in list(df_sex["sex_hebrew"].unique()):
                if sex not in list(df["sex_hebrew"].unique()):
                    df = df.append(
                        {"school_id": school_id, "sex_hebrew": sex, "count_1": 0}, ignore_index=True
                    )
            final_list = df.to_dict(orient="records")
            response = Response(json.dumps(final_list, default=str), mimetype="application/json")
            response.headers.add("Access-Control-Allow-Origin", "*")
            return response
        else:
            if not df_school_id.empty:
                final_list = []
                for sex in list(df_sex["sex_hebrew"].unique()):
                    final_list.append({"school_id": school_id, "sex_hebrew": sex, "count_1": 0})
                response = Response(
                    json.dumps(final_list, default=str), mimetype="application/json"
                )
                response.headers.add("Access-Control-Allow-Origin", "*")
                return response
    response = Response(status=404)
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response


@user_optional
def injured_around_schools_months_graphs_data_api():
    logging.debug("getting injured around schools months graphs data api")
    school_id = request.values.get("school_id")
    if school_id is not None:
        query_obj = (
            db.session.query(InjuredAroundSchoolAllData)
            .filter(InjuredAroundSchoolAllData.school_id == school_id)
            .join(
                AccidentMonth,
                and_(
                    InjuredAroundSchoolAllData.markers_accident_month == AccidentMonth.id,
                    InjuredAroundSchoolAllData.markers_accident_year == AccidentMonth.year,
                    InjuredAroundSchoolAllData.markers_provider_code == AccidentMonth.provider_code,
                ),
            )
            .join(
                InjurySeverity,
                and_(
                    InjuredAroundSchoolAllData.involved_injury_severity == InjurySeverity.id,
                    InjuredAroundSchoolAllData.markers_accident_year == InjurySeverity.year,
                    InjuredAroundSchoolAllData.markers_provider_code
                    == InjurySeverity.provider_code,
                ),
            )
            .with_entities(
                InjuredAroundSchoolAllData.school_id,
                AccidentMonth.accident_month_hebrew,
                InjurySeverity.injury_severity_hebrew,
                func.count(InjuredAroundSchoolAllData.school_id),
            )
            .group_by(
                InjuredAroundSchoolAllData.school_id,
                AccidentMonth.accident_month_hebrew,
                InjurySeverity.injury_severity_hebrew,
            )
        )
        df = pd.read_sql_query(query_obj.statement, query_obj.session.bind)
        query_obj = db.session.query(AccidentMonth).with_entities(
            AccidentMonth.accident_month_hebrew
        )
        df_month = pd.read_sql_query(query_obj.statement, query_obj.session.bind)
        df_month = df_month.groupby(["accident_month_hebrew"]).size().reset_index(name="count")
        query_obj = db.session.query(InjurySeverity).with_entities(
            InjurySeverity.injury_severity_hebrew
        )
        df_injury_severity = pd.read_sql_query(query_obj.statement, query_obj.session.bind)
        df_injury_severity = (
            df_injury_severity.groupby(["injury_severity_hebrew"]).size().reset_index(name="count")
        )
        if not df.empty:
            for month in list(df_month["accident_month_hebrew"].unique()):
                for injury_severity in list(df_injury_severity["injury_severity_hebrew"].unique()):
                    if month not in list(
                        df.accident_month_hebrew.unique()
                    ) or injury_severity not in list(
                        df[df.accident_month_hebrew == month].injury_severity_hebrew.unique()
                    ):
                        df = df.append(
                            {
                                "school_id": school_id,
                                "accident_month_hebrew": month,
                                "injury_severity_hebrew": injury_severity,
                                "count_1": 0,
                            },
                            ignore_index=True,
                        )
            final_list = df.to_dict(orient="records")
            response = Response(json.dumps(final_list, default=str), mimetype="application/json")
            response.headers.add("Access-Control-Allow-Origin", "*")
            return response
        else:
            query_obj = (
                db.session.query(SchoolWithDescription)
                .filter(SchoolWithDescription.school_id == school_id)
                .with_entities(SchoolWithDescription.school_id)
            )
            df_school_id = pd.read_sql_query(query_obj.statement, query_obj.session.bind)
            if not df_school_id.empty:
                final_list = []
                for month in list(df_month["accident_month_hebrew"].unique()):
                    for injury_severity in list(
                        df_injury_severity["injury_severity_hebrew"].unique()
                    ):
                        final_list.append(
                            {
                                "school_id": school_id,
                                "accident_month_hebrew": month,
                                "injury_severity_hebrew": injury_severity,
                                "count_1": 0,
                            }
                        )
                response = Response(
                    json.dumps(final_list, default=str), mimetype="application/json"
                )
                response.headers.add("Access-Control-Allow-Origin", "*")
                return response
    response = Response(status=404)
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response
