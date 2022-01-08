# -*- coding: utf-8 -*-
# pylint: disable=no-member
import base64
import csv
import datetime
import json
import logging
import re
import typing
from functools import wraps
from io import StringIO
import os
import time


from flask_login import login_user, logout_user, LoginManager, current_user
import jinja2
import pandas as pd
from flask import make_response, render_template, Response, jsonify, abort, current_app, g, Request
from flask import request, redirect, session
from flask_assets import Environment
from flask_babel import Babel, gettext
from flask_compress import Compress
from flask_cors import CORS
from flask_principal import (
    Principal,
    identity_changed,
    Identity,
    AnonymousIdentity,
    identity_loaded,
    UserNeed,
    RoleNeed,
    Permission,
)
from flask_restx import Resource, fields, reqparse

from anyway.error_code_and_strings import (
    Errors as Es,
    build_json_for_user_api_error,
    ERROR_TO_HTTP_CODE_DICT,
)

from http import client as http_client, HTTPStatus
from sqlalchemy import and_, not_, or_
from sqlalchemy import func
from webassets import Environment as AssetsEnvironment, Bundle as AssetsBundle
from webassets.ext.jinja2 import AssetsExtension
from werkzeug.exceptions import BadRequestKeyError

from anyway import utilities, secrets
from anyway.base import _set_cookie_hijack, _clear_cookie_hijack
from anyway.clusters_calculator import retrieve_clusters
from anyway.config import ENTRIES_PER_PAGE
from anyway.backend_constants import BE_CONST
from anyway.constants import CONST
from anyway.user_functions import (
    get_current_user_email,
    get_current_user,
    get_user_by_email,
)
from anyway.models import (
    AccidentMarker,
    DiscussionMarker,
    HighlightPoint,
    Involved,
    LocationSubscribers,
    Vehicle,
    ReportProblem,
    EngineVolume,
    PopulationType,
    Region,
    District,
    NaturalArea,
    MunicipalStatus,
    YishuvShape,
    TotalWeight,
    DrivingDirections,
    AgeGroup,
    AccidentMarkerView,
    EmbeddedReports,
    Users,
    Roles,
    users_to_roles,
)
from anyway.oauth import OAuthSignIn
from anyway.infographics_utils import (
    get_infographics_data,
    get_infographics_mock_data,
    get_infographics_data_for_road_segment,
)
from anyway.app_and_db import app, db, api, get_cors_config
from anyway.anyway_dataclasses.user_data import UserData
from anyway.utilities import (
    is_valid_number,
    is_a_safe_redirect_url,
    is_a_valid_email,
)
from anyway.views.schools.api import (
    schools_description_api,
    schools_names_api,
    schools_yishuvs_api,
    schools_api,
    injured_around_schools_sex_graphs_data_api,
    injured_around_schools_months_graphs_data_api,
    injured_around_schools_api,
)
from anyway.views.news_flash.api import (
    news_flash,
    news_flash_new,
    single_news_flash,
    news_flash_v2,
    DEFAULT_LIMIT_REQ_PARAMETER,
    DEFAULT_OFFSET_REQ_PARAMETER,
)

DEFAULT_MAPS_API_KEY = "AIzaSyDUIWsBLkvIUwzLHMHos9qFebyJ63hEG2M"


app.config.from_object(__name__)
app.config["SESSION_COOKIE_SAMESITE"] = "none"
app.config["SESSION_COOKIE_SECURE"] = True
app.config["REMEMBER_COOKIE_SECURE"] = True
app.config["BABEL_DEFAULT_LOCALE"] = "he"
app.config["OAUTH_CREDENTIALS"] = {
    "facebook": {"id": secrets.get("FACEBOOK_KEY"), "secret": secrets.get("FACEBOOK_SECRET")},
    "google": {
        "id": secrets.get("GOOGLE_LOGIN_CLIENT_ID"),
        "secret": secrets.get("GOOGLE_LOGIN_CLIENT_SECRET"),
    },
}
app.secret_key = secrets.get("APP_SECRET_KEY")
assets = Environment()
assets.init_app(app)
assets_env = AssetsEnvironment(os.path.join(utilities._PROJECT_ROOT, "static"), "/static")
assets.register(
    "css_all",
    AssetsBundle(
        "css/jquery.smartbanner.css",
        "css/bootstrap.rtl.css",
        "css/style.css",
        "css/daterangepicker.css",
        "css/accordion.css",
        "css/bootstrap-tour.min.css",
        "css/jquery-ui.min.css",
        "css/jquery.jspanel.min.css",
        "css/markers.css",
        filters="rcssmin",
        output="css/app.min.css",
    ),
)
assets.register(
    "js_all",
    AssetsBundle(
        "js/libs/jquery-1.11.3.min.js",
        "js/libs/spin.js",
        "js/libs/oms.min.js",
        "js/libs/markerclusterer.js",
        "js/markerClustererAugment.js",
        "js/libs/underscore.js",
        "js/libs/backbone.js",
        "js/libs/backbone.paginator.min.js",
        "js/libs/bootstrap.js",
        "js/libs/notify-combined.min.js",
        "js/libs/moment-with-langs.min.js",
        "js/libs/date.js",
        "js/libs/daterangepicker.js",
        "js/libs/js-itm.js",
        "js/constants.js",
        "js/marker.js",
        "js/clusterView.js",
        "js/featuredialog.js",
        "js/subscriptiondialog.js",
        "js/preferencesdialog.js",
        "js/logindialog.js",
        "js/sidebar.js",
        "js/contextmenu.js",
        "js/map_style.js",
        "js/clipboard.js",
        "js/libs/bootstrap-tour.min.js",
        "js/app.js",
        "js/localization.js",
        "js/inv_dict.js",
        "js/veh_dict.js",
        "js/retina.js",
        "js/statPanel.js",
        "js/reports.js",
        filters="rjsmin",
        output="js/app.min.js",
    ),
)
assets.register(
    "email_all",
    AssetsBundle(
        "js/libs/jquery-1.11.3.min.js",
        "js/libs/notify-combined.min.js",
        filters="rjsmin",
        output="js/app_send_email.min.js",
    ),
)

CORS(
    app,
    resources=get_cors_config(),
)

jinja_environment = jinja2.Environment(
    autoescape=True,
    loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), "../templates")),
    extensions=[AssetsExtension],
)
jinja_environment.assets_environment = assets_env

babel = Babel(app)

SESSION_HIGHLIGHTPOINT_KEY = "gps_highlightpoint_created"

DICTIONARY = "Dictionary"
DICTCOLUMN1 = "MS_TAVLA"
DICTCOLUMN2 = "KOD"
DICTCOLUMN3 = "TEUR"
cbs_dict_files = {DICTIONARY: "Dictionary.csv"}
content_encoding = "cp1255"

Compress(app)
# Setup Flask-login
login_manager = LoginManager()
# Those 2 function hijack are a temporary fix - more info in base.py
login_manager._set_cookie = _set_cookie_hijack
login_manager._clear_cookie = _clear_cookie_hijack
login_manager.init_app(app)
# Setup Flask-Principal
principals = Principal(app)


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
    return jsonify(
        {
            "markers": entries,
            "pagination": {
                "totalRecords": total_records,
                "totalAccidents": total_accidents,
                "totalRSA": total_rsa,
            },
        }
    )


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

        row = {k: v.encode("utf8") if type(v) is str else v for k, v in serialized.items()}
        output.writerow(row)
        yield output_file.getvalue()
        output_file.truncate(0)


