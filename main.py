# -*- coding: utf-8 -*-
import os
import csv
from StringIO import StringIO
import time

import jinja2
from flask import make_response, render_template, Response, jsonify, url_for, flash
import flask.ext.assets
from webassets.ext.jinja2 import AssetsExtension
from webassets import Environment as AssetsEnvironment
from flask.ext.babel import Babel,gettext
from clusters_calculator import retrieve_clusters

from database import db_session
from models import *
from base import *
import utilities
from constants import *

from wtforms import form, fields, validators, StringField, PasswordField, Form
import flask_admin as admin
import flask.ext.login as login
from flask_admin.contrib import sqla
from flask_admin import helpers, expose, BaseView
from werkzeug.security import check_password_hash
from sendgrid import sendgrid, SendGridClientError, SendGridServerError, Mail
import glob
from utilities import CsvReader
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.security import Security, SQLAlchemyUserDatastore, roles_required, current_user, LoginForm
from collections import OrderedDict
from sqlalchemy import distinct, func
from apscheduler.scheduler import Scheduler
import united
from flask.ext.compress import Compress
import argparse
from oauth import OAuthSignIn

app = utilities.init_flask(__name__)
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

assets = flask.ext.assets.Environment()
assets.init_app(app)
sg = sendgrid.SendGridClient(app.config['SENDGRID_USERNAME'], app.config['SENDGRID_PASSWORD'], raise_errors=True)

assets_env = AssetsEnvironment('./static/', '/static')

babel = Babel(app)

jinja_environment = jinja2.Environment(
    autoescape=True,
    loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), "templates")),
    extensions=[AssetsExtension])
jinja_environment.assets_environment = assets_env

MINIMAL_ZOOM = 16
SESSION_HIGHLIGHTPOINT_KEY = 'gps_highlightpoint_created'

DICTIONARY = "Dictionary"
DICTCOLUMN1 = "MS_TAVLA"
DICTCOLUMN2 = "KOD"
DICTCOLUMN3 = "TEUR"
lms_dict_files = {DICTIONARY: "Dictionary.csv"}
content_encoding = 'cp1255'

Compress(app)

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


def generate_json(accidents, discussions, is_thin):
    markers = accidents.all()
    if not is_thin:
        markers += discussions.all()
    yield '{"markers": ['
    is_first = True
    for marker in markers:
        if is_first:
            is_first = False
            prefix = ''
        else:
            prefix = ','
        yield prefix + json.dumps(marker.serialize(is_thin))
    yield ']}'


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
        if type(v) is unicode else v
               for k, v in serialized.iteritems()}
        output.writerow(row)
        yield output_file.getvalue()
        output_file.truncate(0)

ARG_TYPES = {'ne_lat': (float, 32.072427482938345), 'ne_lng': (float, 34.79928962966915),
             'sw_lat': (float, 34.79928962966915), 'sw_lng': (float, 34.78877537033077), 'zoom': (int, 17),
             'show_fatal': (bool, True), 'show_severe': (bool, True), 'show_light': (bool, True),
             'approx': (bool, True), 'accurate': (bool, True), 'show_markers': (bool, True),
             'show_discussions': (bool, True), 'show_urban': (int, 3), 'show_intersection': (int, 3),
             'show_lane': (int, 3), 'show_day': (int, 0), 'show_holiday': (int, 0),  'show_time': (int, 24),
             'start_time': (int, 25), 'end_time': (int, 25), 'weather': (int, 0), 'road': (int, 0),
             'separation': (int, 0), 'surface': (int, 0), 'acctype': (int, 0), 'controlmeasure': (int, 0),
             'district': (int, 0), 'case_type': (int, 0)}

def get_kwargs():
    kwargs = {arg: arg_type(request.values.get(arg, default_value)) for (arg, (arg_type, default_value)) in ARG_TYPES.iteritems()}
    kwargs.update({arg: datetime.date.fromtimestamp(int(request.values[arg])) for arg in ('start_date', 'end_date')})
    return kwargs

@babel.localeselector
def get_locale():
    lang = request.values.get('lang')
    if lang is None:
        return request.accept_languages.best_match(app.config['LANGUAGES'].keys())
    else:
        return lang

