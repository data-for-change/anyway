import os
import logging
import urllib
import csv
from StringIO import StringIO
import datetime
import time

import jinja2
from flask import make_response, jsonify, render_template, Response
import flask.ext.assets
from webassets.ext.jinja2 import AssetsExtension
from webassets import Environment as AssetsEnvironment



from database import db_session
from models import *
from base import *
import utilities


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


def generate_json(results, is_thin):
    yield '{"markers": ['
    is_first = True
    for marker in results.all():
        if is_first:
            is_first = False
            prefix = ''
        else:
            prefix = ','
        yield prefix + json.dumps(marker.serialize(is_thin))
    yield ']}'


def generate_csv(results, is_thin):
    output_file = StringIO()
    yield output_file.getvalue()
    output_file.truncate(0)
    output = None
    for marker in results.all():
        serialized = marker.serialize(is_thin)
        if not output:
            output = csv.DictWriter(output_file, serialized.keys())
            output.writeheader()

        row = {k: v.encode('utf8')
               if type(v) is unicode else v
               for k, v in serialized.iteritems()}
        output.writerow(row)
        yield output_file.getvalue()
        output_file.truncate(0)


@app.route("/markers")
@user_optional
def markers(methods=["GET", "POST"]):
    logging.debug('getting markers')
    if request.method == "GET":
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
        results = Marker.bounding_box_query(ne_lat, ne_lng, sw_lat, sw_lng,
                                            start_date, end_date,
                                            fatal, severe, light, inaccurate,
                                            is_thin, yield_per=50)
        if request.values.get('format') == 'csv':
            return Response(generate_csv(results, is_thin), headers={
                "Content-Type": "text/csv",
                "Content-Disposition": 'attachment; filename="data.csv"'
            })

        else: # defaults to json
            return Response(generate_json(results, is_thin), mimetype="application/json")

    else:
        data = json.loads(self.request.body)
        marker = Marker.parse(data)
        marker.user = self.user
        marker.update_location()
        marker.put()
        return make_response(json.dumps(marker.serialize(self.user)))

@app.route("/markers/(.*)", methods=["GET", "PUT", "DELETE"])
@user_required
def marker(self, key_name):
    if request.method == "GET":
        marker = Marker.get_by_key_name(key_name)
        return make_response(json.dumps(marker.serialize(self.user)))

    elif request.method == "PUT":
        marker = Marker.get_by_key_name(key_name)
        data = json.loads(self.request.body)
        marker.update(data, self.user)
        return make_response(json.dumps(marker.serialize(self.user)))

    elif request.method == "DELETE":
        marker = Marker.get_by_key_name(key_name)
        marker.delete()

# @app.route("/login", methods=["POST"])
# @user_optional
# def login():
#     user = get_user()
#     if user:
#         return make_response(json.dumps(user.serialize()))
#
#     if request.json:
#         facebook_data = request.json
#         user_id = facebook_data["userID"]
#         access_token = facebook_data["accessToken"]
#         user_details = json.loads(urllib.urlopen("https://graph.facebook.com/me?access_token=" + access_token).read())
#         # login successful
#         if user_details["id"] == user_id:
#             user = User.query.filter(User.email == user_details["email"]).scalar()
#             if not user:
#                 user = User(
#                     email = user_details["email"],
#                     first_name = user_details["first_name"],
#                     last_name = user_details["last_name"],
#                     username = user_details["username"],
#                     facebook_id = user_details["id"],
#                     facebook_url = user_details["link"],
#                     access_token = facebook_data["accessToken"]
#                 )
#             else:
#                 user.access_token = facebook_data["accessToken"]
#
#             db_session.add(user)
#             set_user(user)
#             return make_response(json.dumps(user.serialize()))
#         else:
#             raise Exception("Error in logging in.")
#     else:
#         raise Exception("No login data or user logged in.")
#
#
# @app.route("/logout")
# @user_required
# def do_logout():
#     logout()
#
# @app.route("/follow/(.*)")
# @user_required
# def follow(key_name):
#     marker = Marker.get_by_key_name(key_name)
#     follower = Follower.all().filter("marker", marker).filter("user", self.user).get()
#     if not follower:
#         Follower(parent = marker, marker = marker, user = self.user).put()
#
# @app.route("/unfollow/(.*)")
# @user_required
# def unfollow(key_name):
#     marker = Marker.get_by_key_name(key_name)
#     follower = Follower.all().filter("marker", marker).filter("user", self.user).get()
#     if follower:
#         follower.delete()

@app.route('/', defaults={'marker_id': None})
@app.route('/<int:marker_id>')
def main(marker_id):
    # at this point the marker id is just a running number, and the
    # LMS is in the description and needs to be promoted to a DB
    # field so we can query it. We also need to add a provider id.
    context = {'minimal_zoom': MINIMAL_ZOOM, 'url': request.host}
    marker = None
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

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s')
    app.run(debug=True)
