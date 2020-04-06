# -*- coding: utf-8 -*-
# pylint: disable=no-member
import csv
import datetime
# from sendgrid import SendGridAPIClient
import json
import logging
import os
import time

import flask_admin as admin
import flask_login as login
import jinja2
import pandas as pd
import six
from flask import make_response, render_template, Response, jsonify, url_for, flash, abort
from flask import request, redirect, session
from flask_admin import helpers, expose, BaseView
from flask_admin.contrib import sqla
from flask_assets import Environment
from flask_babel import Babel, gettext
from flask_compress import Compress
from flask_cors import CORS
from flask_security import Security, SQLAlchemyUserDatastore, roles_required, current_user, LoginForm, login_required
from flask_sqlalchemy import SQLAlchemy
from sendgrid import Mail
from six import StringIO, iteritems
from six.moves import http_client
from sqlalchemy import and_, not_, or_
from sqlalchemy import func
from sqlalchemy.orm import load_only
from webassets import Environment as AssetsEnvironment
from webassets.ext.jinja2 import AssetsExtension
from werkzeug.security import check_password_hash
from wtforms import form, fields, validators, StringField, PasswordField, Form

from . import utilities
from .base import user_optional
from .clusters_calculator import retrieve_clusters
from .config import ENTRIES_PER_PAGE
from .constants import CONST
from .models import (AccidentMarker, DiscussionMarker, HighlightPoint, Involved, User,
                     ReportPreferences,
                     LocationSubscribers, Vehicle, Role, GeneralPreferences, NewsFlash, School, SchoolWithDescription,
                     InjuredAroundSchool, InjuredAroundSchoolAllData, Sex, AccidentMonth, InjurySeverity, ReportProblem,
                     EngineVolume, PopulationType, Region, District, NaturalArea, MunicipalStatus, YishuvShape,
                     TotalWeight, DrivingDirections, AgeGroup, AccidentMarkerView, InvolvedMarkerView, EmbeddedReports)
from .oauth import OAuthSignIn
from .parsers import resolution_dict

app = utilities.init_flask()
db = SQLAlchemy(app)
app.config.from_object(__name__)
app.config['SECURITY_REGISTERABLE'] = False
app.config['SECURITY_USER_IDENTITY_ATTRIBUTES'] = 'username'
app.config['BABEL_DEFAULT_LOCALE'] = 'he'
app.config['OAUTH_CREDENTIALS'] = {
    'facebook': {
        'id': os.environ.get('FACEBOOK_KEY'),
        'secret': os.environ.get('FACEBOOK_SECRET')
    },
    'google': {
        'id': os.environ.get('GOOGLE_LOGIN_CLIENT_ID'),
        'secret': os.environ.get('GOOGLE_LOGIN_CLIENT_SECRET')
    }
}

assets = Environment()
assets.init_app(app)
assets_env = AssetsEnvironment(os.path.join(utilities._PROJECT_ROOT, 'static'), '/static')

CORS(app, resources={r"/location-subscription": {"origins": "*"},
                     r"/report-problem": {"origins": "*"},
                     r"/api/infographics_data": {"origins": "*"},
                     r"/api/news-flash-filters": {"origins": "*"},
                     r"/api/embedded-reports": {"origins": "*"}})

jinja_environment = jinja2.Environment(
    autoescape=True,
    loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), "../templates")),
    extensions=[AssetsExtension])
jinja_environment.assets_environment = assets_env

# sg = SendGridAPIClient(app.config['SENDGRID_API_KEY'])

babel = Babel(app)

SESSION_HIGHLIGHTPOINT_KEY = 'gps_highlightpoint_created'

DICTIONARY = "Dictionary"
DICTCOLUMN1 = "MS_TAVLA"
DICTCOLUMN2 = "KOD"
DICTCOLUMN3 = "TEUR"
cbs_dict_files = {DICTIONARY: "Dictionary.csv"}
content_encoding = 'cp1255'

Compress(app)


@app.teardown_appcontext
def shutdown_session(exception=None):
    db.session.remove()


def generate_json(accidents, rsa_markers, discussions, is_thin, total_records=None):
    markers = accidents.all()
    total_accidents = len(markers)

    rsa = rsa_markers.all()
    total_rsa = len(rsa)
    markers += rsa

    if not is_thin:
        markers += discussions.all()

    if total_records is None:
        total_records = len(markers)

    entries = [marker.serialize(is_thin) for marker in markers]
    return jsonify({"markers": entries, 'pagination': {'totalRecords': total_records,
                                                       'totalAccidents': total_accidents,
                                                       'totalRSA': total_rsa}})


def generate_csv(results):
    output_file = StringIO()
    yield output_file.getvalue()
    output_file.truncate(0)
    output = None
    for marker in results.all():
        serialized = marker.serialize()
        if not output:
            output = csv.DictWriter(output_file, serialized.keys())
            output.writeheader()

        row = {k: v.encode('utf8')
        if type(v) is six.text_type else v
               for k, v in iteritems(serialized)}
        output.writerow(row)
        yield output_file.getvalue()
        output_file.truncate(0)


ARG_TYPES = {'ne_lat': (float, 32.072427482938345), 'ne_lng': (float, 34.79928962966915),
             'sw_lat': (float, 34.79928962966915), 'sw_lng': (float, 34.78877537033077), 'zoom': (int, 17),
             'show_fatal': (bool, True), 'show_severe': (bool, True), 'show_light': (bool, True),
             'approx': (bool, True), 'accurate': (bool, True), 'show_markers': (bool, True),
             'show_accidents': (bool, True), 'show_rsa': (bool, True), 'show_discussions': (bool, True),
             'show_urban': (int, 3), 'show_intersection': (int, 3), 'show_lane': (int, 3), 'show_day': (int, 0),
             'show_holiday': (int, 0), 'show_time': (int, 24), 'start_time': (int, 25), 'end_time': (int, 25),
             'weather': (int, 0), 'road': (int, 0), 'separation': (int, 0), 'surface': (int, 0), 'acctype': (int, 0),
             'controlmeasure': (int, 0), 'district': (int, 0), 'case_type': (int, 0), 'fetch_markers': (bool, True),
             'fetch_vehicles': (bool, True), 'fetch_involved': (bool, True),
             'age_groups': (str, str(CONST.ALL_AGE_GROUPS_LIST).strip('[]').replace(' ', '')),
             'page': (int, 0), 'per_page': (int, 0)}


def get_kwargs():
    kwargs = {arg: arg_type(request.values.get(arg, default_value)) for (arg, (arg_type, default_value)) in
              iteritems(ARG_TYPES)}
    if request.values.get('age_groups[]') == '1234' or request.values.get('age_groups') == '1234':
        kwargs['age_groups'] = '1,2,3,4'
    try:
        kwargs.update(
            {arg: datetime.date.fromtimestamp(int(request.values[arg])) for arg in ('start_date', 'end_date')})
    except ValueError:
        abort(http_client.BAD_REQUEST)
    return kwargs


@babel.localeselector
def get_locale():
    lang = request.values.get('lang')
    if lang is None:
        return request.accept_languages.best_match(app.config['LANGUAGES'].keys())
    else:
        return lang


@app.route('/schools', methods=["GET"])
@user_optional
def schools():
    if request.method == "GET":
        return render_template('schools_dashboard_react.html')
    else:
        return Response("Method Not Allowed", 405)


@app.route('/schools-report', methods=["GET"])
@user_optional
def schools_report():
    if request.method == "GET":
        return render_template('schools_dashboard_react.html')
    else:
        return Response("Method Not Allowed", 405)


@app.route("/markers", methods=["GET"])
@user_optional
def markers():
    logging.debug('getting markers')
    kwargs = get_kwargs()
    logging.debug('querying markers in bounding box: %s' % kwargs)
    is_thin = (kwargs['zoom'] < CONST.MINIMAL_ZOOM)
    result = AccidentMarker.bounding_box_query(is_thin, yield_per=50, involved_and_vehicles=False, **kwargs)
    accident_markers = result.accident_markers
    rsa_markers = result.rsa_markers

    discussion_args = ('ne_lat', 'ne_lng', 'sw_lat', 'sw_lng', 'show_discussions')
    discussions = DiscussionMarker.bounding_box_query(**{arg: kwargs[arg] for arg in discussion_args})

    if request.values.get('format') == 'csv':
        date_format = '%Y-%m-%d'
        return Response(generate_csv(accident_markers), headers={
            "Content-Type": "text/csv",
            "Content-Disposition": 'attachment; '
                                   'filename="Anyway-accidents-from-{0}-to-{1}.csv"'
                        .format(kwargs["start_date"].strftime(date_format), kwargs["end_date"].strftime(date_format))
        })

    else:  # defaults to json
        return generate_json(accident_markers, rsa_markers, discussions, is_thin, total_records=result.total_records)


