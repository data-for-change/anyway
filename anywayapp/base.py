import webapp2
from models import *
from webapp2_extras import sessions

def user_optional(handler):
	def check_login(self, *args, **kwargs):
		self.user = self.get_user()
		return handler(self, *args, **kwargs)

	return check_login

def user_required(handler):
	def check_login(self, *args, **kwargs):
		user = self.get_user()
		if not user:
			self.session["last_page_before_login"] = self.request.path + "?" + self.request.query_string
			self.redirect("/")
		else:
			self.user = user
			return handler(self, *args, **kwargs)

	return check_login


class BaseHandler(webapp2.RequestHandler):
	def dispatch(self):
		# Get a session store for this request.
		self.session_store = sessions.get_store(request=self.request)

		try:
			# Dispatch the request.
			webapp2.RequestHandler.dispatch(self)
		finally:
			# Save all sessions.
			self.session_store.save_sessions(self.response)

	@webapp2.cached_property
	def session(self):
		# Returns a session using the default cookie key.
		return self.session_store.get_session()

	def get_user(self):
		if "user_id" in self.session and self.session["user_id"] is not None:
			return User.get_by_id(self.session["user_id"])

	def set_user(self, user):
		self.session["user_id"] = user.key().id()

	def logout(self):
		self.session["user_id"] = None