ARG_TYPES = {
    "ne_lat": (float, 32.072427482938345),
    "ne_lng": (float, 34.79928962966915),
    "sw_lat": (float, 34.79928962966915),
    "sw_lng": (float, 34.78877537033077),
    "zoom": (int, 17),
    "show_fatal": (bool, True),
    "show_severe": (bool, True),
    "show_light": (bool, True),
    "approx": (bool, True),
    "accurate": (bool, True),
    "show_markers": (bool, True),
    "show_accidents": (bool, True),
    "show_rsa": (bool, True),
    "show_discussions": (bool, True),
    "show_urban": (int, 3),
    "show_intersection": (int, 3),
    "show_lane": (int, 3),
    "show_day": (int, 0),
    "show_holiday": (int, 0),
    "show_time": (int, 24),
    "start_time": (int, 25),
    "end_time": (int, 25),
    "weather": (int, 0),
    "road": (int, 0),
    "separation": (int, 0),
    "surface": (int, 0),
    "acctype": (int, 0),
    "controlmeasure": (int, 0),
    "district": (int, 0),
    "case_type": (int, 0),
    "fetch_markers": (bool, True),
    "fetch_vehicles": (bool, True),
    "fetch_involved": (bool, True),
    "age_groups": (str, str(CONST.ALL_AGE_GROUPS_LIST).strip("[]").replace(" ", "")),
    "page": (int, 0),
    "per_page": (int, 0),
}


def get_kwargs():
    kwargs = {
        arg: arg_type(request.values.get(arg, default_value))
        for (arg, (arg_type, default_value)) in ARG_TYPES.items()
    }

    age_groups_arr = request.values.get("age_groups[]")
    age_groups = request.values.get("age_groups")
    if age_groups_arr == "1234" or age_groups == "1234":
        kwargs["age_groups"] = "1,2,3,4"
    if age_groups_arr == "234" or age_groups == "234":
        kwargs["age_groups"] = "2,3,4"
        kwargs["light_transportation"] = True
    try:
        kwargs.update(
            {
                arg: datetime.date.fromtimestamp(int(request.values[arg]))
                for arg in ("start_date", "end_date")
            }
        )
    except (ValueError, BadRequestKeyError):
        abort(http_client.BAD_REQUEST)
    return kwargs


@babel.localeselector
def get_locale():
    lang = request.values.get("lang")
    if lang is None:
        return request.accept_languages.best_match(app.config["LANGUAGES"].keys())
    else:
        return lang


@app.route("/schools", methods=["GET"])
def schools():
    if request.method == "GET":
        return render_template("schools_redirect.html")
    else:
        return Response("Method Not Allowed", 405)


@app.route("/markers", methods=["GET"])
def markers():
    logging.debug("getting markers")
    kwargs = get_kwargs()
    logging.debug("querying markers in bounding box: %s" % kwargs)
    is_thin = kwargs["zoom"] < CONST.MINIMAL_ZOOM
    result = AccidentMarker.bounding_box_query(
        is_thin, yield_per=50, involved_and_vehicles=False, **kwargs
    )
    accident_markers = result.accident_markers
    rsa_markers = result.rsa_markers

    discussion_args = ("ne_lat", "ne_lng", "sw_lat", "sw_lng", "show_discussions")
    discussions = DiscussionMarker.bounding_box_query(
        **{arg: kwargs[arg] for arg in discussion_args}
    )

    if request.values.get("format") == "csv":
        date_format = "%Y-%m-%d"
        return Response(
            generate_csv(accident_markers),
            headers={
                "Content-Type": "text/csv",
                "Content-Disposition": "attachment; "
                'filename="Anyway-accidents-from-{0}-to-{1}.csv"'.format(
                    kwargs["start_date"].strftime(date_format),
                    kwargs["end_date"].strftime(date_format),
                ),
            },
        )

    else:  # defaults to json
        return generate_json(
            accident_markers, rsa_markers, discussions, is_thin, total_records=result.total_records
        )


@app.route("/markers_by_yishuv_symbol", methods=["GET"])
def markers_by_yishuv_symbol():
    logging.debug("getting markers by yishuv symbol")
    yishuv_symbol = request.values.get("yishuv_symbol")
    markers = (
        db.session.query(AccidentMarker).filter(AccidentMarker.yishuv_symbol == yishuv_symbol).all()
    )
    entries = [marker.serialize(True) for marker in markers]
    return jsonify({"markers": entries})


@app.route("/markers_hebrew_by_yishuv_symbol", methods=["GET"])
def markers_hebrew_by_yishuv_symbol():
    logging.debug("getting hebrew markers by yishuv symbol")
    yishuv_symbol = request.values.get("yishuv_symbol")
    markers = (
        db.session.query(AccidentMarkerView)
        .filter(AccidentMarkerView.yishuv_symbol == yishuv_symbol)
        .all()
    )
    entries = [marker.serialize() for marker in markers]
    return Response(json.dumps(entries, default=str), mimetype="application/json")


@app.route("/yishuv_symbol_to_yishuv_name", methods=["GET"])
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
    logging.debug("getting yishuv symbol and yishuv name pairs")
    markers = (
        db.session.query(AccidentMarkerView.yishuv_name, AccidentMarkerView.yishuv_symbol)
        .filter(not_(AccidentMarkerView.yishuv_name == None))
        .group_by(AccidentMarkerView.yishuv_name, AccidentMarkerView.yishuv_symbol)
        .all()
    )
    entries = [{"yishuv_name": x.yishuv_name, "yishuv_symbol": x.yishuv_symbol} for x in markers]
    return Response(json.dumps(entries, default=str), mimetype="application/json")


@app.route("/charts-data", methods=["GET"])
def charts_data():
    logging.debug("getting charts data")
    kwargs = get_kwargs()
    accidents, vehicles, involved = AccidentMarker.bounding_box_query(
        is_thin=False, yield_per=50, involved_and_vehicles=True, **kwargs
    )
    accidents_list = [acc.serialize() for acc in accidents]
    vehicles_list = [vehicles_data_refinement(veh.serialize()) for veh in vehicles]
    involved_list = [involved_data_refinement(inv.serialize()) for inv in involved]
    return Response(
        json.dumps(
            {"accidents": accidents_list, "vehicles": vehicles_list, "involved": involved_list}
        ),
        mimetype="application/json",
    )


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
    age_group = (
        db.session.query(AgeGroup)
        .filter(and_(AgeGroup.provider_code == provider_code, AgeGroup.year == accident_year))
        .all()
    )
    involved["age_group"] = {g.id: g.age_group_hebrew for g in age_group} if age_group else None

    population_type = (
        db.session.query(PopulationType)
        .filter(
            and_(
                PopulationType.provider_code == provider_code, PopulationType.year == accident_year
            )
        )
        .all()
    )

    involved["population_type"] = (
        {g.id: g.population_type_hebrew for g in population_type} if population_type else None
    )

    home_region = (
        db.session.query(Region)
        .filter(and_(Region.provider_code == provider_code, Region.year == accident_year))
        .all()
    )

    involved["home_region"] = {g.id: g.region_hebrew for g in home_region} if home_region else None

    home_district = (
        db.session.query(District)
        .filter(and_(District.provider_code == provider_code, District.year == accident_year))
        .all()
    )

    involved["home_district"] = (
        {g.id: g.district_hebrew for g in home_district} if home_district else None
    )

    home_natural_area = (
        db.session.query(NaturalArea)
        .filter(and_(NaturalArea.provider_code == provider_code, NaturalArea.year == accident_year))
        .all()
    )

    involved["home_natural_area"] = (
        {g.id: g.natural_area_hebrew for g in home_natural_area} if home_natural_area else None
    )

    home_municipal_status = (
        db.session.query(MunicipalStatus)
        .filter(
            and_(
                MunicipalStatus.provider_code == provider_code,
                MunicipalStatus.year == accident_year,
            )
        )
        .all()
    )
    involved["home_municipal_status"] = (
        {g.id: g.municipal_status_hebrew for g in home_municipal_status}
        if home_municipal_status
        else None
    )

    home_yishuv_shape = (
        db.session.query(YishuvShape)
        .filter(and_(YishuvShape.provider_code == provider_code, YishuvShape.year == accident_year))
        .all()
    )

    involved["home_yishuv_shape"] = (
        {g.id: g.yishuv_shape_hebrew for g in home_yishuv_shape} if home_yishuv_shape else None
    )

    return involved