@app.route("/markers", methods=["GET"])
@user_optional
def markers():
    logging.debug('getting markers')
    kwargs = get_kwargs()
    logging.debug('querying markers in bounding box')
    is_thin = (kwargs['zoom'] < MINIMAL_ZOOM)
    accidents = Marker.bounding_box_query(is_thin, yield_per=50, **kwargs)

    discussion_args = ('ne_lat', 'ne_lng', 'sw_lat', 'sw_lng', 'show_discussions')
    discussions = DiscussionMarker.bounding_box_query(**{arg: kwargs[arg] for arg in discussion_args})

    if request.values.get('format') == 'csv':
        date_format = '%Y-%m-%d'
        return Response(generate_csv(accidents), headers={
            "Content-Type": "text/csv",
            "Content-Disposition": 'attachment; '
                                   'filename="Anyway-accidents-from-{0}-to-{1}.csv"'
                        .format(kwargs["start_date"].strftime(date_format), kwargs["end_date"].strftime(date_format))
        })

    else: # defaults to json
        return Response(generate_json(accidents, discussions, 
                                      is_thin),
                        mimetype="application/json")

@app.route("/markers/<int:marker_id>", methods=["GET"])
def marker(marker_id):
    involved = db_session.query(Involved).filter(Involved.accident_id == marker_id)
    vehicles = db_session.query(Vehicle).filter(Vehicle.accident_id == marker_id)
    list_to_return = list()
    for inv in involved:
        obj = inv.serialize()
        obj["age_group"] = lms_dictionary.get((92, obj["age_group"]))
        obj["population_type"] = lms_dictionary.get((66, obj["population_type"]))
        obj["home_district"] = lms_dictionary.get((77, obj["home_district"]))
        obj["home_nafa"] = lms_dictionary.get((79, obj["home_nafa"]))
        obj["home_area"] = lms_dictionary.get((80, obj["home_area"]))
        obj["home_municipal_status"] = lms_dictionary.get((78, obj["home_municipal_status"]))
        obj["home_residence_type"] = lms_dictionary.get((81, obj["home_residence_type"]))
        list_to_return.append(obj)

    for veh in vehicles:
        obj = veh.serialize()
        obj["engine_volume"] = lms_dictionary.get((111, obj["engine_volume"]))
        obj["total_weight"] = lms_dictionary.get((112, obj["total_weight"]))
        obj["driving_directions"] = lms_dictionary.get((28, obj["driving_directions"]))
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
                marker = db_session.query(DiscussionMarker)\
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


@app.route("/clusters")
@user_optional
def clusters(methods=["GET"]):
    start_time = time.time()
    if request.method == "GET":
        kwargs = get_kwargs()
        results = retrieve_clusters(**kwargs)

        logging.debug('calculating clusters took %f seconds' % (time.time() - start_time))
        return Response(json.dumps({'clusters': results}), mimetype="application/json")

@app.route("/highlightpoints", methods=['POST'])
@user_optional
def highlightpoint():
    highlight = parse_data(HighlightPoint, get_json_object(request))
    if highlight is None:
        log_bad_request(request)
        return make_response("")

    # if it's a user gps type (user location), only handle a single post request per session
    if int(highlight.type) == HighlightPoint.HIGHLIGHT_TYPE_USER_GPS:
        if not SESSION_HIGHLIGHTPOINT_KEY in session:
            session[SESSION_HIGHLIGHTPOINT_KEY] = "saved"
        else:
            return make_response("")

    return make_response(post_handler(highlight))

# Post handler for a generic REST API
def post_handler(obj):
    try:
        db_session.add(obj)
        db_session.commit()
        return jsonify(obj.serialize())
    except Exception as e:
        logging.debug("could not handle a post for object:{0}, error:{1}".format(obj, e.message))
        return ""

# Safely parsing an object
# cls: the ORM Model class that implement a parse method
def parse_data(cls, data):
    try:
        return cls.parse(data) if data is not None else None
    except Exception as e:
        logging.debug("Could not parse the requested data, for class:{0}, data:{1}. Error:{2}".format(cls, data, e.message))
        return