@app.route("/markers_by_yishuv_symbol", methods=["GET"])
@user_optional
def markers_by_yishuv_symbol():
    logging.debug('getting markers by yishuv symbol')
    yishuv_symbol = request.values.get('yishuv_symbol')
    markers = db.session.query(AccidentMarker).filter(AccidentMarker.yishuv_symbol == yishuv_symbol).all()
    entries = [marker.serialize(True) for marker in markers]
    return jsonify({"markers": entries})


@app.route("/markers_hebrew_by_yishuv_symbol", methods=["GET"])
@user_optional
def markers_hebrew_by_yishuv_symbol():
    logging.debug('getting hebrew markers by yishuv symbol')
    yishuv_symbol = request.values.get('yishuv_symbol')
    markers = db.session.query(AccidentMarkerView).filter(AccidentMarkerView.yishuv_symbol == yishuv_symbol).all()
    entries = [marker.serialize() for marker in markers]
    return Response(json.dumps(entries, default=str), mimetype="application/json")


@app.route("/yishuv_symbol_to_yishuv_name", methods=["GET"])
@user_optional
def yishuv_symbol_to_name():
    """
    output example:
    [
        {
            "yishuv_symbol": 667,
            "yishuv_name": "ברעם"
        },
        {
            "yishuv_symbol": 424,
            "yishuv_name": "גבים"
        },
        {
            "yishuv_symbol": 1080,
            "yishuv_name": "מבועים"
        }
    ]
    """
    logging.debug('getting yishuv symbol and yishuv name pairs')
    markers = db.session.query(
        AccidentMarkerView.yishuv_name,
        AccidentMarkerView.yishuv_symbol
    ).filter(
        not_(AccidentMarkerView.yishuv_name == None)
    ).group_by(
        AccidentMarkerView.yishuv_name,
        AccidentMarkerView.yishuv_symbol
    ).all()
    entries = [{"yishuv_name": x.yishuv_name, "yishuv_symbol": x.yishuv_symbol} for x in markers]
    return Response(json.dumps(entries, default=str), mimetype="application/json")


@app.route("/api/news-flash-filters", methods=["GET"])
@user_optional
def news_flash_filters():
    logging.debug('getting filtered news flash')
    source = request.values.get('source')
    count = request.values.get('news_flash_count')
    start_date = request.values.get('start_date')
    end_date = request.values.get('end_date')
    news_flash_obj = db.session.query(NewsFlash)

    # get all possible sources
    sources = [str(source_name[0]) for source_name in db.session.query(NewsFlash.source).distinct().all()]
    if source:
        if source not in sources:
            return Response('{"message": "Requested source does not exist"}',
                            status=404,
                            mimetype='application/json')
        else:
            news_flash_obj = news_flash_obj.filter(NewsFlash.source == source)

    if start_date and end_date:
        s = datetime.datetime.fromtimestamp(int(start_date))
        e = datetime.datetime.fromtimestamp(int(end_date))
        news_flash_obj = news_flash_obj.filter(and_(NewsFlash.date <= e,
                                                    NewsFlash.date >= s))

    # when only one of the dates is sent
    elif start_date or end_date:
        return Response('{"message": "Must send both start_date and end_date"}',
                        status=404,
                        mimetype='application/json')

    news_flash_obj = news_flash_obj.filter(
        and_(NewsFlash.accident == True, not_(and_(NewsFlash.lat == 0, NewsFlash.lon == 0)),
             not_(and_(NewsFlash.lat == None, NewsFlash.lon == None)))
    ).order_by(
        NewsFlash.date.desc())

    if count:
        news_flash_obj = news_flash_obj.limit(count)

    news_flashes = news_flash_obj.all()

    news_flashes_jsons = [news_flash.serialize() for news_flash in news_flashes]
    return Response(json.dumps(news_flashes_jsons, default=str), mimetype="application/json")


@app.route("/api/news-flash", methods=["GET"])
@user_optional
def news_flash():
    logging.debug('getting news flash')
    news_flash_id = request.values.get('id')
    if news_flash_id is not None:
        news_flash_obj = db.session.query(NewsFlash).filter(NewsFlash.id == news_flash_id).first()
        if news_flash_obj is not None:
            return Response(json.dumps(news_flash_obj.serialize(), default=str), mimetype="application/json")
        return Response(status=404)

    # Todo - add start and end time for the news flashes
    news_flashes = db.session.query(NewsFlash).filter(
        and_(NewsFlash.accident == True, not_(and_(NewsFlash.lat == 0, NewsFlash.lon == 0)),
             not_(and_(NewsFlash.lat == None, NewsFlash.lon == None)))).with_entities(NewsFlash.id,
                                                                                      NewsFlash.lat,
                                                                                      NewsFlash.lon,
                                                                                      NewsFlash.title, NewsFlash.source,
                                                                                      NewsFlash.date).order_by(
        NewsFlash.date.desc()).all()
    news_flashes = [{"id": x.id, "lat": x.lat, "lon": x.lon, "title": x.title, "source": x.source, "date": x.date} for x
                    in news_flashes]
    return Response(json.dumps(news_flashes, default=str), mimetype="application/json")


@app.route("/api/news-flash/<int:news_flash_id>", methods=["GET"])
@user_optional
def single_news_flash(news_flash_id):
    news_flash_obj = db.session.query(NewsFlash).filter(NewsFlash.id == news_flash_id).first()
    if news_flash_obj is not None:
        return Response(json.dumps(news_flash_obj.serialize(), default=str), mimetype="application/json")
    return Response(status=404)


