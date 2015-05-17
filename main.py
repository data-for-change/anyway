import os
import logging
import urllib
import csv
from StringIO import StringIO
import datetime
import time

import jinja2
from flask import make_response, jsonify, render_template, Response, url_for
import flask.ext.assets
from webassets.ext.jinja2 import AssetsExtension
from webassets import Environment as AssetsEnvironment


from database import db_session
from models import *
from base import *
import utilities

from wtforms import form, fields, validators
import flask_admin as admin
import flask_login as login
from flask_admin.contrib import sqla
from flask_admin import helpers, expose, BaseView
from werkzeug.security import generate_password_hash, check_password_hash

app = utilities.init_flask(__name__)
assets = flask.ext.assets.Environment()
assets.init_app(app)

assets_env = AssetsEnvironment('./static/', '/static')
jinja_environment = jinja2.Environment(
    autoescape=True,
    loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), "templates")),
    extensions=[AssetsExtension])
jinja_environment.assets_environment = assets_env

MINIMAL_ZOOM = 16

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

    logging.debug('querying markers in bounding box')
    is_thin = (zoom < MINIMAL_ZOOM)
    accidents = Marker.bounding_box_query(ne_lat, ne_lng, sw_lat, sw_lng,
                                          start_date, end_date,
                                          fatal, severe, light, inaccurate,
                                          is_thin, yield_per=50)
    discussions = DiscussionMarker.bounding_box_query(ne_lat, ne_lng,
                                                      sw_lat, sw_lng)
    if request.values.get('format') == 'csv':
        return Response(generate_csv(accidents), headers={
            "Content-Type": "text/csv",
            "Content-Disposition": 'attachment; filename="data.csv"'
        })

    else: # defaults to json
        return Response(generate_json(accidents, discussions, 
                                      is_thin),
                        mimetype="application/json")

@app.route("/markers/(.*)", methods=["GET"])
@user_required
def marker(self, key_name):
    marker = Marker.get_by_key_name(key_name)
    return make_response(json.dumps(marker.serialize(self.user)))

@app.route("/discussion", methods=["GET", "POST"])
@user_optional
def discussion():
    if request.method == "GET":
        # TODO get DiscussionMarker by request.values["lat"] and request.values["lon"] and pass to index()
        return index()
    else:
        marker = DiscussionMarker.parse(request.get_json(force=True))
        db_session.add(marker)
        db_session.commit()
        return make_response(json.dumps(marker.serialize()))

@app.route('/')
def index(marker=None):
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
    for attr in 'show_fatal', 'show_severe', 'show_light', 'show_inaccurate',\
                'zoom':
        if attr in request.values:
            context[attr] = request.values[attr]
    if 'map_only' in request.values:
        if request.values['map_only'] in ('1', 'true'):
            context['map_only'] = 1
    if 'lat' in request.values and 'lon' in request.values:
        context['coordinates'] = (request.values['lat'], request.values['lon'])
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

        if not check_password_hash(user.password, self.password.data):
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
    #    return super(MyAdminIndexView, self).index()

    @expose('/logout/')
    def logout_view(self):
        login.logout_user()
        return redirect(url_for('.index'))

class SendToSubscribersView(BaseView):
    @login.login_required
    @expose('/')
    def index(self):
        return self.render('sendemail.html')

    def is_visible(self):
        return login.current_user.is_authenticated()


init_login()

admin = admin.Admin(app, 'Anyway Administration Panel', index_view=AdminIndexView(), base_template='admin_master.html')

admin.add_view(AdminView(User, db_session))
admin.add_view(SendToSubscribersView(name='Send To Subscribers'))

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s')
    app.run(debug=True)