def get_vehicle_dict(provider_code, accident_year):
    vehicle = {}
    engine_volume = (
        db.session.query(EngineVolume)
        .filter(
            and_(EngineVolume.provider_code == provider_code, EngineVolume.year == accident_year)
        )
        .all()
    )

    vehicle["engine_volume"] = (
        {g.id: g.engine_volume_hebrew for g in engine_volume} if engine_volume else None
    )

    total_weight = (
        db.session.query(TotalWeight)
        .filter(and_(TotalWeight.provider_code == provider_code, TotalWeight.year == accident_year))
        .all()
    )
    vehicle["total_weight"] = (
        {g.id: g.total_weight_hebrew for g in total_weight} if total_weight else None
    )

    driving_directions = (
        db.session.query(DrivingDirections)
        .filter(
            and_(
                DrivingDirections.provider_code == provider_code,
                DrivingDirections.year == accident_year,
            )
        )
        .all()
    )
    vehicle["driving_directions"] = (
        {g.id: g.driving_directions_hebrew for g in driving_directions}
        if driving_directions
        else None
    )

    return vehicle


@app.route("/markers/all", methods=["GET"])
def marker_all():
    marker_id = request.args.get("marker_id", None)
    provider_code = request.args.get("provider_code", None)
    accident_year = request.args.get("accident_year", None)

    involved = db.session.query(Involved).filter(
        and_(
            Involved.accident_id == marker_id,
            Involved.provider_code == provider_code,
            Involved.accident_year == accident_year,
        )
    )

    vehicles = db.session.query(Vehicle).filter(
        and_(
            Vehicle.accident_id == marker_id,
            Vehicle.provider_code == provider_code,
            Vehicle.accident_year == accident_year,
        )
    )

    list_to_return = list()
    for inv in involved:
        obj = inv.serialize()
        new_inv = get_involved_dict(provider_code, accident_year)
        obj["age_group"] = (
            new_inv["age_group"].get(obj["age_group"]) if new_inv["age_group"] else None
        )
        obj["population_type"] = (
            new_inv["population_type"].get(obj["population_type"])
            if new_inv["population_type"]
            else None
        )
        obj["home_region"] = (
            new_inv["home_region"].get(obj["home_region"]) if new_inv["home_region"] else None
        )
        obj["home_district"] = (
            new_inv["home_district"].get(obj["home_district"]) if new_inv["home_district"] else None
        )
        obj["home_natural_area"] = (
            new_inv["home_natural_area"].get(obj["home_natural_area"])
            if new_inv["home_natural_area"]
            else None
        )
        obj["home_municipal_status"] = (
            new_inv["home_municipal_status"].get(obj["home_municipal_status"])
            if new_inv["home_municipal_status"]
            else None
        )
        obj["home_yishuv_shape"] = (
            new_inv["home_yishuv_shape"].get(obj["home_yishuv_shape"])
            if new_inv["home_yishuv_shape"]
            else None
        )

        list_to_return.append(obj)

    for veh in vehicles:
        obj = veh.serialize()
        new_veh = get_vehicle_dict(provider_code, accident_year)
        obj["engine_volume"] = (
            new_veh["engine_volume"].get(obj["engine_volume"]) if new_veh["engine_volume"] else None
        )
        obj["total_weight"] = (
            new_veh["total_weight"].get(obj["total_weight"]) if new_veh["total_weight"] else None
        )
        obj["driving_directions"] = (
            new_veh["driving_directions"].get(obj["driving_directions"])
            if new_veh["driving_directions"]
            else None
        )

        list_to_return.append(obj)
    return make_response(json.dumps(list_to_return, ensure_ascii=False))


@app.route("/discussion", methods=["GET", "POST"])
def discussion():
    if request.method == "GET":
        identifier = request.values["identifier"]
        context = {
            "identifier": identifier,
            "title": identifier,
            "url": request.base_url,
            "index_url": request.url_root,
        }
        lat, lon = request.values.get("lat"), request.values.get("lon")
        if lat is not None and lon is not None:  # create new discussion
            context.update({"new": True, "latitude": lat, "longitude": lon})
        else:  # show existing discussion
            try:
                marker = (
                    db.session.query(DiscussionMarker)
                    .filter(DiscussionMarker.identifier == identifier)
                    .first()
                )
                context["title"] = marker.title
            except AttributeError:
                return index(
                    message=gettext("Discussion not found:") + request.values["identifier"]
                )
            except KeyError:
                return index(message=gettext("Illegal Discussion"))
        return render_template("disqus.html", **context)
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
    return Response(json.dumps({"clusters": results}), mimetype="application/json")


@app.route("/highlightpoints", methods=["POST"])
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
        logging.debug(
            "Could not parse the requested data, for class:{0}, data:{1}. Error:{2}".format(
                cls, data, e
            )
        )
        return


def get_json_object(request):
    try:
        return request.get_json(force=True)
    except Exception as e:
        logging.debug(
            "Could not get json from a request. request:{0}. Error:{1}".format(request, e)
        )
        return


def log_bad_request(request):
    try:
        logging.debug(
            "Bad {0} Request over {1}. Values: {2} {3}".format(
                request.method, request.url, request.form, request.args
            )
        )
    except AttributeError:
        logging.debug("Bad request:{0}".format(str(request)))


