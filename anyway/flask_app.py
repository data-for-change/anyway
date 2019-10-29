# -*- coding: utf-8 -*-
# pylint: disable=no-member
import datetime
# from sendgrid import SendGridAPIClient
import glob
import json
import logging
import os

import flask_admin as admin
import flask_login as login
import jinja2
from flask import make_response, render_template, Response, jsonify, url_for, flash
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
from six import iteritems
from sqlalchemy import and_, not_
from sqlalchemy import func
from sqlalchemy.orm import load_only
from webassets import Environment as AssetsEnvironment
from webassets.ext.jinja2 import AssetsExtension
from werkzeug.security import check_password_hash
from wtforms import form, fields, validators, StringField, PasswordField, Form

from anyway.app_views.clusters.api import clusters
from anyway.app_views.news_flash.api import news_flash, single_news_flash
from anyway.app import app, db
from anyway.helpers import get_kwargs, involved_data_refinement, vehicles_data_refinement, \
    parse_data, get_json_object, log_bad_request, post_handler, string2timestamp, \
    year2timestamp, PreferenceObject, get_dict_file
from anyway.app_views.markers.api import markers, marker, marker_all
from anyway.app_views.schools.api import schools_api, schools_description_api, schools_yishuvs_api, schools_names_api, \
    injured_around_schools_api, injured_around_schools_sex_graphs_data_api, \
    injured_around_schools_months_graphs_data_api
from anyway.app_views.schools.base import schools, schools_report
from anyway.parsers.cbs import global_cbs_dictionary
from . import utilities
from .base import user_optional
from .clusters_calculator import retrieve_clusters
from .config import ENTRIES_PER_PAGE
from .constants import CONST
from .models import (AccidentMarker, DiscussionMarker, HighlightPoint, User, ReportPreferences,
                     LocationSubscribers, Role, GeneralPreferences, NewsFlash, ReportProblem)
from .oauth import OAuthSignIn

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

CORS(app, resources={r"/location-subscription": {"origins": "*"}, r"/report-problem": {"origins": "*"}})

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

CORS(app, resources={r"/location-subscription": {"origins": "*"}})


@app.teardown_appcontext
def shutdown_session(exception=None):
    db.session.remove()


@babel.localeselector
def get_locale():
    lang = request.values.get('lang')
    if lang is None:
        return request.accept_languages.best_match(app.config['LANGUAGES'].keys())
    else:
        return lang


app.add_url_rule('/schools', endpoint=None, view_func=schools, methods=["GET"])
app.add_url_rule('/schools-report', endpoint=None, view_func=schools_report, methods=["GET"])

app.add_url_rule("/markers", endpoint=None, view_func=markers, methods=["GET"])

app.add_url_rule("/api/news-flash", endpoint=None, view_func=news_flash, methods=["GET"])
app.add_url_rule("/api/news-flash/<int:news_flash_id>", endpoint=None, view_func=single_news_flash, methods=["GET"])

app.add_url_rule("/api/schools", endpoint=None, view_func=schools_api, methods=["GET"])
app.add_url_rule("/api/schools-description", endpoint=None, view_func=schools_description_api, methods=["GET"])
app.add_url_rule("/api/schools-yishuvs", endpoint=None, view_func=schools_yishuvs_api, methods=["GET"])
app.add_url_rule("/api/schools-names", endpoint=None, view_func=schools_names_api, methods=["GET"])
app.add_url_rule("/api/injured-around-schools", endpoint=None, view_func=injured_around_schools_api, methods=["GET"])
app.add_url_rule("/api/injured-around-schools-sex-graphs-data", endpoint=None, view_func=injured_around_schools_sex_graphs_data_api, methods=["GET"])
app.add_url_rule("/api/injured-around-schools-months-graphs-data", endpoint=None, view_func=injured_around_schools_months_graphs_data_api, methods=["GET"])


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


app.add_url_rule("/markers/<int:marker_id>", endpoint=None, view_func=marker, methods=["GET"])
app.add_url_rule("/markers/all", endpoint=None, view_func=marker_all, methods=["GET"])


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


app.add_url_rule("/clusters", endpoint=None, view_func=clusters, methods=["GET"])


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


@app.before_first_request
def read_dictionaries():
    for directory in sorted(glob.glob("{0}/{1}/*/*".format(app.static_folder, 'data/cbs')), reverse=True):
        main_dict = dict(get_dict_file(directory))
        if len(main_dict) == 0:
            return
        if len(main_dict) == 1:
            for _, df in main_dict['Dictionary'].iterrows():
                if type(df[DICTCOLUMN3]) is not (int or float):
                    global_cbs_dictionary[(int(df[DICTCOLUMN1]), int(df[DICTCOLUMN2]))] = df[DICTCOLUMN3]
                else:
                    global_cbs_dictionary[(int(df[DICTCOLUMN1]), int(df[DICTCOLUMN2]))] = int(df[DICTCOLUMN3])
            return


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