def get_json_object(request):
    try:
        return request.get_json(force=True)
    except Exception as e:
        logging.debug("Could not get json from a request. request:{0}. Error:{1}".format(request, e.message))
        return

def log_bad_request(request):
    try:
        logging.debug("Bad {0} Request over {1}. Values: {2} {3}".format(request.method, request.url, request.form, request.args))
    except AttributeError:
        logging.debug("Bad request:{0}".format(str(request)))


@app.route('/')
def index(marker=None, message=None):
    context = {'minimal_zoom': MINIMAL_ZOOM, 'url': request.base_url, 'index_url': request.url_root}
    if 'marker' in request.values:
        markers = Marker.get_marker(request.values['marker'])
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
    for attr in 'approx', 'accurate', 'show_markers', 'show_discussions', 'show_urban', 'show_intersection', 'show_lane',\
                'show_day', 'show_holiday', 'show_time', 'start_time', 'end_time', 'weather', 'road', 'separation',\
                'surface', 'acctype', 'controlmeasure', 'district', 'case_type', 'show_fatal', 'show_severe', 'show_light':
        value = request.values.get(attr)
        if value is not None:
            context[attr] = value or '-1'
    if message:
        context['message'] = message
    return render_template('index.html', **context)


def string2timestamp(s):
    return time.mktime(datetime.datetime.strptime(s, "%Y-%m-%d").timetuple())


def year2timestamp(y):
    return time.mktime(datetime.date(y, 1, 1).timetuple())

@app.route("/new-features", methods=["POST"])
def updatebyemail():
    jsonData = request.get_json(force=True)
    emailaddress = str(jsonData['address'])
    fname = (jsonData['fname']).encode("utf8")
    lname = (jsonData['lname']).encode("utf8")

    if len(fname)>40:
        return  jsonify(respo='First name to long')
    if len(lname)>40:
        return  jsonify(respo='Last name to long')
    if len(emailaddress)>40:
        return jsonify(respo='Email too long', emailaddress = emailaddress)
    user_exists = db_session.query(User).filter(User.email == emailaddress)
    if user_exists.count()==0:
        user = User(email = emailaddress, first_name = fname.decode("utf8"), last_name = lname.decode("utf8"), new_features_subscription=True)
        db_session.add(user)
        db_session.commit()
        return jsonify(respo='Subscription saved', )
    else:
        user_exists = user_exists.first()
        if user_exists.new_features_subscription==False:
            user_exists.new_features_subscription = True
            db_session.add(user_exists)
            db_session.commit()
            return jsonify(respo='Subscription saved', )
        else:
            return jsonify(respo='Subscription already exist')

@app.route("/preferences", methods=('GET', 'POST'))
def update_preferences():
    if not current_user.is_authenticated:
        return jsonify(respo='user not authenticated')
    cur_id = current_user.get_id()
    cur_user = db_session.query(User).filter(User.id == cur_id).first()
    if cur_user is None:
        return jsonify(respo='user not found')
    cur_report_preferences = db_session.query(ReportPreferences).filter(User.id == cur_id).first()
    if request.method == "GET":
        if cur_report_preferences is None:
            return jsonify(lat='', lon='', distance='', accident_severity='0', history_report=False)
        else:
            return jsonify(lat=cur_report_preferences.latitude, lon=cur_report_preferences.longitude, distance=cur_report_preferences.radius, \
                accident_severity=cur_report_preferences.minimum_severity, history_report=cur_report_preferences.historical_report)
    else:
        jsonData = request.get_json(force=True)    
        lat = jsonData['lat']
        lon = jsonData['lon']
        distance = jsonData['distance']
        accident_severity = jsonData['accident_severity']
        history_report = jsonData['history_report']
    
        cur_general_preferences = db_session.query(GeneralPreferences).filter(User.id == cur_id).first()
        if cur_general_preferences is None:
            general_pref = GeneralPreferences(user_id = cur_id, minimum_displayed_severity = accident_severity)
            db_session.add(general_pref)
            db_session.commit()
        else:
            cur_general_preferences.minimum_displayed_severity = accident_severity  
            db_session.add(cur_general_preferences)
            db_session.commit()
    
        if cur_report_preferences is None:
            report_pref = ReportPreferences(user_id = cur_id, line_number=1,historical_report=history_report,\
                latitude=lat,longitude=lon, radius=distance, minimum_severity=accident_severity)
            db_session.add(report_pref)
            db_session.commit()
        else:
            cur_report_preferences.historical_report = history_report  
            cur_report_preferences.latitude = lat  
            cur_report_preferences.longitude = lon  
            cur_report_preferences.radius = distance  
            cur_report_preferences.minimum_severity = accident_severity  
            db_session.add(cur_general_preferences)
            db_session.commit()
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
        return db_session.query(User).filter_by(username=self.username.data).first()


