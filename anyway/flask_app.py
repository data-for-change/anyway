# -*- coding: utf-8 -*-
# pylint: disable=no-member
import csv
import os
import time
from http import client as http_client
from io import StringIO

import jinja2
import pandas as pd
from flask import make_response, render_template, abort
from flask import session
from flask_assets import Environment
from flask_babel import Babel, gettext
from flask_compress import Compress
from flask_cors import CORS
from flask_restx import Resource, fields, reqparse
from sqlalchemy import and_, not_, or_
from sqlalchemy import func
from webassets import Environment as AssetsEnvironment, Bundle as AssetsBundle
from webassets.ext.jinja2 import AssetsExtension
from werkzeug.exceptions import BadRequestKeyError

from anyway import utilities, secrets
from anyway.app_and_db import api, get_cors_config
from anyway.clusters_calculator import retrieve_clusters
from anyway.config import ENTRIES_PER_PAGE
from anyway.constants import CONST
from anyway.infographics_utils import (
    get_infographics_data,
    get_infographics_mock_data,
    get_infographics_data_for_location,
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
)
from anyway.request_params import get_request_params_from_request_values
from anyway.views.news_flash.api import (
    news_flash,
    news_flash_new,
    single_news_flash,
    news_flash_v2,
    DEFAULT_LIMIT_REQ_PARAMETER,
    DEFAULT_OFFSET_REQ_PARAMETER,
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
from anyway.views.user_system.api import *

DEFAULT_MAPS_API_KEY = "AIzaSyDUIWsBLkvIUwzLHMHos9qFebyJ63hEG2M"


app.config.from_object(__name__)
app.config["SWAGGER_UI_DOC_EXPANSION"] = "list"
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

CORS(app, resources=get_cors_config())

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
        .filter(not_(AccidentMarkerView.yishuv_name is None))
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
    context = {"url": request.base_url, "index_url": request.url_root, "CONST": CONST.to_dict()}
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
    json_data = request.get_json(force=True)
    logging.debug(json_data)
    emailaddress = str(json_data["address"])
    fname = (json_data["fname"]).encode("utf8")
    lname = (json_data["lname"]).encode("utf8")
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
    if "school_id" in json_data.keys():
        school_id = int(json_data["school_id"])
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
            ne_lng=json_data["ne_lng"],
            ne_lat=json_data["ne_lat"],
            sw_lng=json_data["sw_lng"],
            sw_lat=json_data["sw_lat"],
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
    json_data = request.get_json(force=True)
    logging.debug(json_data)
    first_name = (json_data["first_name"]).encode("utf8")
    last_name = (json_data["last_name"]).encode("utf8")
    report_problem = ReportProblem(
        latitude=json_data["latitude"],
        longitude=json_data["longitude"],
        problem_description=json_data["problem_description"],
        signs_on_the_road_not_clear=json_data["signs_on_the_road_not_clear"],
        signs_problem=json_data["signs_problem"],
        pothole=json_data["pothole"],
        no_light=json_data["no_light"],
        no_sign=json_data["no_sign"],
        crossing_missing=json_data["crossing_missing"],
        sidewalk_is_blocked=json_data["sidewalk_is_blocked"],
        street_light_issue=json_data["street_light_issue"],
        road_hazard=json_data["road_hazard"],
        first_name=first_name.decode("utf8"),
        last_name=last_name.decode("utf8"),
        phone_number=json_data["phone_number"],
        email=str(json_data["email"]),
        send_to_municipality=json_data["send_to_municipality"],
        personal_id=json_data["personal_id"],
        image_data=json_data["image_data"],
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
app.add_url_rule("/api/news-flash", endpoint=None, view_func=news_flash_v2, methods=["GET"])

app.add_url_rule("/api/v1/news-flash", endpoint=None, view_func=news_flash, methods=["GET"])


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
        if news_flash_id is None:
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
        get_road_segment_by_name,
    )

    location = get_db_matching_location_interurban(float(latitude), float(longitude))
    if not location:
        logging.info("location not exist")
    location["resolution"] = "interurban_road_segment"
    location["road_segment_id"] = get_road_segment_by_name(
        road_segment_name=location["road_segment_name"]
    ).segment_id
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
        request_params = get_request_params_from_request_values(request.values)
        output = get_infographics_data_for_location(request_params)
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


# def infographics_data_by_location():
#     mock_data = request.values.get("mock", "false")
#     personalized_data = request.values.get("personalized", "false")
#     if mock_data == "true":
#         output = get_infographics_mock_data()
#     elif mock_data == "false":
#         road_segment_id = request.values.get("road_segment_id")
#         if road_segment_id == None:
#             log_bad_request(request)
#             return abort(http_client.BAD_REQUEST)
#
#         number_of_years_ago = request.values.get("years_ago", BE_CONST.DEFAULT_NUMBER_OF_YEARS_AGO)
#         lang: str = request.values.get("lang", "he")
#         logging.debug(
#             (
#                 "getting infographics data for news_flash_id: {news_flash_id}, "
#                 + "in time period:{number_of_years_ago}, lang:{lang}"
#             ).format(
#                 news_flash_id=road_segment_id, number_of_years_ago=number_of_years_ago, lang=lang
#             )
#         )
#         output = get_infographics_data_for_road_segment(
#             road_segment_id=road_segment_id, years_ago=number_of_years_ago, lang=lang
#         )
#         if not output:
#             log_bad_request(request)
#             return abort(http_client.NOT_FOUND)
#     else:
#         log_bad_request(request)
#         return abort(http_client.BAD_REQUEST)
#
#     if personalized_data == "true":
#         output = widgets_personalisation_for_user(output)
#
#     json_data = json.dumps(output, default=str)
#     return Response(json_data, mimetype="application/json")
#
#

# User system API
app.add_url_rule("/user/add_role", view_func=add_role, methods=["POST"])
app.add_url_rule(
    "/user/change_user_active_mode", view_func=change_user_active_mode, methods=["POST"]
)
app.add_url_rule("/user/update", view_func=user_update, methods=["POST"])
app.add_url_rule("/user/update_user", view_func=admin_update_user, methods=["POST"])
app.add_url_rule("/user/add_to_role", view_func=add_to_role, methods=["POST"])
app.add_url_rule("/user/remove_from_role", view_func=remove_from_role, methods=["POST"])
app.add_url_rule("/user/info", view_func=get_user_info, methods=["GET"])
app.add_url_rule("/user/get_all_users_info", view_func=get_all_users_info, methods=["GET"])
app.add_url_rule("/user/get_roles_list", view_func=get_roles_list, methods=["GET"])
app.add_url_rule("/callback/<provider>", view_func=oauth_callback, methods=["GET"])
app.add_url_rule("/authorize/<provider>", view_func=oauth_authorize, methods=["GET"])

# A hack for Jinja template that is looking for /logout
app.add_url_rule("/logout", view_func=logout, methods=["GET"])


@api.route("/logout")
class UserLogout(Resource):
    @api.doc("Logout the user")
    @api.response(200, "")
    def get(self):
        return logout()


@api.route("/user/get_organization_list")
class GetOrganizationList(Resource):
    @api.doc("Get a list of organizations from the DB")
    @api.response(200, "", fields.List(fields.String(example="Anyway")))
    @api.response(401, "Unauthorized")
    def get(self):
        return get_organization_list()


add_org_parser = api.parser()
add_org_parser.add_argument("name", type=str, required=True)


@api.route("/user/add_organization")
@api.expect(add_org_parser)
class AddOrganization(Resource):
    @api.doc("Add an organization to the DB")
    @api.response(200, "")
    @api.response(400, "Name is missing from the request")
    @api.response(401, "Unauthorized")
    def post(self):
        args = add_org_parser.parse_args()
        org_name = args["name"]
        return add_organization(org_name)


update_user_org_parser = api.parser()
update_user_org_parser.add_argument("email", type=str, required=True)
update_user_org_parser.add_argument(
    "org",
    type=str,
    required=False,
    help="If 'org' argument is missing then the user will not be a member of any organization.",
)


@api.route("/user/update_user_org")
@api.expect(update_user_org_parser)
class UpdateUserOrg(Resource):
    @api.doc(
        "Add user as a member in organization, if 'org' argument is missing then the user will not be a "
        "member of any organization"
    )
    @api.response(200, "")
    @api.response(400, "Organization or User is not in the DB")
    def post(self):
        args = update_user_org_parser.parse_args()
        user_email = args["email"]
        org_name = args["org"]
        return update_user_org(user_email, org_name)