@app.route("/api/schools", methods=["GET"])
@user_optional
def schools_api():
    logging.debug('getting schools')
    schools = db.session.query(School).filter(not_(and_(School.latitude == 0, School.longitude == 0)), \
                                              not_(and_(School.latitude == None, School.longitude == None))) \
        .with_entities(School.yishuv_symbol,
                       School.yishuv_name,
                       School.school_name,
                       School.longitude,
                       School.latitude).all()
    schools_list = [{"yishuv_symbol": x.yishuv_symbol,
                     "yishuv_name": x.yishuv_name,
                     "school_name": x.school_name,
                     "longitude": x.longitude,
                     "latitude": x.latitude} for x in schools]
    response = Response(json.dumps(schools_list, default=str), mimetype="application/json")
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@app.route("/api/schools-description", methods=["GET"])
@user_optional
def schools_description_api():
    logging.debug('getting schools with description')
    query_obj = db.session.query(SchoolWithDescription) \
        .filter(not_(and_(SchoolWithDescription.latitude == 0, SchoolWithDescription.longitude == 0)), \
                not_(and_(SchoolWithDescription.latitude == None, SchoolWithDescription.longitude == None)), \
                or_(SchoolWithDescription.school_type == 'גן ילדים', SchoolWithDescription.school_type == 'בית ספר')) \
        .with_entities(SchoolWithDescription.school_id,
                       SchoolWithDescription.school_name,
                       SchoolWithDescription.students_number,
                       SchoolWithDescription.municipality_name,
                       SchoolWithDescription.yishuv_name,
                       SchoolWithDescription.geo_district,
                       SchoolWithDescription.school_type,
                       SchoolWithDescription.foundation_year,
                       SchoolWithDescription.location_accuracy,
                       SchoolWithDescription.longitude,
                       SchoolWithDescription.latitude)
    df = pd.read_sql_query(query_obj.statement, query_obj.session.bind)
    schools_list = df.to_dict(orient='records')
    response = Response(json.dumps(schools_list, default=str), mimetype="application/json")
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@app.route("/api/schools-yishuvs", methods=["GET"])
@user_optional
def schools_yishuvs_api():
    logging.debug('getting schools yishuvs')
    schools_yishuvs = db.session.query(SchoolWithDescription) \
        .filter(not_(and_(SchoolWithDescription.latitude == 0, SchoolWithDescription.longitude == 0)), \
                not_(and_(SchoolWithDescription.latitude == None, SchoolWithDescription.longitude == None)), \
                or_(SchoolWithDescription.school_type == 'גן ילדים', SchoolWithDescription.school_type == 'בית ספר')) \
        .group_by(SchoolWithDescription.yishuv_name) \
        .with_entities(SchoolWithDescription.yishuv_name).all()
    schools_yishuvs_list = sorted([x[0] for x in schools_yishuvs])
    response = Response(json.dumps(schools_yishuvs_list, default=str), mimetype="application/json")
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@app.route("/api/schools-names", methods=["GET"])
@user_optional
def schools_names_api():
    logging.debug('getting schools names')
    query_obj = db.session.query(SchoolWithDescription) \
        .filter(not_(and_(SchoolWithDescription.latitude == 0, SchoolWithDescription.longitude == 0)), \
                not_(and_(SchoolWithDescription.latitude == None, SchoolWithDescription.longitude == None)), \
                or_(SchoolWithDescription.school_type == 'גן ילדים', SchoolWithDescription.school_type == 'בית ספר')) \
        .with_entities(SchoolWithDescription.yishuv_name,
                       SchoolWithDescription.school_name,
                       SchoolWithDescription.longitude,
                       SchoolWithDescription.latitude,
                       SchoolWithDescription.school_id)
    df = pd.read_sql_query(query_obj.statement, query_obj.session.bind)
    df = df.groupby(['yishuv_name', 'school_name', 'longitude', 'latitude']).min()
    df = df.reset_index(drop=False)
    schools_names_ids = df.to_dict(orient='records')
    response = Response(json.dumps(schools_names_ids, default=str), mimetype="application/json")
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@app.route("/api/injured-around-schools", methods=["GET"])
@user_optional
def injured_around_schools_api():
    report_years = [2014, 2015, 2016, 2017, 2018]
    logging.debug('getting injured around schools api')
    school_id = request.values.get('school_id')
    if school_id is not None:
        query_obj = db.session.query(InjuredAroundSchool).filter(InjuredAroundSchool.school_id == school_id) \
            .with_entities(InjuredAroundSchool.school_id,
                           InjuredAroundSchool.accident_year,
                           InjuredAroundSchool.killed_count,
                           InjuredAroundSchool.severly_injured_count,
                           InjuredAroundSchool.light_injured_count,
                           InjuredAroundSchool.total_injured_killed_count,
                           InjuredAroundSchool.rank_in_yishuv)
        df = pd.read_sql_query(query_obj.statement, query_obj.session.bind)
        if not df.empty:
            for year in report_years:
                if year not in list(df.accident_year.unique()):
                    df = df.append({'school_id': df.school_id.values[0],
                                    'accident_year': year,
                                    'killed_count': 0,
                                    'severly_injured_count': 0,
                                    'light_injured_count': 0,
                                    'total_injured_killed_count': 0,
                                    'rank_in_yishuv': df.rank_in_yishuv.values[0]},
                                   ignore_index=True)
            final_list = df.to_dict(orient='records')
            response = Response(json.dumps(final_list, default=str), mimetype="application/json")
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
        else:
            query_obj = db.session.query(SchoolWithDescription) \
                .filter(SchoolWithDescription.school_id == school_id) \
                .with_entities(SchoolWithDescription.school_id)
            df_school_id = pd.read_sql_query(query_obj.statement, query_obj.session.bind)
            if not df_school_id.empty:
                final_list = []
                for year in report_years:
                    final_list.append({'school_id': school_id,
                                       'accident_year': year,
                                       'killed_count': 0,
                                       'severly_injured_count': 0,
                                       'light_injured_count': 0,
                                       'total_injured_killed_count': 0,
                                       'rank_in_yishuv': None})
                response = Response(json.dumps(final_list, default=str), mimetype="application/json")
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response

        response = Response(status=404)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    school_yishuv_name = request.values.get('school_yishuv_name')
    if school_yishuv_name is not None:
        query_obj = db.session.query(InjuredAroundSchool).filter(
            InjuredAroundSchool.school_yishuv_name == school_yishuv_name) \
            .with_entities(InjuredAroundSchool.school_id,
                           InjuredAroundSchool.accident_year,
                           InjuredAroundSchool.killed_count,
                           InjuredAroundSchool.severly_injured_count,
                           InjuredAroundSchool.light_injured_count,
                           InjuredAroundSchool.total_injured_killed_count,
                           InjuredAroundSchool.rank_in_yishuv)
        df = pd.read_sql_query(query_obj.statement, query_obj.session.bind)
        final_list = df.to_dict(orient='records')
        if not df.empty:
            response = Response(json.dumps(final_list, default=str), mimetype="application/json")
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
        response = Response(status=404)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    query_obj = db.session.query(InjuredAroundSchool).with_entities(InjuredAroundSchool.school_id,
                                                                    InjuredAroundSchool.accident_year,
                                                                    InjuredAroundSchool.killed_count,
                                                                    InjuredAroundSchool.severly_injured_count,
                                                                    InjuredAroundSchool.light_injured_count,
                                                                    InjuredAroundSchool.total_injured_killed_count,
                                                                    InjuredAroundSchool.rank_in_yishuv)
    df = pd.read_sql_query(query_obj.statement, query_obj.session.bind)
    final_list = df.to_dict(orient='records')
    response = Response(json.dumps(final_list, default=str), mimetype="application/json")
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@app.route("/api/injured-around-schools-sex-graphs-data", methods=["GET"])
@user_optional
def injured_around_schools_sex_graphs_data_api():
    logging.debug('getting injured around schools sex graphs data api')
    school_id = request.values.get('school_id')
    if school_id is not None:
        query_obj = db.session.query(InjuredAroundSchoolAllData) \
            .filter(InjuredAroundSchoolAllData.school_id == school_id) \
            .join(Sex, and_(InjuredAroundSchoolAllData.involved_sex == Sex.id,
                            InjuredAroundSchoolAllData.markers_accident_year == Sex.year,
                            InjuredAroundSchoolAllData.markers_provider_code == Sex.provider_code)) \
            .with_entities(InjuredAroundSchoolAllData.school_id,
                           Sex.sex_hebrew,
                           func.count(InjuredAroundSchoolAllData.school_id)) \
            .group_by(InjuredAroundSchoolAllData.school_id,
                      Sex.sex_hebrew)
        df = pd.read_sql_query(query_obj.statement, query_obj.session.bind)
        query_obj = db.session.query(Sex) \
            .with_entities(Sex.sex_hebrew)
        df_sex = pd.read_sql_query(query_obj.statement, query_obj.session.bind)
        df_sex = df_sex.groupby(['sex_hebrew']).size().reset_index(name='count')
        query_obj = db.session.query(SchoolWithDescription) \
            .filter(SchoolWithDescription.school_id == school_id) \
            .with_entities(SchoolWithDescription.school_id)
        df_school_id = pd.read_sql_query(query_obj.statement, query_obj.session.bind)
        if not df.empty:
            for sex in list(df_sex['sex_hebrew'].unique()):
                if sex not in list(df['sex_hebrew'].unique()):
                    df = df.append({'school_id': school_id,
                                    'sex_hebrew': sex,
                                    'count_1': 0},
                                   ignore_index=True)
            final_list = df.to_dict(orient='records')
            response = Response(json.dumps(final_list, default=str), mimetype="application/json")
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
        else:
            if not df_school_id.empty:
                final_list = []
                for sex in list(df_sex['sex_hebrew'].unique()):
                    final_list.append({'school_id': school_id,
                                       'sex_hebrew': sex,
                                       'count_1': 0})
                response = Response(json.dumps(final_list, default=str), mimetype="application/json")
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response
    response = Response(status=404)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@app.route("/api/injured-around-schools-months-graphs-data", methods=["GET"])
