import os
import json
import urllib

import jinja2

import webapp2
from google.appengine.api import taskqueue
from models import *
from base import *
import process


FACEBOOK_KEY = "157028231131213"
FACEBOOK_SECRET = "0437ee70207dca46609219b990be0614"

jinja_environment = jinja2.Environment(
    autoescape=True,
    loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), "templates")))

class MainHandler(BaseHandler):
    def get(self, *args):
        template = jinja_environment.get_template("index.html")
        self.response.write(template.render({}))

class MarkersHandler(BaseHandler):
    @user_optional
    def get(self):
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
        self.response.write(json.dumps(markers))

    @user_required
    def post(self):
        data = json.loads(self.request.body)
        marker = Marker.parse(data)
        marker.user = self.user
        marker.update_location()
        marker.put()
        self.response.write(json.dumps(marker.serialize(self.user)))

class MarkerHandler(BaseHandler):
    def get(self, key_name):
        marker = Marker.get_by_key_name(key_name)
        self.response.write(json.dumps(marker.serialize(self.user)))

    @user_required
    def put(self, key_name):
        marker = Marker.get_by_key_name(key_name)
        data = json.loads(self.request.body)
        marker.update(data, self.user)
        self.response.write(json.dumps(marker.serialize(self.user)))

    @user_required
    def delete(self, key_name):
        marker = Marker.get_by_key_name(key_name)
        marker.delete()

class LoginHandler(BaseHandler):
    @user_optional
    def post(self):
        if self.user:
            self.response.out.write(json.dumps(self.user.serialize()))
            return

        if self.request.body:
            facebook_data = json.loads(self.request.body)
            user_id = facebook_data["userID"]
            access_token = facebook_data["accessToken"]
            user_details = json.loads(urllib.urlopen("https://graph.facebook.com/me?access_token=" + access_token).read())
            # login successful
            if user_details["id"] == user_id:
                user = User.all().filter("email", user_details["email"]).get()
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

                user.put()
                self.set_user(user)
                self.response.out.write(json.dumps(user.serialize()))
            else:
                raise Exception("Error in logging in.")
        else:
            raise Exception("No login data or user logged in.")

class LogoutHandler(BaseHandler):
    @user_required
    def get(self):
        self.logout()

class FollowHandler(BaseHandler):
    @user_required
    def get(self, key_name):
        marker = Marker.get_by_key_name(key_name)
        follower = Follower.all().filter("marker", marker).filter("user", self.user).get()
        if not follower:
            Follower(parent = marker, marker = marker, user = self.user).put()

class UnfollowHandler(BaseHandler):
    @user_required
    def get(self, key_name):
        marker = Marker.get_by_key_name(key_name)
        follower = Follower.all().filter("marker", marker).filter("user", self.user).get()
        if follower:
            follower.delete()

class MakeAdminHandler(webapp2.RequestHandler):
    def get(self):
        user = User.all().filter("email", self.request.get("email")).get()

        if user:
            self.response.write("User with email %s is now admin" % user.email)
            user.is_admin = True
            user.put()

class ImportHandler(BaseHandler):
    def get(self):
        process.import_to_datastore()

class StartImportHandler(BaseHandler):
    def get(self):
        taskqueue.add(url="/import", method="GET")
        self.response.write("Import started.")

app = webapp2.WSGIApplication([
    ("/", MainHandler),
    ("/(\d+)", MainHandler),
    ("/login", LoginHandler),
    ("/logout", LogoutHandler),
    ("/markers", MarkersHandler),
    ("/markers/(.*)", MarkerHandler),
    ("/follow/(.*)", FollowHandler),
    ("/unfollow/(.*)", UnfollowHandler),
    ("/make_admin", MakeAdminHandler),
    ("/import", ImportHandler),
    ("/start_import", StartImportHandler),
], debug=True, config={
    "webapp2_extras.sessions": {
        "secret_key": "f0dd2949d6422150343dfa262cb15eafc536085cba624",
    }
})
