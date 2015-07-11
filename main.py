# -*- coding: utf-8 -*-
import os
import urllib
import logging
import csv
from StringIO import StringIO
import time

import jinja2
from flask import make_response, render_template, Response, jsonify, url_for
import flask.ext.assets
from webassets.ext.jinja2 import AssetsExtension
from webassets import Environment as AssetsEnvironment
from clusters_calculator import retrieve_clusters

from database import db_session
from models import *
from base import *
import utilities
from constants import *

from wtforms import form, fields, validators
import flask_admin as admin
import flask.ext.login as login
from flask_admin.contrib import sqla
from flask_admin import helpers, expose, BaseView
from werkzeug.security import check_password_hash
from sendgrid import sendgrid, SendGridClientError, SendGridServerError, Mail
import argparse
import glob
from utilities import CsvReader
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.principal import Principal, Permission, RoleNeed
from flask.ext.security import Security, SQLAlchemyUserDatastore, \
     UserMixin, RoleMixin
from collections import OrderedDict
from sqlalchemy import distinct, func


app = utilities.init_flask(__name__)
db = SQLAlchemy(app)
app = utilities.init_flask(__name__)
app.config.from_object(__name__)

assets = flask.ext.assets.Environment()
assets.init_app(app)
sg = sendgrid.SendGridClient(app.config['SENDGRID_USERNAME'], app.config['SENDGRID_PASSWORD'], raise_errors=True)

assets_env = AssetsEnvironment('./static/', '/static')
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


