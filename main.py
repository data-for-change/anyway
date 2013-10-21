import os
from flask import Flask, request, make_response

app = Flask(__name__)
app.secret_key = 'aiosdjsaodjoidjioewnioewfnoeijfoisdjf'

import json
import urllib
import jinja2

from models import *
from base import *

FACEBOOK_KEY = "157028231131213"
FACEBOOK_SECRET = "0437ee70207dca46609219b990be0614"

jinja_environment = jinja2.Environment(
    autoescape=True,
    loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), "templates")))

@app.route("/")
@app.route("/(\d+)")
def main(*args):
    template = jinja_environment.get_template("index.html")
    return make_response(template.render({}))

@app.route("/markers")
@user_optional
def markers(self, methods=["GET", "POST"]):
    if request.method == "GET":
        ne_lat = float(self.request.get("ne_lat"))
        ne_lng = float(self.request.get("ne_lng"))
        sw_lat = float(self.request.get("sw_lat"))
        sw_lng = float(self.request.get("sw_lng"))

        start_time = self.request.get("start_time")
        end_time = self.request.get("end_time")

        query = Marker.all()

        if start_time:
            query = query.filter("created >=", start_time)

        if end_time:
            query = query.filter("created <=", end_time)

        results = Marker.bounding_box_fetch(ne_lat, ne_lng, sw_lat, sw_lng)

        markers = [marker.serialize(self.user) for marker in results]
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

@app.route("/make_admin")
def make_admin():
    user = User.all().filter("email", request.get("email")).get()

    if user:

        user.is_admin = True
        user.put()
        return make_response("User with email %s is now admin" % user.email)

@app.route("/import")
def import_handler():
    import process
    process.import_to_datastore()

if __name__ == "__main__":
    app.run(debug=True)
