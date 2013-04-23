import webapp2
import jinja2
import os
import json
import urllib

from models import *
from base import *

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
		markers = [marker.serialize(self.user) for marker in Marker.all()]
		self.response.write(json.dumps(markers))

	@user_required
	def post(self):
		data = json.loads(self.request.body)
		marker = Marker.parse(data)
		marker.user = self.user
		marker.put()
		self.response.write(json.dumps(marker.serialize(self.user)))

class MarkerHandler(BaseHandler):
	def get(self, id):
		marker = Marker.get_by_id(int(id))
		self.response.write(json.dumps(marker.serialize(self.user)))

	@user_required
	def put(self, id):
		marker = Marker.get_by_id(int(id))
		data = json.loads(self.request.body)
		marker.update(data, self.user)
		self.response.write(json.dumps(marker.serialize(self.user)))

	@user_required
	def delete(self, id):
		marker = Marker.get_by_id(int(id))
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
	def get(self, id):
		marker = Marker.get_by_id(int(id))
		follower = Follower.all().filter("marker", marker).filter("user", self.user).get()
		if not follower:
			Follower(marker = marker, user = self.user).put()

class UnfollowHandler(BaseHandler):
	@user_required
	def get(self, id):
		marker = Marker.get_by_id(int(id))
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


app = webapp2.WSGIApplication([
	("/", MainHandler),
	("/(\d+)", MainHandler),
	("/login", LoginHandler),
	("/logout", LogoutHandler),
	("/markers", MarkersHandler),
	("/markers/(\d+)", MarkerHandler),
	("/follow/(\d+)", FollowHandler),
	("/unfollow/(\d+)", UnfollowHandler),
	("/make_admin", MakeAdminHandler),
], debug=True, config={
	"webapp2_extras.sessions": {
		"secret_key": "f0dd2949d6422150343dfa262cb15eafc536085cba624",
	}
})