def index(marker=None, message=None):
    context = {"url": request.base_url, "index_url": request.url_root}
    context["CONST"] = CONST.to_dict()
    if "marker" in request.values:
        markers = AccidentMarker.get_marker(request.values["marker"])
        if markers.count() == 1:
            marker = markers[0]
            context["coordinates"] = (marker.latitude, marker.longitude)
            context["marker"] = marker.id
        else:
            message = "תאונה לא נמצאה: " + request.values["marker"]
    elif "discussion" in request.values:
        discussions = DiscussionMarker.get_by_identifier(request.values["discussion"])
        if discussions.count() == 1:
            marker = discussions[0]
            context["coordinates"] = (marker.latitude, marker.longitude)
            context["discussion"] = marker.identifier
        else:
            message = gettext("Discussion not found:") + request.values["discussion"]
    if "start_date" in request.values:
        context["start_date"] = string2timestamp(request.values["start_date"])
    elif marker:
        context["start_date"] = year2timestamp(marker.created.year)
    if "end_date" in request.values:
        context["end_date"] = string2timestamp(request.values["end_date"])
    elif marker:
        context["end_date"] = year2timestamp(marker.created.year + 1)
    for attr in "show_inaccurate", "zoom":
        if attr in request.values:
            context[attr] = request.values[attr]
    if "map_only" in request.values:
        if request.values["map_only"] in ("1", "true"):
            context["map_only"] = 1
    if "lat" in request.values and "lon" in request.values:
        context["coordinates"] = (request.values["lat"], request.values["lon"])
    for attr in (
        "approx",
        "accurate",
        "show_markers",
        "show_accidents",
        "show_rsa",
        "show_discussions",
        "show_urban",
        "show_intersection",
        "show_lane",
        "show_day",
        "show_holiday",
        "show_time",
        "start_time",
        "end_time",
        "weather",
        "road",
        "separation",
        "surface",
        "acctype",
        "controlmeasure",
        "district",
        "case_type",
        "show_fatal",
        "show_severe",
        "show_light",
        "age_groups",
    ):
        value = request.values.get(attr)
        if value is not None:
            context[attr] = value or "-1"
    if message:
        context["message"] = message
    pref_accident_severity = []
    pref_light = PreferenceObject("prefLight", "2", "קלה")
    pref_severe = PreferenceObject("prefSevere", "1", "חמורה")
    pref_fatal = PreferenceObject("prefFatal", "0", "קטלנית")
    pref_accident_severity.extend([pref_light, pref_severe, pref_fatal])
    context["pref_accident_severity"] = pref_accident_severity
    pref_accident_report_severity = []
    pref_report_light = PreferenceObject("prefReportLight", "2", "קלה")
    pref_report_severe = PreferenceObject("prefReportSevere", "1", "חמורה")
    pref_report_fatal = PreferenceObject("prefReportFatal", "0", "קטלנית")
    pref_accident_report_severity.extend([pref_report_light, pref_report_severe, pref_report_fatal])
    context["pref_accident_report_severity"] = pref_accident_report_severity
    pref_historical_report_periods = []
    month_strings = [
        "אחד",
        "שניים",
        "שלושה",
        "ארבעה",
        "חמישה",
        "שישה",
        "שבעה",
        "שמונה",
        "תשעה",
        "עשרה",
        "אחד עשר",
        "שניים עשר",
    ]
    for x in range(0, 12):
        pref_historical_report_periods.append(
            PreferenceObject(
                "prefHistoricalReport" + str(x + 1) + "Month", str(x + 1), month_strings[x]
            )
        )
    context["pref_historical_report_periods"] = pref_historical_report_periods
    pref_radius = []
    for x in range(1, 5):
        pref_radius.append(PreferenceObject("prefRadius" + str(x * 500), x * 500, x * 500))
    context["pref_radius"] = pref_radius
    latest_created_date = AccidentMarker.get_latest_marker_created_date()

    if latest_created_date is None:
        end_date = datetime.date.today()
    else:
        end_date = latest_created_date

    context["default_end_date_format"] = request.values.get(
        "end_date", end_date.strftime("%Y-%m-%d")
    )
    context["default_start_date_format"] = request.values.get(
        "start_date", (end_date - datetime.timedelta(days=365)).strftime("%Y-%m-%d")
    )
    context["entries_per_page"] = ENTRIES_PER_PAGE
    context["iteritems"] = dict.items
    context["hide_search"] = True if request.values.get("hide_search") == "true" else False
    context["embedded_reports"] = get_embedded_reports()
    context["maps_api_key"] = os.environ.get("MAPS_API_KEY", DEFAULT_MAPS_API_KEY)
    return render_template("index.html", **context)


api.set_render_root_function(index)


def string2timestamp(s):
    return time.mktime(datetime.datetime.strptime(s, "%Y-%m-%d").timetuple())


def year2timestamp(y):
    return time.mktime(datetime.date(y, 1, 1).timetuple())


@app.route("/location-subscription", methods=["POST", "OPTIONS"])
def updatebyemail():
    jsonData = request.get_json(force=True)
    logging.debug(jsonData)
    emailaddress = str(jsonData["address"])
    fname = (jsonData["fname"]).encode("utf8")
    lname = (jsonData["lname"]).encode("utf8")
    if len(fname) > 40:
        response = Response(
            json.dumps({"respo": "First name too long"}, default=str), mimetype="application/json"
        )
        response.headers.add("Access-Control-Allow-Methods", ["POST", "OPTIONS"])
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", ["Content-Type", "Authorization"])
        return response
    if len(lname) > 40:
        response = Response(
            json.dumps({"respo": "Last name too long"}, default=str), mimetype="application/json"
        )
        response.headers.add("Access-Control-Allow-Methods", ["POST", "OPTIONS"])
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", ["Content-Type", "Authorization"])
        return response
    if len(emailaddress) > 60:
        response = Response(
            json.dumps({"respo": "Email too long"}, default=str), mimetype="application/json"
        )
        response.headers.add("Access-Control-Allow-Methods", ["POST", "OPTIONS"])
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", ["Content-Type", "Authorization"])
        return response

    curr_max_id = db.session.query(func.max(LocationSubscribers.id)).scalar()
    if curr_max_id is None:
        curr_max_id = 0
    user_id = curr_max_id + 1
    if "school_id" in jsonData.keys():
        school_id = int(jsonData["school_id"])
        user_subscription = LocationSubscribers(
            id=user_id,
            email=emailaddress,
            first_name=fname.decode("utf8"),
            last_name=lname.decode("utf8"),
            ne_lng=None,
            ne_lat=None,
            sw_lng=None,
            sw_lat=None,
            school_id=school_id,
        )
    else:
        user_subscription = LocationSubscribers(
            id=user_id,
            email=emailaddress,
            first_name=fname.decode("utf8"),
            last_name=lname.decode("utf8"),
            ne_lng=jsonData["ne_lng"],
            ne_lat=jsonData["ne_lat"],
            sw_lng=jsonData["sw_lng"],
            sw_lat=jsonData["sw_lat"],
            school_id=None,
        )
    db.session.add(user_subscription)
    db.session.commit()
    response = Response(
        json.dumps({"respo": "Subscription saved"}, default=str), mimetype="application/json"
    )
    response.headers.add("Access-Control-Allow-Methods", ["POST", "OPTIONS"])
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", ["Content-Type", "Authorization"])
    return response


