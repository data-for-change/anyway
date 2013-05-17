from google.appengine.ext import db
from google.appengine.api import search

class User(db.Model):
	email = db.StringProperty()
	access_token = db.StringProperty()
	first_name = db.StringProperty()
	last_name = db.StringProperty()
	username = db.StringProperty()
	facebook_id = db.StringProperty()
	facebook_url = db.StringProperty()
	is_admin = db.BooleanProperty(default=False)

	def serialize(self):
		return {
			"id" : str(self.key()),
			"first_name" : self.first_name,
			"last_name" : self.last_name,
			"username" : self.username,
			"facebook_id" : self.facebook_id,
			"facebook_url" : self.facebook_url,
			"is_admin" : self.is_admin,
		}

class Marker(db.Model):
	MARKER_TYPE_ACCIDENT = 1
	MARKER_TYPE_HAZARD = 2
	MARKER_TYPE_OFFER = 3
	MARKER_TYPE_PLEDGE = 4
	MARKER_TYPE_BILL = 5
	MARKER_TYPE_ENGINEERING_PLAN = 6
	MARKER_TYPE_CITY = 7
	MARKER_TYPE_OR_YAROK = 8

	user = db.ReferenceProperty(User)
	title = db.StringProperty()
	description = db.TextProperty()
	type = db.IntegerProperty()
	subtype = db.IntegerProperty()
	created = db.DateTimeProperty(auto_now=True)
	modified = db.DateTimeProperty(auto_now_add=True)
	location = db.GeoPtProperty()

	def serialize(self, current_user):
		return {
			"id" : str(self.key()),
			"title" : self.title,
			"description" : self.description,
			"latitude" : self.location.lat,
			"longitude" : self.location.lon,
			"type" : self.type,
			"user" : self.user.serialize(),
			"followers" : [x.user.serialize() for x in Follower.all().filter("marker", self).fetch(100)],
			"following" : Follower.all().filter("user", current_user).filter("marker", self).filter("user", current_user).get() is not None if current_user else None,
			"created" : self.created.isoformat(),
			"modified" : self.modified.isoformat()
		}

	def update(self, data, current_user):
		self.title = data["title"]
		self.description = data["description"]
		self.type = data["type"]
		self.location = db.GeoPt(data["latitude"], data["longitude"])
		follower = Follower.all().filter("marker", self).filter("user", current_user).get()
		if data["following"]:
			if not follower:
				Follower(marker = self, user = current_user).put()
		else:
			if follower:
				follower.delete()

		self.update_location()
		self.put()

	def update_location(self):
		index = search.Index(name="markers")
		index.put(search.Document(
			doc_id=str(self.key()), fields=[
				search.TextField(name="title", value=self.title),
				search.TextField(name="description", value=self.description),
				search.DateField(name="modified", value=self.modified),
				search.DateField(name="created", value=self.created),
				search.GeoField(name="location", value=search.GeoPoint(self.location.lat, self.location.lon)),
			]
		))


	@classmethod
	def bounding_box_fetch(cls, ne_lat, ne_lng, sw_lat, sw_lng):
		index = search.Index(name="markers")

		center_lat = (ne_lat + sw_lat) / 2
		center_lng = (ne_lng + sw_lng) / 2

		distance = max(ne_lng - sw_lng, ne_lat - sw_lat) * 10000

		query = "distance(location, geopoint(%(lat)3.4f, %(lng)3.4f)) < %(distance)s" % {
			"lat" : center_lat,
			"lng" : center_lng,
			"distance" : distance,
		}
		search_query = search.Query(
			query_string=query,
			options=search.QueryOptions(limit=20)
		)
		results = index.search(search_query)
		return [Marker.get(result.doc_id) for result in results]

	@classmethod
	def parse(cls, data):
		return Marker(
			title = data["title"],
			description = data["description"],
			type = data["type"],
			location = db.GeoPt(data["latitude"], data["longitude"]),
		)

class Follower(db.Model):
	user = db.ReferenceProperty(User)
	marker = db.ReferenceProperty(Marker)