@user_optional
def injured_around_schools_months_graphs_data_api():
    logging.debug('getting injured around schools months graphs data api')
    school_id = request.values.get('school_id')
    if school_id is not None:
        query_obj = db.session.query(InjuredAroundSchoolAllData) \
            .filter(InjuredAroundSchoolAllData.school_id == school_id) \
            .join(AccidentMonth, and_(InjuredAroundSchoolAllData.markers_accident_month == AccidentMonth.id,
                                      InjuredAroundSchoolAllData.markers_accident_year == AccidentMonth.year,
                                      InjuredAroundSchoolAllData.markers_provider_code == AccidentMonth.provider_code)) \
            .join(InjurySeverity, and_(InjuredAroundSchoolAllData.involved_injury_severity == InjurySeverity.id,
                                       InjuredAroundSchoolAllData.markers_accident_year == InjurySeverity.year,
                                       InjuredAroundSchoolAllData.markers_provider_code == InjurySeverity.provider_code)) \
            .with_entities(InjuredAroundSchoolAllData.school_id,
                           AccidentMonth.accident_month_hebrew,
                           InjurySeverity.injury_severity_hebrew,
                           func.count(InjuredAroundSchoolAllData.school_id)) \
            .group_by(InjuredAroundSchoolAllData.school_id,
                      AccidentMonth.accident_month_hebrew,
                      InjurySeverity.injury_severity_hebrew)
        df = pd.read_sql_query(query_obj.statement, query_obj.session.bind)
        query_obj = db.session.query(AccidentMonth) \
            .with_entities(AccidentMonth.accident_month_hebrew)
        df_month = pd.read_sql_query(query_obj.statement, query_obj.session.bind)
        df_month = df_month.groupby(['accident_month_hebrew']).size().reset_index(name='count')
        query_obj = db.session.query(InjurySeverity) \
            .with_entities(InjurySeverity.injury_severity_hebrew)
        df_injury_severity = pd.read_sql_query(query_obj.statement, query_obj.session.bind)
        df_injury_severity = df_injury_severity.groupby(['injury_severity_hebrew']).size().reset_index(name='count')
        if not df.empty:
            for month in list(df_month['accident_month_hebrew'].unique()):
                for injury_severity in list(df_injury_severity['injury_severity_hebrew'].unique()):
                    if month not in list(df.accident_month_hebrew.unique()) \
                            or injury_severity not in list(
                        df[df.accident_month_hebrew == month].injury_severity_hebrew.unique()):
                        df = df.append({'school_id': school_id,
                                        'accident_month_hebrew': month,
                                        'injury_severity_hebrew': injury_severity,
                                        'count_1': 0},
                                       ignore_index=True)
            final_list = df.to_dict(orient='records')
            response = Response(json.dumps(final_list, default=str), mimetype="application/json")
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
        else:
            query_obj = db.session.query(SchoolWithDescription) \
                .filter(SchoolWithDescription.school_id == school_id) \
                .with_entities(SchoolWithDescription.school_id)
            df_school_id = pd.read_sql_query(query_obj.statement, query_obj.session.bind)
            if not df_school_id.empty:
                final_list = []
                for month in list(df_month['accident_month_hebrew'].unique()):
                    for injury_severity in list(df_injury_severity['injury_severity_hebrew'].unique()):
                        final_list.append({'school_id': school_id,
                                           'accident_month_hebrew': month,
                                           'injury_severity_hebrew': injury_severity,
                                           'count_1': 0})
                response = Response(json.dumps(final_list, default=str), mimetype="application/json")
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response
    response = Response(status=404)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@app.route("/charts-data", methods=["GET"])
@user_optional
def charts_data():
    logging.debug('getting charts data')
    kwargs = get_kwargs()
    accidents, vehicles, involved = AccidentMarker.bounding_box_query(is_thin=False, yield_per=50,
                                                                      involved_and_vehicles=True, **kwargs)
    accidents_list = [acc.serialize() for acc in accidents]
    vehicles_list = [vehicles_data_refinement(veh.serialize()) for veh in vehicles]
    involved_list = [involved_data_refinement(inv.serialize()) for inv in involved]
    return Response(json.dumps({'accidents': accidents_list, 'vehicles': vehicles_list, 'involved': involved_list}),
                    mimetype="application/json")


def vehicles_data_refinement(vehicle):
    provider_code = vehicle["provider_code"]
    accident_year = vehicle["accident_year"]
    new_vehicle = get_vehicle_dict(provider_code, accident_year)

    vehicle["engine_volume"] = new_vehicle["engine_volume"]
    vehicle["total_weight"] = new_vehicle["total_weight"]
    vehicle["driving_directions"] = new_vehicle["driving_directions"]

    return vehicle


def involved_data_refinement(involved):
    provider_code = involved["provider_code"]
    accident_year = involved["accident_year"]
    new_involved = get_involved_dict(provider_code, accident_year)

    involved["age_group"] = new_involved["age_group"]
    involved["population_type"] = new_involved["population_type"]
    involved["home_region"] = new_involved["home_region"]
    involved["home_district"] = new_involved["home_district"]
    involved["home_natural_area"] = new_involved["home_natural_area"]
    involved["home_municipal_status"] = new_involved["home_municipal_status"]
    involved["home_yishuv_shape"] = new_involved["home_yishuv_shape"]

    return involved


def get_involved_dict(provider_code, accident_year):
    involved = {}
    age_group = db.session.query(AgeGroup).filter(and_(AgeGroup.provider_code == provider_code,
                                                       AgeGroup.year == accident_year)).all()
    involved["age_group"] = {g.id: g.age_group_hebrew for g in age_group} if age_group else None

    population_type = db.session.query(PopulationType).filter(and_(PopulationType.provider_code == provider_code,
                                                                   PopulationType.year == accident_year)).all()

    involved["population_type"] = {g.id: g.population_type_hebrew for g in population_type} if population_type else None

    home_region = db.session.query(Region).filter(and_(Region.provider_code == provider_code,
                                                       Region.year == accident_year)).all()

    involved["home_region"] = {g.id: g.region_hebrew for g in home_region} if home_region else None

    home_district = db.session.query(District).filter(and_(District.provider_code == provider_code,
                                                           District.year == accident_year)).all()

    involved["home_district"] = {g.id: g.district_hebrew for g in home_district} if home_district else None

    home_natural_area = db.session.query(NaturalArea).filter(and_(NaturalArea.provider_code == provider_code,
                                                                  NaturalArea.year == accident_year)).all()

    involved["home_natural_area"] = {g.id: g.natural_area_hebrew for g in
                                     home_natural_area} if home_natural_area else None

    home_municipal_status = db.session.query(MunicipalStatus).filter(
        and_(MunicipalStatus.provider_code == provider_code,
             MunicipalStatus.year == accident_year)).all()
    involved[
        "home_municipal_status"] = {g.id: g.municipal_status_hebrew for g in
                                    home_municipal_status} if home_municipal_status else None

    home_yishuv_shape = db.session.query(YishuvShape).filter(and_(YishuvShape.provider_code == provider_code,
                                                                  YishuvShape.year == accident_year)).all()

    involved["home_yishuv_shape"] = {g.id: g.yishuv_shape_hebrew for g in
                                     home_yishuv_shape} if home_yishuv_shape else None

    return involved


def get_vehicle_dict(provider_code, accident_year):
    vehicle = {}
    engine_volume = db.session.query(EngineVolume) \
        .filter(and_(EngineVolume.provider_code == provider_code, EngineVolume.year == accident_year)) \
        .all()

    vehicle["engine_volume"] = {g.id: g.engine_volume_hebrew for g in engine_volume} if engine_volume else None

    total_weight = db.session.query(TotalWeight) \
        .filter(and_(TotalWeight.provider_code == provider_code, TotalWeight.year == accident_year)) \
        .all()
    vehicle["total_weight"] = {g.id: g.total_weight_hebrew for g in total_weight} if total_weight else None

    driving_directions = db.session.query(DrivingDirections) \
        .filter(and_(DrivingDirections.provider_code == provider_code, DrivingDirections.year == accident_year)) \
        .all()
    vehicle["driving_directions"] = {g.id: g.driving_directions_hebrew for g in
                                     driving_directions} if driving_directions else None

    return vehicle


@app.route("/markers/all", methods=["GET"])
def marker_all():
    marker_id = request.args.get('marker_id', None)
    provider_code = request.args.get('provider_code', None)
    accident_year = request.args.get('accident_year', None)

    involved = db.session.query(Involved).filter(and_(Involved.accident_id == marker_id,
                                                      Involved.provider_code == provider_code,
                                                      Involved.accident_year == accident_year))

    vehicles = db.session.query(Vehicle).filter(and_(Vehicle.accident_id == marker_id,
                                                     Vehicle.provider_code == provider_code,
                                                     Vehicle.accident_year == accident_year))

    list_to_return = list()
    for inv in involved:
        obj = inv.serialize()
        new_inv = get_involved_dict(provider_code, accident_year)
        obj["age_group"] = new_inv["age_group"].get(obj["age_group"]) if new_inv["age_group"] else None
        obj["population_type"] = new_inv["population_type"].get(obj["population_type"]) if new_inv[
            "population_type"] else None
        obj["home_region"] = new_inv["home_region"].get(obj["home_region"]) if new_inv["home_region"] else None
        obj["home_district"] = new_inv["home_district"].get(obj["home_district"]) if new_inv["home_district"] else None
        obj["home_natural_area"] = new_inv["home_natural_area"].get(obj["home_natural_area"]) if new_inv[
            "home_natural_area"] else None
        obj["home_municipal_status"] = new_inv["home_municipal_status"].get(obj["home_municipal_status"]) if new_inv[
            "home_municipal_status"] else None
        obj["home_yishuv_shape"] = new_inv["home_yishuv_shape"].get(obj["home_yishuv_shape"]) if new_inv[
            "home_yishuv_shape"] else None

        list_to_return.append(obj)

    for veh in vehicles:
        obj = veh.serialize()
        new_veh = get_vehicle_dict(provider_code, accident_year)
        obj["engine_volume"] = new_veh["engine_volume"].get(obj["engine_volume"]) if new_veh["engine_volume"] else None
        obj["total_weight"] = new_veh["total_weight"].get(obj["total_weight"]) if new_veh["total_weight"] else None
        obj["driving_directions"] = new_veh["driving_directions"].get(obj["driving_directions"]) if new_veh[
            "driving_directions"] else None

        list_to_return.append(obj)
    return make_response(json.dumps(list_to_return, ensure_ascii=False))