class RegistrationForm(form.Form):
    username = fields.StringField(validators=[validators.required()])
    email = fields.StringField()
    password = fields.PasswordField(validators=[validators.required()])

    def validate_login(self, field):
        if db_session.query(User).filter_by(username=self.username.data).count() > 0:
            raise validators.ValidationError('Duplicate username')


def init_login():
    login_manager = login.LoginManager()
    login_manager.init_app(app)

    # Create user loader function
    @login_manager.user_loader
    def load_user(user_id):
        return db_session.query(User).get(user_id)


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
        #link = '<p>Don\'t have an account? <a href="' + url_for('.register_view') + '">Click here to register.</a></p>'
        self._template_args['form'] = form
        #self._template_args['link'] = link
        return super(AdminIndexView, self).index()

    # @expose('/register/', methods=('GET', 'POST'))
    # def register_view(self):
    #    form = RegistrationForm(request.form)
    #    if helpers.validate_form_on_submit(form):
    #        user = User()
    #
    #        form.populate_obj(user)
    #        # we hash the users password to avoid saving it as plaintext in the db,
    #        # remove to use plain text:
    #        user.password = generate_password_hash(form.password.data)
    #        user.is_admin = True
    #
    #        db_session.add(user)
    #        db_session.commit()
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
        if request.method=='GET':
            user_emails = db_session.query(User).filter(User.new_features_subscription == True)
            email_list = []
            for user in user_emails:
                email_list.append(user.email)
                email_list.append(';')
            context = {'user_emails': email_list}
            return self.render('sendemail.html', **context)
        else:
            jsondata = request.get_json(force=True)
            users_send_email_to = db_session.query(User).filter(User.new_features_subscription == True)
            message = Mail()
            message.set_subject(jsondata['subject'].encode("utf8"))
            message.set_text(jsondata['message'].encode("utf8"))
            message.set_from('ANYWAY Team <feedback@anyway.co.il>')
            for user in users_send_email_to:
                message.add_bcc(user.email)
            try:
                status, msg = sg.send(message)
            except SendGridClientError:
                return "Error occurred while trying to send the emails"
            except SendGridServerError:
                return "Error occurred while trying to send the emails"
            return "Email/s Sent"

    def is_visible(self):
        return login.current_user.is_authenticated

class ViewHighlightedMarkersData(BaseView):
    @roles_required('admin')
    @expose('/')
    def index(self):
        highlightedpoints = db_session.query(HighlightPoint).options(load_only("id", "latitude", "longitude", "type"))
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
           user = User(username = formAccount.username.data, password = formAccount.password.data)
           role = db_session.query(Role).filter(Role.id==2).first()
           user.roles.append(role)
           db_session.add(user)
           db_session.commit()
           flash('The user was created successfully')
       return self.render('open_account.html', form=formAccount)

    def is_visible(self):
        return login.current_user.is_authenticated


init_login()

admin = admin.Admin(app, 'ANYWAY Administration Panel', index_view=AdminIndexView(), base_template='admin_master.html')

admin.add_view(AdminView(User, db_session, name='Users', endpoint='AllUsers', category='Users'))
admin.add_view(OpenNewOrgAccount(name='Open new organization account', endpoint='OpenAccount', category='Users'))
admin.add_view(SendToSubscribersView(name='Send To Subscribers'))
admin.add_view(ViewHighlightedMarkersData(name='View Highlighted Markers Data', endpoint='ViewHighlightedMarkersData', category='View Highlighted Markers'))
admin.add_view(ViewHighlightedMarkersMap(name='View Highlighted Markers Map', endpoint='ViewHighlightedMarkersMap', category='View Highlighted Markers'))