@app.route("/report-problem", methods=["POST"])
def report_problem():
    jsonData = request.get_json(force=True)
    logging.debug(jsonData)
    first_name = (jsonData["first_name"]).encode("utf8")
    last_name = (jsonData["last_name"]).encode("utf8")
    report_problem = ReportProblem(
        latitude=jsonData["latitude"],
        longitude=jsonData["longitude"],
        problem_description=jsonData["problem_description"],
        signs_on_the_road_not_clear=jsonData["signs_on_the_road_not_clear"],
        signs_problem=jsonData["signs_problem"],
        pothole=jsonData["pothole"],
        no_light=jsonData["no_light"],
        no_sign=jsonData["no_sign"],
        crossing_missing=jsonData["crossing_missing"],
        sidewalk_is_blocked=jsonData["sidewalk_is_blocked"],
        street_light_issue=jsonData["street_light_issue"],
        road_hazard=jsonData["road_hazard"],
        first_name=first_name.decode("utf8"),
        last_name=last_name.decode("utf8"),
        phone_number=jsonData["phone_number"],
        email=str(jsonData["email"]),
        send_to_municipality=jsonData["send_to_municipality"],
        personal_id=jsonData["personal_id"],
        image_data=jsonData["image_data"],
    )
    db.session.add(report_problem)
    db.session.commit()
    response = Response(
        json.dumps({"respo": "Subscription saved"}, default=str), mimetype="application/json"
    )
    response.headers.add("Access-Control-Allow-Methods", ["POST", "OPTIONS"])
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", ["Content-Type", "Authorization"])
    return response


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


@app.route("/markers/polygon/", methods=["GET"])
def acc_in_area_query():
    # polygon will be received in the following format: 'POLYGON(({lon} {lat},{lon} {lat},........,{lonN},
    # {latN}))' please note that start point and end point must be equal: i.e. lon=lonN, lat=latN
    # Request format: http://{server url}/markers/polygon?polygon=POLYGON(({lon} {lat},{lon} {lat},........,{lonN},
    # {latN}))"

    # Disable all the no-member violations in this function
    # pylint: disable=no-member
    pol_str = request.values.get("polygon")
    if pol_str is None:
        msg = (
            "polygon parameter is mandatory and must be sent as part of the request - http://{host:port}/markers/polygon?polygon=POLYGON(({lon} {"
            "lat},{lon} {lat},........,{lonN},{latN}))"
        )
        raise abort(Response(msg))  # pylint: disable=all

    query_obj = (
        db.session.query(AccidentMarker)
        .filter(AccidentMarker.geom.intersects(pol_str))
        .filter(
            or_(
                (AccidentMarker.provider_code == BE_CONST.CBS_ACCIDENT_TYPE_1_CODE),
                (AccidentMarker.provider_code == BE_CONST.CBS_ACCIDENT_TYPE_3_CODE),
            )
        )
    )

    df = pd.read_sql_query(query_obj.with_labels().statement, query_obj.session.bind)
    markers_in_area_list = df.to_dict(orient="records")
    response = Response(json.dumps(markers_in_area_list, default=str), mimetype="application/json")
    return response


######## rauth integration (login through facebook) ##################


@app.route("/logout")
def logout() -> Response:
    logout_user()
    identity_changed.send(current_app._get_current_object(), identity=AnonymousIdentity())
    return Response(status=HTTPStatus.OK)


# noinspection PyUnusedLocal
@identity_loaded.connect_via(app)
def on_identity_loaded(sender, identity):
    # Set the identity user object
    identity.user = current_user

    # Add the UserNeed to the identity
    if hasattr(current_user, "id"):
        identity.provides.add(UserNeed(current_user.id))

    # Assuming the User model has a list of roles, update the
    # identity with the roles that the user provides
    if hasattr(current_user, "roles"):
        for role in current_user.roles:
            identity.provides.add(RoleNeed(role.name))

    if not current_user.is_anonymous:
        identity.provides.add(RoleNeed("authenticated"))


@principals.identity_loader
def load_identity_when_session_expires():
    if hasattr(current_user, "id"):
        if hasattr(current_user, "is_active"):
            if not current_user.is_active:
                logout_user()
                return AnonymousIdentity()

        return Identity(current_user.id)


app.add_url_rule("/api/schools", endpoint=None, view_func=schools_api, methods=["GET"])
app.add_url_rule(
    "/api/schools-description", endpoint=None, view_func=schools_description_api, methods=["GET"]
)
app.add_url_rule(
    "/api/schools-yishuvs", endpoint=None, view_func=schools_yishuvs_api, methods=["GET"]
)
app.add_url_rule("/api/schools-names", endpoint=None, view_func=schools_names_api, methods=["GET"])
app.add_url_rule(
    "/api/injured-around-schools-sex-graphs-data",
    endpoint=None,
    view_func=injured_around_schools_sex_graphs_data_api,
    methods=["GET"],
)
app.add_url_rule(
    "/api/injured-around-schools-months-graphs-data",
    endpoint=None,
    view_func=injured_around_schools_months_graphs_data_api,
    methods=["GET"],
)
app.add_url_rule(
    "/api/injured-around-schools",
    endpoint=None,
    view_func=injured_around_schools_api,
    methods=["GET"],
)
app.add_url_rule("/api/news-flash", endpoint=None, view_func=news_flash, methods=["GET"])

app.add_url_rule("/api/news-flash-v2", endpoint=None, view_func=news_flash_v2, methods=["GET"])


nf_parser = reqparse.RequestParser()
nf_parser.add_argument("id", type=int, help="News flash id")
nf_parser.add_argument("source", type=str, help="news flash source")
nf_parser.add_argument(
    "start_date",
    type=int,
    help="limit news flashes to a time period starting at the given timestamp",
)
nf_parser.add_argument(
    "end_date", type=int, help="limit news flashes to a time period ending at the given timestamp"
)
nf_parser.add_argument("interurban_only", type=str, help="limit news flashes to inter-urban")
nf_parser.add_argument("road_number", type=int, help="limit news flashes to given road")
nf_parser.add_argument(
    "road_segment_only",
    type=bool,
    help="limit news flashes to items where a road_segment is specified",
)
nf_parser.add_argument(
    "offset",
    type=int,
    default=DEFAULT_OFFSET_REQ_PARAMETER,
    help="skip items from start to given offset",
)
nf_parser.add_argument(
    "limit",
    type=int,
    default=DEFAULT_LIMIT_REQ_PARAMETER,
    help="limit number of retrieved items to given limit",
)


def datetime_to_str(val: datetime.datetime) -> str:
    return val.strftime("%Y-%m-%d %H:%M:%S") if isinstance(val, datetime.datetime) else "None"


news_flash_fields_model = api.model(
    "news_flash",
    {
        "id": fields.Integer(),
        "accident": fields.Boolean(description="This news-flash reports an accident"),
        "author": fields.String(),
        "date": fields.String(description='format: "%Y-%m-%d %H:%M:%S"'),
        "description": fields.String(),
        "lat": fields.Float(),
        "link": fields.String(),
        "lon": fields.Float(),
        "road1": fields.Float(),
        "road2": fields.Float(),
        "resolution": fields.String(description="Type of location of this news-flash"),
        "title": fields.String(),
        "source": fields.String(),
        "organization": fields.String(),
        "location": fields.String(),
        "tweet_id": fields.Integer(),
        "region_hebrew": fields.String(),
        "district_hebrew": fields.String(),
        "yishuv_name": fields.String(),
        "street1_hebrew": fields.String(),
        "street2_hebrew": fields.String(),
        "non_urban_intersection_hebrew": fields.String(),
        "road_segment_name": fields.String(),
    },
)
news_flash_list_model = api.model(
    "news_flash_list", {"news_flashes": fields.List(fields.Nested(news_flash_fields_model))}
)