@app.route("/discussion", methods=["GET", "POST"])
@user_optional
def discussion():
    if request.method == "GET":
        identifier = request.values['identifier']
        context = {'identifier': identifier, 'title': identifier,
                   'url': request.base_url, 'index_url': request.url_root}
        lat, lon = request.values.get('lat'), request.values.get('lon')
        if lat is not None and lon is not None:  # create new discussion
            context.update({'new': True, 'latitude': lat, 'longitude': lon})
        else:  # show existing discussion
            try:
                marker = db.session.query(DiscussionMarker) \
                    .filter(DiscussionMarker.identifier == \
                            identifier).first()
                context['title'] = marker.title
            except AttributeError:
                return index(message=gettext(u'Discussion not found:') + request.values['identifier'])
            except KeyError:
                return index(message=gettext(u'Illegal Discussion'))
        return render_template('disqus.html', **context)
    else:
        marker = parse_data(DiscussionMarker, get_json_object(request))
        if marker is None:
            log_bad_request(request)
            return make_response("")
        logging.debug("Created new discussion with id=%d" % marker.id)
        return make_response(post_handler(marker))


@app.route("/clusters", methods=["GET"])
def clusters():
    # start_time = time.time()
    kwargs = get_kwargs()
    results = retrieve_clusters(**kwargs)

    # logging.debug('calculating clusters took %f seconds' % (time.time() - start_time))
    return Response(json.dumps({'clusters': results}), mimetype="application/json")


@app.route("/highlightpoints", methods=['POST'])
@user_optional
def highlightpoint():
    highlight = parse_data(HighlightPoint, get_json_object(request))
    if highlight is None:
        log_bad_request(request)
        return make_response("")

    # if it's a user gps type (user location), only handle a single post request per session
    if int(highlight.type) == CONST.HIGHLIGHT_TYPE_USER_GPS:
        if SESSION_HIGHLIGHTPOINT_KEY not in session:
            session[SESSION_HIGHLIGHTPOINT_KEY] = "saved"
        else:
            return make_response("")

    return make_response(post_handler(highlight))


# Post handler for a generic REST API
def post_handler(obj):
    try:
        db.session.add(obj)
        db.session.commit()
        return jsonify(obj.serialize())
    except Exception as e:
        logging.debug("could not handle a post for object:{0}, error:{1}".format(obj, e))
        return ""


# Safely parsing an object
# cls: the ORM Model class that implement a parse method
def parse_data(cls, data):
    try:
        return cls.parse(data) if data is not None else None
    except Exception as e:
        logging.debug("Could not parse the requested data, for class:{0}, data:{1}. Error:{2}".format(cls, data, e))
        return


def get_json_object(request):
    try:
        return request.get_json(force=True)
    except Exception as e:
        logging.debug("Could not get json from a request. request:{0}. Error:{1}".format(request, e))
        return


def log_bad_request(request):
    try:
        logging.debug(
            "Bad {0} Request over {1}. Values: {2} {3}".format(request.method, request.url, request.form, request.args))
    except AttributeError:
        logging.debug("Bad request:{0}".format(str(request)))


@app.route('/')
def index(marker=None, message=None):
    context = {'url': request.base_url, 'index_url': request.url_root}
    context['CONST'] = CONST.to_dict()
    # logging.debug("Debug CONST:{0}",context['CONST'])
    if 'marker' in request.values:
        markers = AccidentMarker.get_marker(request.values['marker'])
        if markers.count() == 1:
            marker = markers[0]
            context['coordinates'] = (marker.latitude, marker.longitude)
            context['marker'] = marker.id
        else:
            message = u"תאונה לא נמצאה: " + request.values['marker']
    elif 'discussion' in request.values:
        discussions = DiscussionMarker.get_by_identifier(request.values['discussion'])
        if discussions.count() == 1:
            marker = discussions[0]
            context['coordinates'] = (marker.latitude, marker.longitude)
            context['discussion'] = marker.identifier
        else:
            message = gettext(u"Discussion not found:") + request.values['discussion']
    if 'start_date' in request.values:
        context['start_date'] = string2timestamp(request.values['start_date'])
    elif marker:
        context['start_date'] = year2timestamp(marker.created.year)
    if 'end_date' in request.values:
        context['end_date'] = string2timestamp(request.values['end_date'])
    elif marker:
        context['end_date'] = year2timestamp(marker.created.year + 1)
    for attr in 'show_inaccurate', 'zoom':
        if attr in request.values:
            context[attr] = request.values[attr]
    if 'map_only' in request.values:
        if request.values['map_only'] in ('1', 'true'):
            context['map_only'] = 1
    if 'lat' in request.values and 'lon' in request.values:
        context['coordinates'] = (request.values['lat'], request.values['lon'])
    for attr in 'approx', 'accurate', 'show_markers', 'show_accidents', 'show_rsa', 'show_discussions', 'show_urban', 'show_intersection', 'show_lane', \
                'show_day', 'show_holiday', 'show_time', 'start_time', 'end_time', 'weather', 'road', 'separation', \
                'surface', 'acctype', 'controlmeasure', 'district', 'case_type', 'show_fatal', 'show_severe', 'show_light', 'age_groups':
        value = request.values.get(attr)
        if value is not None:
            context[attr] = value or '-1'
    if message:
        context['message'] = message
    pref_accident_severity = []
    pref_light = PreferenceObject('prefLight', '2', u"קלה")
    pref_severe = PreferenceObject('prefSevere', '1', u"חמורה")
    pref_fatal = PreferenceObject('prefFatal', '0', u"קטלנית")
    pref_accident_severity.extend([pref_light, pref_severe, pref_fatal])
    context['pref_accident_severity'] = pref_accident_severity
    pref_accident_report_severity = []
    pref_report_light = PreferenceObject('prefReportLight', '2', u"קלה")
    pref_report_severe = PreferenceObject('prefReportSevere', '1', u"חמורה")
    pref_report_fatal = PreferenceObject('prefReportFatal', '0', u"קטלנית")
    pref_accident_report_severity.extend([pref_report_light, pref_report_severe, pref_report_fatal])
    context['pref_accident_report_severity'] = pref_accident_report_severity
    pref_historical_report_periods = []
    month_strings = [u"אחד", u"שניים", u"שלושה", u"ארבעה", u"חמישה", u"שישה", u"שבעה", u"שמונה", u"תשעה", \
                     u"עשרה", u"אחד עשר", u"שניים עשר"]
    for x in range(0, 12):
        pref_historical_report_periods.append(
            PreferenceObject('prefHistoricalReport' + str(x + 1) + 'Month', str(x + 1), month_strings[x]))
    context['pref_historical_report_periods'] = pref_historical_report_periods
    pref_radius = []
    for x in range(1, 5):
        pref_radius.append(PreferenceObject('prefRadius' + str(x * 500), x * 500, x * 500))
    context['pref_radius'] = pref_radius
    today = datetime.date.today()
    context['default_end_date_format'] = request.values.get('end_date', today.strftime('%Y-%m-%d'))
    context['default_start_date_format'] = request.values.get('start_date',
                                                              (today - datetime.timedelta(days=365)).strftime(
                                                                  '%Y-%m-%d'))
    context['entries_per_page'] = ENTRIES_PER_PAGE
    context['iteritems'] = iteritems
    context['hide_search'] = True if request.values.get('hide_search') == 'true' else False
    return render_template('index.html', **context)


def string2timestamp(s):
    return time.mktime(datetime.datetime.strptime(s, "%Y-%m-%d").timetuple())


def year2timestamp(y):
    return time.mktime(datetime.date(y, 1, 1).timetuple())


