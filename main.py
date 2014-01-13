import os
import logging
import json
import urllib
import jinja2

from flask import Flask, request, make_response
from flask.ext.sqlalchemy import SQLAlchemy

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('CLEARDB_DATABASE_URL')
db = SQLAlchemy(app)

app.secret_key = 'aiosdjsaodjoidjioewnioewfnoeijfoisdjf'

FACEBOOK_KEY = "157028231131213"
FACEBOOK_SECRET = "0437ee70207dca46609219b990be0614"

jinja_environment = jinja2.Environment(
    autoescape=True,
    loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), "templates")))

from models import *
from base import *

@app.route("/")
@app.route("/(\d+)")
def main(*args):
    template = jinja_environment.get_template("index.html")
    return make_response(template.render({}))

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
        min_zoom_level = 16
        logging.debug('got params')
        if zoom < min_zoom_level:
            markers = []
        else:
            # query = Marker.all()

            # if 'start_time' in request.values:
            #     query = query.filter("created >=", request.values["start_time"])
            # if 'start_time' in request.values:
            #     query = query.filter("created <=", request.values["end_time"])
            print ""
            logging.debug('querying markers in bouding box')
            results = Marker.bounding_box_fetch(ne_lat, ne_lng, sw_lat, sw_lng)
            logging.debug('serializing markers')
            markers = [marker.serialize() for marker in results.all()]
        return make_response(json.dumps(markers))

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

@app.route("/login", methods=["POST"])
@user_optional
def login():
    user = get_user()
    if user:
        return make_response(json.dumps(user.serialize()))

    if request.json:
        facebook_data = request.json
        user_id = facebook_data["userID"]
        access_token = facebook_data["accessToken"]
        user_details = json.loads(urllib.urlopen("https://graph.facebook.com/me?access_token=" + access_token).read())
        # login successful
        if user_details["id"] == user_id:
            user = db_session.query(User).filter(User.email == user_details["email"]).scalar()
            if not user:
                user = User(
                    email = user_details["email"],
                    first_name = user_details["first_name"],
                    last_name = user_details["last_name"],
                    username = user_details["username"],
                    facebook_id = user_details["id"],
                    facebook_url = user_details["link"],
                    access_token = facebook_data["accessToken"]
                )
            else:
                user.access_token = facebook_data["accessToken"]

            db_session.add(user)
            set_user(user)
            return make_response(json.dumps(user.serialize()))
        else:
            raise Exception("Error in logging in.")
    else:
        raise Exception("No login data or user logged in.")


@app.route("/logout")
@user_required
def do_logout():
    logout()

@app.route("/follow/(.*)")
@user_required
def follow(key_name):
    marker = Marker.get_by_key_name(key_name)
    follower = Follower.all().filter("marker", marker).filter("user", self.user).get()
    if not follower:
        Follower(parent = marker, marker = marker, user = self.user).put()

@app.route("/unfollow/(.*)")
@user_required
def unfollow(key_name):
    marker = Marker.get_by_key_name(key_name)
    follower = Follower.all().filter("marker", marker).filter("user", self.user).get()
    if follower:
        follower.delete()

if __name__ == "__main__":
    app.run(debug=True)