@api.route("/api/news-flash/<int:news_flash_id>")
class RetrieveSingleNewsFlash(Resource):
    @api.doc("get single news flash")
    @api.response(404, "News flash not found")
    @api.response(200, "Retrieve single news-flash item", news_flash_fields_model)
    def get(self, news_flash_id):
        return single_news_flash(news_flash_id)


@api.route("/api/news-flash-new", methods=["GET"])
class RetrieveNewsFlash(Resource):
    @api.doc("get news flash records")
    @api.expect(nf_parser)
    @api.response(404, "Parameter value not supported or missing")
    @api.response(
        200, "Retrieve news-flash items filtered by given parameters", news_flash_list_model
    )
    def get(self):
        args = nf_parser.parse_args()
        res = news_flash_new(args)
        for d in res:
            d["date"] = datetime_to_str(d["date"]) if "date" in d else "None"
        return {"news_flashes": res}


# Copied and modified from flask-security
def roles_accepted(*roles):
    """Decorator which specifies that a user must have at least one of the
    specified roles. Example::
        @app.route('/create_post')
        @roles_accepted('editor', 'author')
        def create_post():
            return 'Create Post'
    The current user must have either the `editor` role or `author` role in
    order to view the page.
    :param roles: The possible roles.
    """

    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            perm = Permission(*[RoleNeed(role) for role in roles])
            if perm.can():
                return fn(*args, **kwargs)
            user_email = "not logged in"
            user_roles = ""
            if not current_user.is_anonymous:
                user_email = current_user.email
                user_roles = str([role.name for role in current_user.roles])
            logging.info(
                f"roles_accepted: User {user_email} doesn't have the needed roles: {str(roles)} for Path {request.url_rule}, but the user have {user_roles}"
            )
            return return_json_error(Es.BR_BAD_AUTH)

        return decorated_view

    return wrapper


def return_json_error(error_code: int, *argv) -> Response:
    return app.response_class(
        response=json.dumps(build_json_for_user_api_error(error_code, argv)),
        status=ERROR_TO_HTTP_CODE_DICT[error_code],
        mimetype="application/json",
    )


@app.route("/authorize/<provider>")
def oauth_authorize(provider: str) -> Response:
    if provider != "google":
        return return_json_error(Es.BR_ONLY_SUPPORT_GOOGLE)

    if not current_user.is_anonymous:
        return return_json_error(Es.BR_USER_ALREADY_LOGGED_IN)

    redirect_url_from_url = request.args.get("redirect_url", type=str)
    redirect_url = BE_CONST.DEFAULT_REDIRECT_URL
    if redirect_url_from_url and is_a_safe_redirect_url(redirect_url_from_url):
        redirect_url = redirect_url_from_url

    oauth = OAuthSignIn.get_provider(provider)
    return oauth.authorize(redirect_url=redirect_url)


@app.route("/callback/<provider>")
def oauth_callback(provider: str) -> Response:
    if provider != "google":
        return return_json_error(Es.BR_ONLY_SUPPORT_GOOGLE)

    oauth = OAuthSignIn.get_provider(provider)
    user_data: UserData = oauth.callback()
    if not user_data or not user_data.service_user_id:
        return return_json_error(Es.BR_NO_USER_ID)

    user = (
        db.session.query(Users)
        .filter_by(oauth_provider=provider, oauth_provider_user_id=user_data.service_user_id)
        .first()
    )

    if not user:
        user = (
            db.session.query(Users)
            .filter_by(oauth_provider=provider, email=user_data.email)
            .first()
        )

    if not user:
        user = Users(
            user_register_date=datetime.datetime.now(),
            user_last_login_date=datetime.datetime.now(),
            email=user_data.email,
            oauth_provider_user_name=user_data.name,
            is_active=True,
            oauth_provider=provider,
            oauth_provider_user_id=user_data.service_user_id,
            oauth_provider_user_domain=user_data.service_user_domain,
            oauth_provider_user_picture_url=user_data.picture_url,
            oauth_provider_user_locale=user_data.service_user_locale,
            oauth_provider_user_profile_url=user_data.user_profile_url,
        )
        db.session.add(user)
    else:
        if not user.is_active:
            return return_json_error(Es.BR_USER_NOT_ACTIVE)

        user.user_last_login_date = datetime.datetime.now()
        if (
            user.oauth_provider_user_id == "unknown-manual-insert"
        ):  # Only for anyway@anyway.co.il first login
            user.oauth_provider_user_id = user_data.service_user_id
            user.oauth_provider_user_name = user_data.name
            user.oauth_provider_user_domain = user_data.service_user_domain
            user.oauth_provider_user_picture_url = user_data.picture_url
            user.oauth_provider_user_locale = user_data.service_user_locale
            user.oauth_provider_user_profile_url = user_data.user_profile_url

    db.session.commit()

    redirect_url = BE_CONST.DEFAULT_REDIRECT_URL
    redirect_url_json_base64 = request.args.get("state", type=str)
    if redirect_url_json_base64:
        redirect_url_json = json.loads(base64.b64decode(redirect_url_json_base64.encode("UTF8")))
        redirect_url_to_check = redirect_url_json.get("redirect_url")
        if redirect_url_to_check and is_a_safe_redirect_url(redirect_url_to_check):
            redirect_url = redirect_url_to_check

    login_user(user, True)
    identity_changed.send(current_app._get_current_object(), identity=Identity(user.id))

    return redirect(redirect_url, code=HTTPStatus.FOUND)


"""
    Returns infographics-data API
"""
parser = reqparse.RequestParser()
parser.add_argument("id", type=int, help="News flash id")
parser.add_argument(
    "years_ago", type=int, default=5, help="Number of years back to consider accidents"
)
parser.add_argument("lang", type=str, default="he", help="Language")


@api.route("/api/infographics-data", methods=["GET"])
class InfographicsData(Resource):
    @api.doc("get infographics data")
    @api.expect(parser)
    def get(self):
        return infographics_data()


def infographics_data():
    mock_data = request.values.get("mock", "false")
    personalized_data = request.values.get("personalized", "false")
    if mock_data == "true":
        output = get_infographics_mock_data()
    elif mock_data == "false":
        news_flash_id = request.values.get("news_flash_id")
        if news_flash_id == None:
            log_bad_request(request)
            return abort(http_client.BAD_REQUEST)

        number_of_years_ago = request.values.get("years_ago", BE_CONST.DEFAULT_NUMBER_OF_YEARS_AGO)
        lang: str = request.values.get("lang", "he")
        logging.debug(
            (
                "getting infographics data for news_flash_id: {news_flash_id}, "
                + "in time period:{number_of_years_ago}, lang:{lang}"
            ).format(
                news_flash_id=news_flash_id, number_of_years_ago=number_of_years_ago, lang=lang
            )
        )
        output = get_infographics_data(
            news_flash_id=news_flash_id, years_ago=number_of_years_ago, lang=lang
        )
        if not output:
            log_bad_request(request)
            return abort(http_client.NOT_FOUND)
    else:
        log_bad_request(request)
        return abort(http_client.BAD_REQUEST)

    if personalized_data == "true":
        output = widgets_personalisation_for_user(output)

    json_data = json.dumps(output, default=str)
    return Response(json_data, mimetype="application/json")