@app.route("/location-subscription", methods=["POST", "OPTIONS"])
def updatebyemail():
    jsonData = request.get_json(force=True)
    logging.debug(jsonData)
    emailaddress = str(jsonData['address'])
    fname = (jsonData['fname']).encode("utf8")
    lname = (jsonData['lname']).encode("utf8")
    if len(fname) > 40:
        response = Response(json.dumps({'respo': 'First name too long'}, default=str), mimetype="application/json")
        response.headers.add('Access-Control-Allow-Methods', ['POST', 'OPTIONS'])
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', ['Content-Type', 'Authorization'])
        return response
    if len(lname) > 40:
        response = Response(json.dumps({'respo': 'Last name too long'}, default=str), mimetype="application/json")
        response.headers.add('Access-Control-Allow-Methods', ['POST', 'OPTIONS'])
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', ['Content-Type', 'Authorization'])
        return response
    if len(emailaddress) > 60:
        response = Response(json.dumps({'respo': 'Email too long'}, default=str), mimetype="application/json")
        response.headers.add('Access-Control-Allow-Methods', ['POST', 'OPTIONS'])
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', ['Content-Type', 'Authorization'])
        return response

    curr_max_id = db.session.query(func.max(LocationSubscribers.id)).scalar()
    if curr_max_id is None:
        curr_max_id = 0
    user_id = curr_max_id + 1
    if 'school_id' in jsonData.keys():
        school_id = int(jsonData['school_id'])
        user_subscription = LocationSubscribers(id=user_id,
                                                email=emailaddress,
                                                first_name=fname.decode("utf8"),
                                                last_name=lname.decode("utf8"),
                                                ne_lng=None,
                                                ne_lat=None,
                                                sw_lng=None,
                                                sw_lat=None,
                                                school_id=school_id)
    else:
        user_subscription = LocationSubscribers(id=user_id,
                                                email=emailaddress,
                                                first_name=fname.decode("utf8"),
                                                last_name=lname.decode("utf8"),
                                                ne_lng=jsonData['ne_lng'],
                                                ne_lat=jsonData['ne_lat'],
                                                sw_lng=jsonData['sw_lng'],
                                                sw_lat=jsonData['sw_lat'],
                                                school_id=None)
    db.session.add(user_subscription)
    db.session.commit()
    response = Response(json.dumps({'respo': 'Subscription saved'}, default=str), mimetype="application/json")
    response.headers.add('Access-Control-Allow-Methods', ['POST', 'OPTIONS'])
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', ['Content-Type', 'Authorization'])
    return response


@app.route("/report-problem", methods=["POST"])
def report_problem():
    jsonData = request.get_json(force=True)
    logging.debug(jsonData)
    first_name = (jsonData['first_name']).encode("utf8")
    last_name = (jsonData['last_name']).encode("utf8")
    report_problem = ReportProblem(latitude=jsonData['latitude'],
                                   longitude=jsonData['longitude'],
                                   problem_description=jsonData['problem_description'],
                                   signs_on_the_road_not_clear=jsonData['signs_on_the_road_not_clear'],
                                   signs_problem=jsonData['signs_problem'],
                                   pothole=jsonData['pothole'],
                                   no_light=jsonData['no_light'],
                                   no_sign=jsonData['no_sign'],
                                   crossing_missing=jsonData['crossing_missing'],
                                   sidewalk_is_blocked=jsonData['sidewalk_is_blocked'],
                                   street_light_issue=jsonData['street_light_issue'],
                                   road_hazard=jsonData['road_hazard'],
                                   first_name=first_name.decode("utf8"),
                                   last_name=last_name.decode("utf8"),
                                   phone_number=jsonData['phone_number'],
                                   email=str(jsonData['email']),
                                   send_to_municipality=jsonData['send_to_municipality'],
                                   personal_id=jsonData['personal_id'],
                                   image_data=jsonData['image_data'])
    db.session.add(report_problem)
    db.session.commit()
    response = Response(json.dumps({'respo': 'Subscription saved'}, default=str), mimetype="application/json")
    response.headers.add('Access-Control-Allow-Methods', ['POST', 'OPTIONS'])
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', ['Content-Type', 'Authorization'])
    return response


@app.route("/preferences", methods=('GET', 'POST'))
def update_preferences():
    if not current_user.is_authenticated:
        return jsonify(respo='user not authenticated')
    cur_id = current_user.get_id()
    cur_user = db.session.query(User).filter(User.id == cur_id).first()
    if cur_user is None:
        return jsonify(respo='user not found')
    cur_report_preferences = db.session.query(ReportPreferences).filter(User.id == cur_id).first()
    cur_general_preferences = db.session.query(GeneralPreferences).filter(User.id == cur_id).first()
    if request.method == "GET":
        if cur_report_preferences is None and cur_general_preferences is None:
            return jsonify(accident_severity='0', pref_accidents_cbs=True, pref_accidents_ihud=True,
                           produce_accidents_report=False)
        else:
            resource_types = cur_general_preferences.resource_type.split(',')
            if cur_report_preferences is None:
                return jsonify(accident_severity=cur_general_preferences.minimum_displayed_severity,
                               pref_resource_types=resource_types, produce_accidents_report=False)
            else:
                return jsonify(accident_severity=cur_general_preferences.minimum_displayed_severity,
                               pref_resource_types=resource_types, produce_accidents_report=True, \
                               lat=cur_report_preferences.latitude, lon=cur_report_preferences.longitude,
                               pref_radius=cur_report_preferences.radius, \
                               pref_accident_severity_for_report=cur_report_preferences.minimum_severity,
                               how_many_months_back=cur_report_preferences.how_many_months_back)
    else:
        json_data = request.get_json(force=True)
        accident_severity = json_data['accident_severity']
        resources = json_data['pref_resource_types']
        produce_accidents_report = json_data['produce_accidents_report']
        lat = json_data['lat']
        lon = json_data['lon']
        pref_radius = json_data['pref_radius']
        pref_accident_severity_for_report = json_data['pref_accident_severity_for_report']
        history_report = json_data['history_report']
        is_history_report = (history_report != '0')
        resource_types = ','.join(resources)
        cur_general_preferences = db.session.query(GeneralPreferences).filter(User.id == cur_id).first()
        if cur_general_preferences is None:
            general_pref = GeneralPreferences(user_id=cur_id, minimum_displayed_severity=accident_severity,
                                              resource_type=resource_types)
            db.session.add(general_pref)
            db.session.commit()
        else:
            cur_general_preferences.minimum_displayed_severity = accident_severity
            cur_general_preferences.resource_type = resource_types
            db.session.add(cur_general_preferences)
            db.session.commit()

        if produce_accidents_report:
            if lat == '':
                lat = None
            if lon == '':
                lon = None
            if cur_report_preferences is None:
                report_pref = ReportPreferences(user_id=cur_id, line_number=1, historical_report=is_history_report, \
                                                how_many_months_back=history_report, latitude=lat, longitude=lon, \
                                                radius=pref_radius, minimum_severity=pref_accident_severity_for_report)
                db.session.add(report_pref)
                db.session.commit()
            else:
                cur_report_preferences.historical_report = is_history_report
                cur_report_preferences.latitude = lat
                cur_report_preferences.longitude = lon
                cur_report_preferences.radius = pref_radius
                cur_report_preferences.minimum_severity = pref_accident_severity_for_report
                cur_report_preferences.how_many_months_back = history_report
                db.session.add(cur_report_preferences)
                db.session.commit()
        else:
            if cur_report_preferences is not None:
                db.session.delete(cur_report_preferences)
                db.session.commit()
        return jsonify(respo='ok', )


class PreferenceObject:
    def __init__(self, id, value, string):
        self.id = id
        self.value = value
        self.string = string


class HistoricalReportPeriods:
    def __init__(self, period_id, period_value, severity_string):
        self.period_id = period_id
        self.period_value = period_value
        self.severity_string = severity_string


class LoginFormAdmin(form.Form):
    username = fields.StringField(validators=[validators.required()])
    password = fields.PasswordField(validators=[validators.required()])

    def validate_login(self, field):
        user = self.get_user()

        if user is None:
            raise validators.ValidationError('Invalid user')

        if not check_password_hash(user.password.encode("utf8"), self.password.data.encode("utf8")):
            raise validators.ValidationError('Invalid password')

    def get_user(self):
        return db.session.query(User).filter_by(username=self.username.data).first()


class RegistrationForm(form.Form):
    username = fields.StringField(validators=[validators.required()])
    email = fields.StringField()
    password = fields.PasswordField(validators=[validators.required()])

    def validate_login(self, field):
        if db.session.query(User).filter_by(username=self.username.data).count() > 0:
            raise validators.ValidationError('Duplicate username')


def init_login():
    login_manager = login.LoginManager()
    login_manager.init_app(app)

    # Create user loader function
    @login_manager.user_loader
    def load_user(user_id):  # pylint: disable=unused-variable
        return db.session.query(User).get(user_id)


class AdminView(sqla.ModelView):

    def is_accessible(self):
        return login.current_user.is_authenticated