@app.route("/markers", methods=["GET"])
@user_optional
def markers():
    logging.debug('getting markers')
    ne_lat = float(request.values['ne_lat'])
    ne_lng = float(request.values['ne_lng'])
    sw_lat = float(request.values['sw_lat'])
    sw_lng = float(request.values['sw_lng'])
    zoom = int(request.values['zoom'])
    start_date = datetime.date.fromtimestamp(int(request.values['start_date']))
    end_date = datetime.date.fromtimestamp(int(request.values['end_date']))
    fatal = int(request.values['show_fatal'])
    severe = int(request.values['show_severe'])
    light = int(request.values['show_light'])
    inaccurate = int(request.values['show_inaccurate'])
    show_markers = bool(request.values['show_markers'])
    show_discussions = bool(request.values['show_discussions'])

    logging.debug('querying markers in bounding box')
    is_thin = (zoom < MINIMAL_ZOOM)
    accidents = Marker.bounding_box_query(ne_lat, ne_lng, sw_lat, sw_lng,
                                          start_date, end_date,
                                          fatal, severe, light, inaccurate,
                                          show_markers, is_thin, yield_per=50)
    discussions = DiscussionMarker.bounding_box_query(ne_lat, ne_lng,
                                                      sw_lat, sw_lng, show_discussions)
    if request.values.get('format') == 'csv':
        return Response(generate_csv(accidents), headers={
            "Content-Type": "text/csv",
            "Content-Disposition": 'attachment; filename="data.csv"'
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
        if (92,obj["age_group"]) in lmsDictionary:
            obj["age_group"] = lmsDictionary[92,obj["age_group"]]
        if (66,obj["population_type"]) in lmsDictionary:
            obj["population_type"] = lmsDictionary[66,obj["population_type"]]
        if (77,obj["home_district"]) in lmsDictionary:
            obj["home_district"] = lmsDictionary[77,obj["home_district"]]
        if (79,obj["home_nafa"]) in lmsDictionary:
            obj["home_nafa"] = lmsDictionary[79,obj["home_nafa"]]
        if (80,obj["home_area"]) in lmsDictionary:
            obj["home_area"] = lmsDictionary[80,obj["home_area"]]
        if (78,obj["home_municipal_status"]) in lmsDictionary:
            obj["home_municipal_status"] = lmsDictionary[78,obj["home_municipal_status"]]
        if (81,obj["home_residence_type"]) in lmsDictionary:
            obj["home_residence_type"] = lmsDictionary[81,obj["home_residence_type"]]
        list_to_return.append(obj)
    for veh in vehicles:
        obj = veh.serialize()
        if (111,obj["engine_volume"]) in lmsDictionary:
            obj["engine_volume"] = lmsDictionary[111,obj["engine_volume"]]
        if (112,obj["total_weight"]) in lmsDictionary:
            obj["total_weight"] = lmsDictionary[112,obj["total_weight"]]
        list_to_return.append(obj)
    return make_response(json.dumps(list_to_return, ensure_ascii=False))


@app.route("/discussion", methods=["GET", "POST"])
@user_optional
def discussion():
    if request.method == "GET":
        try:
            marker = db_session.query(DiscussionMarker)\
                .filter(DiscussionMarker.identifier == \
                        request.values['identifier']).first()
            context = {'identifier': marker.identifier, 'title': marker.title}
            return render_template('disqus.html', **context)
        except AttributeError:
            return index(message=u"הדיון לא נמצא: " + request.values['identifier'])
        except KeyError:
            return index(message=u"דיון לא חוקי")
    else:
        marker = parse_data(DiscussionMarker, get_json_object(request))
        if marker is None:
            log_bad_request(request)
            return make_response("")
        return make_response(post_handler(marker))

@app.route("/follow/(.*)")
@user_required
def follow(key_name):
    marker = Marker.get_by_key_name(key_name)
    follower = Follower.all().filter("marker", marker).filter("user", self.user).get()
    if not follower:
        Follower(parent=marker, marker=marker, user=self.user).put()


@app.route("/unfollow/(.*)")
@user_required
def unfollow(key_name):
    marker = Marker.get_by_key_name(key_name)
    follower = Follower.all().filter("marker", marker).filter("user", self.user).get()
    if follower:
        follower.delete()


@app.route("/clusters")
@user_optional
def clusters(methods=["GET"]):
    start_time = time.time()
    if request.method == "GET":
        ne_lat = float(request.values['ne_lat'])
        ne_lng = float(request.values['ne_lng'])
        sw_lat = float(request.values['sw_lat'])
        sw_lng = float(request.values['sw_lng'])
        start_date = datetime.date.fromtimestamp(int(request.values['start_date']))
        end_date = datetime.date.fromtimestamp(int(request.values['end_date']))
        fatal = int(request.values['show_fatal'])
        severe = int(request.values['show_severe'])
        light = int(request.values['show_light'])
        inaccurate = int(request.values['show_inaccurate'])
        zoom = int(request.values['zoom'])

        results = retrieve_clusters(ne_lat, ne_lng, sw_lat, sw_lng,
                                    start_date, end_date,
                                    fatal, severe, light, inaccurate, zoom)

        logging.debug('calculating clusters took ' + str(time.time() - start_time))
        return Response(json.dumps({'clusters': results}), mimetype="application/json")

@app.route('/', defaults={'marker_id': None})
@app.route('/<int:marker_id>')
def main(marker_id):
    # at this point the marker id is just a running number, and the
    # LMS is in the description and needs to be promoted to a DB
    # field so we can query it. We also need to add a provider id.
    context = {'minimal_zoom': MINIMAL_ZOOM}
    marker = None

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
    context = {'minimal_zoom': MINIMAL_ZOOM, 'url': request.base_url}
    if 'marker' in request.values:
        markers = Marker.get_marker(request.values['marker'])
        if markers.count() == 1:
            marker = markers[0]
            context['coordinates'] = (marker.latitude, marker.longitude)
            context['marker'] = marker.id
    if 'start_date' in request.values:
        context['start_date'] = string2timestamp(request.values['start_date'])
    elif marker:
        context['start_date'] = year2timestamp(marker.created.year)
    if 'end_date' in request.values:
        context['end_date'] = string2timestamp(request.values['end_date'])
    elif marker:
        context['end_date'] = year2timestamp(marker.created.year + 1)
    for attr in 'show_fatal', 'show_severe', 'show_light', 'show_inaccurate', \
                'zoom':
        if attr in request.values:
            context[attr] = request.values[attr]
    if 'map_only' in request.values:
        if request.values['map_only'] in ('1', 'true'):
            context['map_only'] = 1
    if 'lat' in request.values and 'lon' in request.values:
        context['coordinates'] = (request.values['lat'], request.values['lon'])
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
            return jsonify(respo='Subscription already exist', )


class LoginForm(form.Form):
    login = fields.TextField(validators=[validators.required()])
    password = fields.PasswordField(validators=[validators.required()])

    def validate_login(self, field):
        user = self.get_user()

        if user is None:
            raise validators.ValidationError('Invalid user')

        if not check_password_hash(user.password.encode("utf8"), self.password.data.encode("utf8")):
            raise validators.ValidationError('Invalid password')

    def get_user(self):
        return db_session.query(User).filter_by(login=self.login.data).first()


class RegistrationForm(form.Form):
    login = fields.TextField(validators=[validators.required()])
    email = fields.TextField()
    password = fields.PasswordField(validators=[validators.required()])

    def validate_login(self, field):
        if db_session.query(User).filter_by(login=self.login.data).count() > 0:
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
        return login.current_user.is_authenticated()


class AdminIndexView(admin.AdminIndexView):

    @expose('/')
    def index(self):
        if not login.current_user.is_authenticated():
            return redirect(url_for('.login_view'))
        return super(AdminIndexView, self).index()

    @expose('/login/', methods=('GET', 'POST'))
    def login_view(self):
        # handle user login
        form = LoginForm(request.form)
        if helpers.validate_form_on_submit(form):
            user = form.get_user()
            login.login_user(user)

        if login.current_user.is_authenticated():
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
    @login.login_required
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
        return login.current_user.is_authenticated()

class ViewHighlightedMarkers(BaseView):
    @login.login_required
    @expose('/')
    def index(self):
        highlightedpoints = db_session.query(HighlightPoint).options(load_only("id", "latitude", "longitude", "type"))
        points = []
        point_id_list = []
        for point in highlightedpoints:
            p = HighlightPoint()
            p.id = point.id
            p.latitude = point.latitude
            p.longitude = point.longitude
            p.created = point.created
            p.type = point.type
            points.append(p)
        context = {'points': points}
        return self.render('viewhighlighted.html', **context)

    def is_visible(self):
        return login.current_user.is_authenticated()


init_login()

admin = admin.Admin(app, 'ANYWAY Administration Panel', index_view=AdminIndexView(), base_template='admin_master.html')

admin.add_view(AdminView(User, db_session))
admin.add_view(SendToSubscribersView(name='Send To Subscribers'))
admin.add_view(ViewHighlightedMarkers(name='View Highlighted Markers'))


lmsDictionary = {}
def ReadDictionaries():
    global lmsDictionary
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', type=str, default="static/data/lms")
    args = parser.parse_args()
    for directory in glob.glob("{0}/*/*".format(args.path)):
        mainDict = dict(get_dict_file(directory))
        if len(mainDict) == 0:
            return
        elif len(mainDict) == 1:
            for dic in mainDict['Dictionary']:
                if type(dic[DICTCOLUMN3]) is str:
                    lmsDictionary[(int(dic[DICTCOLUMN1]),int(dic[DICTCOLUMN2]))] = dic[DICTCOLUMN3].decode(content_encoding)
                else:
                    lmsDictionary[(int(dic[DICTCOLUMN1]),int(dic[DICTCOLUMN2]))] = int(dic[DICTCOLUMN3])
            return


def get_dict_file(directory):
    for name, filename in lms_dict_files.iteritems():

        if name not in [DICTIONARY]:
            continue
        files = filter(lambda path: filename.lower() in path.lower(), os.listdir(directory))
        amount = len(files)
        if amount == 0:
            raise ValueError("file not found in directory: " + filename)
        if amount > 1:
            raise ValueError("there are too many matches: " + filename)
        csv = CsvReader(os.path.join(directory, files[0]))
        if name == DICTIONARY:
            yield name, csv


user_datastore = SQLAlchemyUserDatastore(SQLAlchemy(app), User, Role)
security = Security(app, user_datastore)
principals = Principal(app)

@app.route('/testroles')
@login_required
def TestLogin():
   return render_template('testroles.html')

@app.route('/login/', methods=['GET', 'POST'])
def login2():
    if request.method == "POST":
        uname = request.values["username"]
        passw = request.values["password"]
        users_query = db_session.query(User).filter(User.login==uname).first()
        if users_query is not None:
            if check_password_hash(users_query.password, passw):
                login.login_user(users_query)

    if login.current_user.is_authenticated():
        return render_template('index.html')
    else:
        return render_template('login.html')


def year_range(year):
    return ["01/01/%s" % year, "31/12/%s" % year]

def create_years_list():
    """
    Edits 'years.js', a years structure ready to be presented in app.js
    as user's last-4-years filter choices.
    """
    year_col = db.session.query(distinct(func.extract("year", Marker.created)))
    years = OrderedDict({"שנת" + " %s" % year: year_range(year)
                         for year in sorted(year_col[:4], reverse=True)})
    with open('static/js/years.js', 'w') as outfile:
        outfile.write("var ACCYEARS = ")
        json.dump(years, outfile, encoding='utf-8')
        outfile.write(";\n")

create_years_list()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s')
    ReadDictionaries()
    app.run(debug=True)