"""
    Returns GPS to CBS location
"""
gps_parser = reqparse.RequestParser()
gps_parser.add_argument("longitude", type=float, help="longitude")
gps_parser.add_argument("latitude", type=float, help="latitude")


@api.route("/api/gps-to-location", methods=["GET"])
class GPSToLocation(Resource):
    @api.doc("from gps to location")
    @api.expect(gps_parser)
    def get(self):
        return gps_to_cbs_location()


def gps_to_cbs_location():
    longitude = request.values.get("longitude")
    latitude = request.values.get("latitude")
    if not longitude or not latitude:
        log_bad_request(request)
        return abort(http_client.BAD_REQUEST)
    from anyway.parsers.news_flash_db_adapter import init_db
    from anyway.parsers.location_extraction import (
        get_db_matching_location_interurban,
        get_road_segment_id,
    )

    location = get_db_matching_location_interurban(float(latitude), float(longitude))
    if not location:
        logging.info("location not exist")
    location["resolution"] = "interurban_road_segment"
    location["road_segment_id"] = get_road_segment_id(
        road_segment_name=location["road_segment_name"]
    )
    json_data = json.dumps(location, default=str)
    return Response(json_data, mimetype="application/json")


"""
    Returns infographics-data-by-location API
"""
idbl_parser = reqparse.RequestParser()
idbl_parser.add_argument("road_segment_id", type=int, help="Road Segment id")
idbl_parser.add_argument(
    "years_ago", type=int, default=5, help="Number of years back to consider accidents"
)
idbl_parser.add_argument("lang", type=str, default="he", help="Language")


@api.route("/api/infographics-data-by-location", methods=["GET"])
class InfographicsDataByLocation(Resource):
    @api.doc("get infographics data")
    @api.expect(idbl_parser)
    def get(self):
        return infographics_data_by_location()


def infographics_data_by_location():
    mock_data = request.values.get("mock", "false")
    personalized_data = request.values.get("personalized", "false")
    if mock_data == "true":
        output = get_infographics_mock_data()
    elif mock_data == "false":
        road_segment_id = request.values.get("road_segment_id")
        if road_segment_id == None:
            log_bad_request(request)
            return abort(http_client.BAD_REQUEST)

        number_of_years_ago = request.values.get("years_ago", BE_CONST.DEFAULT_NUMBER_OF_YEARS_AGO)
        lang: str = request.values.get("lang", "he")
        logging.debug(
            (
                "getting infographics data for news_flash_id: {news_flash_id}, "
                + "in time period:{number_of_years_ago}, lang:{lang}"
            ).format(
                news_flash_id=road_segment_id, number_of_years_ago=number_of_years_ago, lang=lang
            )
        )
        output = get_infographics_data_for_road_segment(
            road_segment_id=road_segment_id, years_ago=number_of_years_ago, lang=lang
        )
        if not output:
            log_bad_request(request)
            return abort(http_client.NOT_FOUND)
    else:
        log_bad_request(request)
        return abort(http_client.BAD_REQUEST)

    if personalized_data == "true":
        output = widgets_personalisation_for_user(output)

    json_data = json.dumps(output, default=str)
    return Response(json_data, mimetype="application/json")


def widgets_personalisation_for_user(raw_info: typing.Dict) -> typing.Dict:
    if current_user.is_anonymous:
        return raw_info

    roles_names = [role.name for role in current_user.roles]

    if BE_CONST.Roles2Names.Or_yarok.value in roles_names:
        widgets_list = raw_info.get("widgets")
        if not widgets_list:
            return raw_info

        new_list = []
        for wig in widgets_list:
            wig_name = wig.get("name")
            if wig_name is None:
                new_list.append(wig)
                continue

            if wig_name in BE_CONST.OR_YAROK_WIDGETS:
                new_list.append(wig)
        raw_info["widgets"] = new_list
    return raw_info


def get_embedded_reports():
    logging.debug("getting embedded reports")
    embedded_reports = db.session.query(EmbeddedReports).all()
    embedded_reports_list = [
        {
            "id": x.id,
            "report_name_english": x.report_name_english,
            "report_name_hebrew": x.report_name_hebrew,
            "url": x.url,
        }
        for x in embedded_reports
    ]
    return embedded_reports_list


@app.route("/api/embedded-reports", methods=["GET"])
def embedded_reports_api():
    embedded_reports_list = get_embedded_reports()
    response = Response(json.dumps(embedded_reports_list, default=str), mimetype="application/json")
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response


@login_manager.user_loader
def load_user(id: str) -> Users:
    return db.session.query(Users).get(id)


# TODO: in the future add pagination if needed
@app.route("/user/get_all_users_info")
@roles_accepted(BE_CONST.Roles2Names.Admins.value)
def get_all_users_info() -> Response:
    dict_ret = []
    for user_obj in db.session.query(Users).order_by(Users.user_register_date).all():
        dict_ret.append(user_obj.serialize_exposed_to_user())
    return jsonify(dict_ret)


@app.route("/user/info")
@roles_accepted(BE_CONST.Roles2Names.Authenticated.value)
def get_user_info() -> Response:
    user_obj = get_current_user()
    return jsonify(user_obj.serialize_exposed_to_user())


@app.route("/user/remove_from_role", methods=["POST"])
@roles_accepted(BE_CONST.Roles2Names.Admins.value)
def remove_from_role() -> Response:
    return change_user_roles("remove")


@app.route("/user/add_to_role", methods=["POST"])
@roles_accepted(BE_CONST.Roles2Names.Admins.value)
def add_to_role() -> Response:
    return change_user_roles("add")


def is_input_fields_malformed(request: Request, allowed_fields: typing.List[str]) -> bool:
    # Validate input
    reg_dict = request.json
    if not reg_dict:
        return True
    for key in reg_dict:
        if key not in allowed_fields:
            return True
    return False


def change_user_roles(action: str) -> Response:
    allowed_fields = [
        "role",
        "email",
    ]

    res = is_input_fields_malformed(request, allowed_fields)
    if res:
        return return_json_error(Es.BR_FIELD_MISSING)
    reg_dict = request.json

    role_name = reg_dict.get("role")
    if not role_name:
        return return_json_error(Es.BR_ROLE_NAME_MISSING)
    role = get_role_object(role_name)
    if role is None:
        return return_json_error(Es.BR_ROLE_NOT_EXIST, role_name)

    email = reg_dict.get("email")
    if not email:
        return return_json_error(Es.BR_NO_EMAIL)
    if not is_a_valid_email(email):
        return return_json_error(Es.BR_BAD_EMAIL)
    user = get_user_by_email(db, email)
    if user is None:
        return return_json_error(Es.BR_USER_NOT_FOUND, email)

    if action == "add":
        # Add user to role
        for user_role in user.roles:
            if role.name == user_role.name:
                return return_json_error(Es.BR_USER_ALREADY_IN_ROLE, email, role_name)
        user.roles.append(role)
        # Add user to role in the current instance
        if current_user.email == user.email:
            # g is flask global data
            g.identity.provides.add(RoleNeed(role.name))
    elif action == "remove":
        # Remove user from role
        removed = False
        for user_role in user.roles:
            if role.name == user_role.name:
                d = users_to_roles.delete().where(  # noqa pylint: disable=no-value-for-parameter
                    (users_to_roles.c.user_id == user.id) & (users_to_roles.c.role_id == role.id)
                )
                db.session.execute(d)
                removed = True
        if not removed:
            return return_json_error(Es.BR_USER_NOT_IN_ROLE, email, role_name)
    db.session.commit()

    return Response(status=HTTPStatus.OK)