class AdminIndexView(admin.AdminIndexView):

    @expose('/')
    def index(self):
        if login.current_user.is_authenticated:
            if current_user.has_role('admin'):
                return super(AdminIndexView, self).index()
            else:
                return make_response("Unauthorized User")
        else:
            return redirect(url_for('.login_view'))

    @expose('/login/', methods=('GET', 'POST'))
    def login_view(self):
        # handle user login
        form = LoginFormAdmin(request.form)
        if helpers.validate_form_on_submit(form):
            user = form.get_user()
            login.login_user(user)

        if login.current_user.is_authenticated:
            return redirect(url_for('.index'))
        # link = '<p>Don\'t have an account? <a href="' + url_for('.register_view') + '">Click here to register.</a></p>'
        self._template_args['form'] = form
        # self._template_args['link'] = link
        return super(AdminIndexView, self).index()

    # @expose('/register/', methods=('GET', 'POST'))
    # def register_view(self):
    #    form = RegistrationForm(request.form)
    #    if helpers.validate_form_on_submit(form):
    #        user = User()
    #        admin_role = db.session.query(Role).filter_by(name='admin').first()
    #        form.populate_obj(user)
    #        # we hash the users password to avoid saving it as plaintext in the db,
    #        # remove to use plain text:
    #        user.password = generate_password_hash(form.password.data)
    #        user.is_admin = True
    #        user.nickname = user.username
    #        user.roles.append(admin_role) #adding admin role
    #
    #        db.session.add(user)
    #        db.session.commit()
    #
    #        login.login_user(user)
    #        return redirect(url_for('.index'))
    #    link = '<p>Already have an account? <a href="' + url_for('.login_view') + '">Click here to log in.</a></p>'
    #    self._template_args['form'] = form
    #    self._template_args['link'] = link
    #    return super(AdminIndexView, self).index()

    @expose('/logout/')
    def logout_view(self):
        login.logout_user()
        return redirect(url_for('.index'))


class SendToSubscribersView(BaseView):
    @roles_required('admin')
    @expose('/', methods=('GET', 'POST'))
    def index(self):
        if request.method == 'GET':
            user_emails = db.session.query(User).filter(User.new_features_subscription == True)
            email_list = []
            for user in user_emails:
                email_list.append(user.email)
                email_list.append(';')
            context = {'user_emails': email_list}
            return self.render('sendemail.html', **context)
        else:
            jsondata = request.get_json(force=True)
            users_send_email_to = db.session.query(User).filter(User.new_features_subscription == True)
            message = Mail(subject=jsondata['subject'].encode("utf8"),
                           html_content=jsondata['message'].encode("utf8"),
                           from_email='ANYWAY Team <feedback@anyway.co.il>')
            for user in users_send_email_to:
                message.add_bcc(user.email)
            # try:
            # sg.send(message)
            # except Exception as _:
            #    return "Error occurred while trying to send the emails"
            return "Email/s was not Sent"

    def is_visible(self):
        return login.current_user.is_authenticated


class ViewHighlightedMarkersData(BaseView):
    @roles_required('admin')
    @expose('/')
    def index(self):
        highlightedpoints = db.session.query(HighlightPoint).options(load_only("id", "latitude", "longitude", "type"))
        points = []
        for point in highlightedpoints:
            p = HighlightPoint()
            p.id = point.id
            p.latitude = point.latitude
            p.longitude = point.longitude
            p.created = point.created
            p.type = point.type
            points.append(p)
        context = {'points': points}
        return self.render('viewhighlighteddata.html', **context)

    def is_visible(self):
        return login.current_user.is_authenticated


class ViewHighlightedMarkersMap(BaseView):
    @roles_required('admin')
    @expose('/')
    def index1(self):
        return index(marker=None, message=None)

    def is_visible(self):
        return login.current_user.is_authenticated


class OpenAccountForm(Form):
    username = StringField('Username', validators=[validators.DataRequired()])
    password = PasswordField('Password', validators=[validators.DataRequired()])

    def validate_on_submit(self):
        if self.username.data == '':
            return False

        if self.password.data == '':
            return False
        return True


class OpenNewOrgAccount(BaseView):
    @roles_required('admin')
    @expose('/', methods=('GET', 'POST'))
    def index(self):
        formAccount = OpenAccountForm(request.form)
        if request.method == "POST" and formAccount.validate_on_submit():
            user = User(username=formAccount.username.data, password=formAccount.password.data)
            role = db.session.query(Role).filter(Role.id == 2).first()
            user.roles.append(role)
            db.session.add(user)
            db.session.commit()
            flash('The user was created successfully')
        return self.render('open_account.html', form=formAccount)

    def is_visible(self):
        return login.current_user.is_authenticated


init_login()

admin = admin.Admin(app, 'ANYWAY Administration Panel', index_view=AdminIndexView(), base_template='admin_master.html')

admin.add_view(AdminView(User, db.session, name='Users', endpoint='Users', category='Users'))
admin.add_view(AdminView(Role, db.session, name='Roles', endpoint='Roles'))
admin.add_view(OpenNewOrgAccount(name='Open new organization account', endpoint='OpenAccount', category='Users'))
admin.add_view(SendToSubscribersView(name='Send To Subscribers'))
admin.add_view(ViewHighlightedMarkersData(name='View Highlighted Markers Data', endpoint='ViewHighlightedMarkersData',
                                          category='View Highlighted Markers'))
admin.add_view(ViewHighlightedMarkersMap(name='View Highlighted Markers Map', endpoint='ViewHighlightedMarkersMap',
                                         category='View Highlighted Markers'))



@app.route("/markers/polygon/", methods=["GET"])
def acc_in_area_query():
    # polygon will be received in the following format: 'POLYGON(({lon} {lat},{lon} {lat},........,{lonN},
    # {latN}))' please note that start point and end point must be equal: i.e. lon=lonN, lat=latN
    # Request format: http://{server url}/markers/polygon?polygon=POLYGON(({lon} {lat},{lon} {lat},........,{lonN},
    # {latN}))"

    pol_str = request.values.get('polygon')
    if pol_str is None:
        msg = "polygon parameter is mandatory and must be sent as part of the request - http://{host:port}/markers/polygon?polygon=POLYGON(({lon} {" \
              "lat},{lon} {lat},........,{lonN},{latN}))"
        raise abort(Response(msg))

    query_obj = db.session.query(AccidentMarker) \
        .filter(AccidentMarker.geom.intersects(pol_str)) \
        .filter(or_((AccidentMarker.provider_code == CONST.CBS_ACCIDENT_TYPE_1_CODE),
                    (AccidentMarker.provider_code == CONST.CBS_ACCIDENT_TYPE_3_CODE)))

    df = pd.read_sql_query(query_obj.with_labels().statement, query_obj.session.bind)
    markers_in_area_list = df.to_dict(orient='records')
    response = Response(json.dumps(markers_in_area_list, default=str), mimetype="application/json")
    return response


class ExtendedLoginForm(LoginForm):
    username = StringField('User Name', [validators.DataRequired()])

    def validate(self):
        if not super(ExtendedLoginForm, self).validate():
            return False
        if self.username.data.strip() == '':
            return False
        self.user = db.session.query(User).filter(User.username == self.username.data).first()
        if self.user is None:
            return False
        if self.password.data == self.user.password:
            return True
        return False


user_datastore = SQLAlchemyUserDatastore(SQLAlchemy(app), User, Role)
security = Security(app, user_datastore, login_form=ExtendedLoginForm)
lm = login.LoginManager(app)
lm.login_view = 'index'


@login_required
@roles_required('privileged_user')
@app.route('/testroles')
def TestLogin():
    if current_user.is_authenticated:
        if current_user.has_role('privileged_user'):
            context = {'user_name': get_current_user_first_name()}
            return render_template('testroles.html', **context)
        else:
            return make_response("Unauthorized User")
    else:
        return redirect('/login')


def get_current_user_first_name():
    cur_id = current_user.get_id()
    cur_user = db.session.query(User).filter(User.id == cur_id).first()
    if cur_user is not None:
        return cur_user.first_name
    return "User"


######## rauth integration (login through facebook) ##################

@lm.user_loader
def load_user(id):
    return db.session.query(User).get(int(id))


@app.route('/logout')
def logout():
    login.logout_user()
    return redirect(url_for('index'))


@app.route('/authorize/<provider>')
def oauth_authorize(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('index'))
    oauth = OAuthSignIn.get_provider(provider)
    return oauth.authorize()


@app.route('/callback/<provider>')
def oauth_callback(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('index'))
    oauth = OAuthSignIn.get_provider(provider)
    if provider == 'google':
        username, email = oauth.callback()
        if email is None:
            flash('Authentication failed.')
            return redirect(url_for('index'))
        user = db.session.query(User).filter_by(email=email).first()
        if not user:
            user = User(nickname=username, email=email, provider=provider)
            db.session.add(user)
            db.session.commit()
    else:  # facebook authentication
        social_id, username, email = oauth.callback()
        if social_id is None:
            flash('Authentication failed.')
            return redirect(url_for('index'))
        user = db.session.query(User).filter_by(social_id=social_id).first()
        if not user:
            curr_max_id = db.session.query(func.max(User.id)).scalar()
            if curr_max_id is None:
                curr_max_id = 0
            user_id = curr_max_id + 1
            user = User(id=user_id, social_id=social_id, nickname=username, email=email, provider=provider)
            db.session.add(user)
            db.session.commit()
    login.login_user(user, True)
    return redirect(url_for('index'))