lms_dictionary = {}

@app.before_first_request
def read_dictionaries():
    global lms_dictionary
    for directory in sorted(glob.glob("{0}/{1}/*/*".format(app.static_folder, 'data/lms')),reverse=True):
        main_dict = dict(get_dict_file(directory))
        if len(main_dict) == 0:
            return
        if len(main_dict) == 1:
            for dic in main_dict['Dictionary']:
                if type(dic[DICTCOLUMN3]) is str:
                    lms_dictionary[(int(dic[DICTCOLUMN1]),int(dic[DICTCOLUMN2]))] = dic[DICTCOLUMN3].decode(content_encoding)
                else:
                    lms_dictionary[(int(dic[DICTCOLUMN1]),int(dic[DICTCOLUMN2]))] = int(dic[DICTCOLUMN3])
            return


def get_dict_file(directory):
    for name, filename in lms_dict_files.iteritems():
        files = filter(lambda path: filename.lower() in path.lower(), os.listdir(directory))
        amount = len(files)
        if amount == 0:
            raise ValueError("file not found: " + filename + " in directory " + directory)
        if amount > 1:
            raise ValueError("there are too many matches: " + filename)
        csv = CsvReader(os.path.join(directory, files[0]))
        yield name, csv

class ExtendedLoginForm(LoginForm):
    username = StringField('User Name', [validators.DataRequired()])

    def validate(self):
        if not super(LoginForm, self).validate():
            return False
        if self.username.data.strip() == '':
            return False
        self.user = db_session.query(User).filter(User.username==self.username.data).first()
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
            return  make_response("Unauthorized User")
    else:
        return redirect('/login')


def get_current_user_first_name():
     cur_id = current_user.get_id()
     cur_user = db_session.query(User).filter(User.id == cur_id).first()
     if cur_user is not None:
        return cur_user.first_name
     return "User"

def year_range(year):
    return ["01/01/%d" % year, "31/12/%d" % year]


######## rauth integration (login through facebook) ##################

@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

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
        user=User.query.filter_by(email=email).first()
        if not user:
            user = User(nickname=username, email=email, provider=provider)
            db.session.add(user)
            db.session.commit()
    else: #facebook authentication
        social_id, username, email = oauth.callback()
        if social_id is None:
            flash('Authentication failed.')
            return redirect(url_for('index'))
        user = User.query.filter_by(social_id=social_id).first()
        if not user:
            user = User(social_id=social_id, nickname=username, email=email, provider=provider)
            db.session.add(user)
            db.session.commit()
    login.login_user(user, True)
    return redirect(url_for('index'))

######## end rauth integration

@app.before_first_request
def create_years_list():
    """
    Edits 'years.js', a years structure ready to be presented in app.js
    as user's last-4-years filter choices.
    """
    while True:
        try:
            year_col = db.session.query(distinct(func.extract("year", Marker.created)))
            break
        except OperationalError:
            time.sleep(1)

    years = OrderedDict([("שנת" + " %d" % year, year_range(year))
                         for year in sorted(year_col, reverse=True)[:4]])
    years_file = os.path.join(app.static_folder, 'js/years.js')
    with open(years_file, 'w') as outfile:
        outfile.write("var ACCYEARS = ")
        json.dump(years, outfile, encoding='utf-8')
        outfile.write(";\n")
    logging.debug("wrote '%s'" % years_file)
    logging.debug("\n".join("\t{0}: {1}".format(k, str(v)) for k, v in years.items()))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--open', action='store_true', help='Open broadcasting to all local IPs')
    args = parser.parse_args()

    sched = Scheduler()

    @sched.interval_schedule(hours=12)
    def scheduled_import():
        united.main()
    sched.start()

    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s')

    if not args.open:
        app.run(debug=True)
    else:
        app.run(debug=True, host='0.0.0.0')