def get_role_object(role_name):
    role = db.session.query(Roles).filter(Roles.name == role_name).first()
    return role


@app.route("/user/update_user", methods=["POST"])
@roles_accepted(BE_CONST.Roles2Names.Admins.value)
def admin_update_user() -> Response:
    allowed_fields = [
        "user_current_email",
        "first_name",
        "last_name",
        "email",
        "phone",
        "user_type",
        "user_url",
        "user_desc",
        "is_user_completed_registration",
    ]

    res = is_input_fields_malformed(request, allowed_fields)
    if res:
        return return_json_error(Es.BR_FIELD_MISSING)
    reg_dict = request.json

    user_current_email = reg_dict.get("user_current_email")
    if not user_current_email:
        return return_json_error(Es.BR_NO_EMAIL)
    if not is_a_valid_email(user_current_email):
        return return_json_error(Es.BR_BAD_EMAIL)
    user = get_user_by_email(db, user_current_email)
    if user is None:
        return return_json_error(Es.BR_USER_NOT_FOUND, user_current_email)

    user_db_new_email = reg_dict.get("email")
    if not is_a_valid_email(user_db_new_email):
        return return_json_error(Es.BR_BAD_EMAIL)

    phone = reg_dict.get("phone")
    if phone and not is_valid_number(phone):
        return return_json_error(Es.BR_BAD_PHONE)

    first_name = reg_dict.get("first_name")
    last_name = reg_dict.get("last_name")
    user_desc = reg_dict.get("user_desc")
    user_type = reg_dict.get("user_type")
    user_url = reg_dict.get("user_url")
    is_user_completed_registration = reg_dict.get("is_user_completed_registration")
    update_user_in_db(
        user,
        first_name,
        last_name,
        phone,
        user_db_new_email,
        user_desc,
        user_type,
        user_url,
        is_user_completed_registration,
    )

    return Response(status=HTTPStatus.OK)


# This code is also used as part of the user first registration
@app.route("/user/update", methods=["POST"])
@roles_accepted(BE_CONST.Roles2Names.Authenticated.value)
def user_update() -> Response:
    allowed_fields = [
        "first_name",
        "last_name",
        "email",
        "phone",
        "user_type",
        "user_url",
        "user_desc",
    ]

    res = is_input_fields_malformed(request, allowed_fields)
    if res:
        return return_json_error(Es.BR_FIELD_MISSING)
    reg_dict = request.json

    first_name = reg_dict.get("first_name")
    last_name = reg_dict.get("last_name")
    if not first_name or not last_name:
        return return_json_error(Es.BR_FIRST_NAME_OR_LAST_NAME_MISSING)

    # If we don't have the user email then we have to get it else only update if the user want.
    tmp_given_user_email = reg_dict.get("email")
    user_db_email = get_current_user_email()
    if not user_db_email or tmp_given_user_email:
        if not tmp_given_user_email:
            return return_json_error(Es.BR_NO_EMAIL)

        if not is_a_valid_email(tmp_given_user_email):
            return return_json_error(Es.BR_BAD_EMAIL)

        user_db_email = tmp_given_user_email

    phone = reg_dict.get("phone")
    if phone and not is_valid_number(phone):
        return return_json_error(Es.BR_BAD_PHONE)

    user_type = reg_dict.get("user_type")
    user_url = reg_dict.get("user_url")
    user_desc = reg_dict.get("user_desc")

    update_user_in_db(
        first_name, last_name, phone, user_db_email, user_desc, user_type, user_url, True
    )

    return Response(status=HTTPStatus.OK)


def update_user_in_db(
    user: Users,
    first_name: str,
    last_name: str,
    phone: str,
    user_db_email: str,
    user_desc: str,
    user_type: str,
    user_url: str,
    is_user_completed_registration: bool,
) -> None:
    user.first_name = first_name
    user.last_name = last_name
    user.email = user_db_email
    user.phone = phone
    user.user_type = user_type
    user.user_url = user_url
    user.user_desc = user_desc
    user.is_user_completed_registration = is_user_completed_registration
    db.session.commit()


@app.route("/user/change_user_active_mode", methods=["POST"])
@roles_accepted(BE_CONST.Roles2Names.Admins.value)
def user_disable() -> Response:
    allowed_fields = [
        "email",
        "mode",
    ]

    result = is_input_fields_malformed(request, allowed_fields)
    if result:
        return return_json_error(Es.BR_FIELD_MISSING)
    reg_dict = request.json

    email = reg_dict.get("email")
    if not email:
        return return_json_error(Es.BR_NO_EMAIL)
    if not is_a_valid_email(email):
        return return_json_error(Es.BR_BAD_EMAIL)
    user = get_user_by_email(db, email)
    if user is None:
        return return_json_error(Es.BR_USER_NOT_FOUND, email)

    mode = reg_dict.get("mode")
    if mode is None:
        return return_json_error(Es.BR_NO_MODE)

    if type(mode) != bool:
        return return_json_error(Es.BR_BAD_MODE)

    user.is_active = mode
    db.session.commit()
    return Response(status=HTTPStatus.OK)


@app.route("/user/add_role", methods=["POST"])
@roles_accepted(BE_CONST.Roles2Names.Admins.value)
def add_role() -> Response:
    allowed_fields = [
        "name",
        "description",
    ]

    res = is_input_fields_malformed(request, allowed_fields)
    if res:
        return return_json_error(Es.BR_FIELD_MISSING)
    reg_dict = request.json

    name = reg_dict.get("name")
    if not name:
        return return_json_error(Es.BR_ROLE_NAME_MISSING)

    if not is_a_valid_role_name(name):
        return return_json_error(Es.BR_BAD_ROLE_NAME)

    role = db.session.query(Roles).filter(Roles.name == name).first()
    if role:
        return return_json_error(Es.BR_ROLE_EXIST)

    description = reg_dict.get("description")
    if not description:
        return return_json_error(Es.BR_ROLE_DESCRIPTION_MISSING)

    if not is_a_valid_role_description(description):
        return return_json_error(Es.BR_BAD_ROLE_DESCRIPTION)

    role = Roles(name=name, description=description, create_date=datetime.datetime.now())
    db.session.add(role)
    db.session.commit()
    return Response(status=HTTPStatus.OK)


def is_a_valid_role_name(name: str) -> bool:
    if len(name) < 2 or len(name) >= Roles.name.type.length:
        return False

    match = re.match("^[a-zA-Z0-9_-]+$", name)
    if not match:
        return False

    return True


def is_a_valid_role_description(name: str) -> bool:
    if len(name) >= Roles.description.type.length:
        return False

    return True


@app.route("/user/get_roles_list", methods=["GET"])
@roles_accepted(BE_CONST.Roles2Names.Admins.value)
def get_roles_list() -> Response:
    roles_list = db.session.query(Roles).all()
    send_list = []
    for role in roles_list:
        send_list.append({"id": role.id, "name": role.name, "description": role.description})

    return app.response_class(
        response=json.dumps(send_list),
        status=HTTPStatus.OK,
        mimetype="application/json",
    )