def extract_news_flash_location(news_flash_id):
    news_flash_obj = db.session.query(NewsFlash).filter(NewsFlash.id==news_flash_id).first()
    if not news_flash_obj:
        logging.warn('could not find news flash id {}'.format(news_flash_id))
        return None
    resolution = news_flash_obj.resolution if news_flash_obj.resolution else None
    if not news_flash_obj or not resolution or resolution not in resolution_dict:
        logging.warn('could not find valid resolution for news flash id {}'.format(news_flash_id))
        return {'name': 'location', 'data': {'resolution': None}}
    data = {'resolution': resolution}
    for field in resolution_dict[resolution]:
        data[field] = getattr(news_flash_obj, field)
    return {'name': 'location', 'data': data}

def get_query(table_obj, filters, start_time, end_time):
    query = db.session.query(table_obj)
    if start_time:
        query = query.filter(getattr(table_obj,'accident_timestamp') >= start_time)
    if end_time:
        query = query.filter(getattr(table_obj,'accident_timestamp') <= end_time)
    if filters:
        for field_name, value in filters.items():
            if isinstance(value, list):
                values = value
            else:
                values = [value]
            query = query.filter((getattr(table_obj,field_name)).in_(values))
    return query


def get_accidents_stats(table_obj, filters=None, group_by=None, count=None, start_time=None, end_time=None):
    filters = filters or {}
    filters['provider_code'] = [CONST.CBS_ACCIDENT_TYPE_1_CODE, CONST.CBS_ACCIDENT_TYPE_3_CODE]
    # get stats
    query = get_query(table_obj, filters, start_time, end_time)
    if group_by:
        query = query.group_by(group_by)
        query = query.with_entities(group_by, func.count(count))
    df = pd.read_sql_query(query.statement, query.session.bind)
    df.rename(columns={'count_1': 'count'}, inplace=True)
    df.columns = [c.replace('_hebrew', '') for c in df.columns]
    return df.to_dict(orient='records') if group_by or count else df.to_dict()

def get_injured_filters(location_info):
    new_filters = {}
    for curr_filter, curr_values in location_info.items():
        if curr_filter in ['region_hebrew', 'district_hebrew', 'district_hebrew', 'yishuv_name']:
            new_filter_name = 'accident_' + curr_filter
            new_filters[new_filter_name] = curr_values
        else:
            new_filters[curr_filter] = curr_values
    new_filters['injury_severity'] = [1,2,3,4,5]
    return new_filters


def get_most_severe_accidents(table_obj, filters, start_time, end_time, limit=10):
    filters = filters or {}
    filters['provider_code'] = [CONST.CBS_ACCIDENT_TYPE_1_CODE, CONST.CBS_ACCIDENT_TYPE_3_CODE]
    query = get_query(table_obj, filters, start_time, end_time)
    query = query.with_entities('longitude', 'latitude', 'accident_severity_hebrew', 'accident_timestamp',
                                'accident_type_hebrew')
    query = query.order_by(getattr(table_obj,"accident_severity"), getattr(table_obj,"accident_timestamp").desc())
    query = query.limit(limit)
    df = pd.read_sql_query(query.statement, query.session.bind)
    df.columns = [c.replace('_hebrew', '') for c in df.columns]
    return df.to_dict(orient='records')


def get_accidents_heat_map(table_obj, filters, start_time, end_time):
    filters = filters or {}
    filters['provider_code'] = [CONST.CBS_ACCIDENT_TYPE_1_CODE, CONST.CBS_ACCIDENT_TYPE_3_CODE]
    query = get_query(table_obj, filters, start_time, end_time)
    query = query.with_entities('longitude', 'latitude')
    df = pd.read_sql_query(query.statement, query.session.bind)
    return df.to_dict(orient='records')


@app.route('/api/infographics_data', methods=['GET'])
def infographics_data():

    output = {}

    location_info = extract_news_flash_location(request.values.get('news_flash_id'))
    if location_info is None:
        return Response({})
    location_info = location_info['data']
    output['meta'] = {"location_info": location_info.copy()}
    output['widgets'] = []
    resolution    = location_info.pop('resolution')
    if resolution is None:
        return Response({})

    if all(value is None for value in location_info.values()):
        return Response({})

    number_of_years_ago_to_pull_raw = request.values.get('years_ago', CONST.DEFAULT_NUMBER_OF_YEARS_AGO)
    try:
        number_of_years_ago_to_pull = int(number_of_years_ago_to_pull_raw)
    except ValueError:
        return Response({})

    if number_of_years_ago_to_pull < 0 or number_of_years_ago_to_pull > 100:
        return Response({})

    end_time = datetime.date.today()
    start_time = datetime.date(end_time.year - number_of_years_ago_to_pull, 1, 1)

    # most severe accidents
    most_severe_accidents = {'name': 'most_severe_accidents',
                            'data': get_most_severe_accidents(table_obj=AccidentMarkerView, filters=location_info, start_time=start_time, end_time=end_time),
                            'meta': {}}
    output['widgets'].append(most_severe_accidents)
    # accident_severity count
    accident_count_by_severity = {'name': 'accident_count_by_severity',
                                  'data': get_accidents_stats(table_obj=AccidentMarkerView, filters=location_info, group_by='accident_severity_hebrew', count='accident_severity_hebrew', start_time=start_time, end_time=end_time),
                                  'meta': {}}
    output['widgets'].append(accident_count_by_severity)

    # accident_type count
    accident_count_by_accident_type = {'name': 'accident_count_by_accident_type',
                                      'data': get_accidents_stats(table_obj=AccidentMarkerView, filters=location_info, group_by='accident_type_hebrew', count='accident_type_hebrew', start_time=start_time, end_time=end_time),
                                       'meta': {}}
    output['widgets'].append(accident_count_by_accident_type)

    # accident count by accident year
    accident_count_by_accident_year = {'name': 'accident_count_by_accident_year',
                                       'data': get_accidents_stats(table_obj=AccidentMarkerView, filters=location_info, group_by='accident_year', count='accident_year', start_time=start_time, end_time=end_time),
                                       'meta': {}}
    output['widgets'].append(accident_count_by_accident_year)

    # accidents heat map
    accidents_heat_map = {'name': 'accidents_heat_map',
                          'data': get_accidents_heat_map(table_obj=AccidentMarkerView,
                                                         filters=location_info,
                                                         start_time=start_time,
                                                         end_time=end_time),
                          'meta': {}}
    output['widgets'].append(accidents_heat_map)

    # injured count by accident year
    injured_count_by_accident_year = {'name': 'injured_count_by_accident_year',
                                       'data': get_accidents_stats(table_obj=InvolvedMarkerView, filters=get_injured_filters(location_info), group_by='accident_year', count='accident_year', start_time=start_time, end_time=end_time),
                                       'meta': {}}
    output['widgets'].append(injured_count_by_accident_year)

    # accident count on day light
    accident_count_by_day_night = {'name': 'accident_count_by_day_night',
                                   'data' : get_accidents_stats(table_obj=AccidentMarkerView, filters=location_info, group_by='day_night_hebrew', count='day_night_hebrew', start_time=start_time, end_time=end_time),
                                    'meta': {}}
    output['widgets'].append(accident_count_by_day_night)

    # accidents distribution count by hour
    accidents_count_by_hour = {'name': 'accidents_count_by_hour',
                                            'data': get_accidents_stats(table_obj=AccidentMarkerView, filters=location_info, group_by='accident_hour', count='accident_hour', start_time=start_time, end_time=end_time),
                                            'meta': {}}
    output['widgets'].append(accidents_count_by_hour)

    # accident count by road_light
    accident_count_by_road_light = {'name': 'accident_count_by_road_light',
                                   'data' : get_accidents_stats(table_obj=AccidentMarkerView, filters=location_info, group_by='road_light_hebrew', count='road_light_hebrew', start_time=start_time, end_time=end_time),
                                    'meta': {}}
    output['widgets'].append(accident_count_by_road_light)

    return Response(json.dumps(output, default=str), mimetype="application/json")

@app.route("/api/embedded-reports", methods=["GET"])
@user_optional
def embedded_reports_api():
    logging.debug('getting embedded reports')
    embedded_reports = db.session.query(EmbeddedReports).all()
    embedded_reports_list = [{"id": x.id,
                              "report_name_english": x.report_name_english,
                              "report_name_hebrew": x.report_name_hebrew,
                              "url": x.url} for x in embedded_reports]
    response = Response(json.dumps(embedded_reports_list, default=str), mimetype="application/json")
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response
