#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import logging

from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, DateTime, Text, Index, desc, sql
from sqlalchemy.orm import relationship, load_only
import datetime
import localization
from database import Base

db_encoding = 'utf-8'

logging.basicConfig(level=logging.DEBUG)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(120), unique=True)
    first_name = Column(String(50))
    last_name = Column(String(50))
    access_token = Column(String(100))
    username = Column(String(50))
    facebook_id = Column(String(50))
    facebook_url = Column(String(100))
    is_admin = Column(Boolean(), default=False)
    new_features_subscription = Column(Boolean(), default=False)
    login = Column(String(80), unique=True)
    password = Column(String(256))
	
    def serialize(self):
        return {
            "id": str(self.id),
            "first_name": self.first_name,
            "last_name": self.last_name,
            "username": self.username,
            "facebook_id": self.facebook_id,
            "facebook_url": self.facebook_url,
            "is_admin": self.is_admin,
            "new_features_subscription": self.new_features_subscription
        }

    # Flask-Login integration
    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id

    # Required for administrative interface
    def __unicode__(self):
        return self.username

MARKER_TYPE_ACCIDENT = 1
MARKER_TYPE_DISCUSSION = 2

class Point(object):
    id = Column(Integer, primary_key=True)
    latitude = Column(Float())
    longitude = Column(Float())
        
class MarkerMixin(Point):
    type = Column(Integer)
    title = Column(String(100))
    created = Column(DateTime, default=datetime.datetime.now, index=True)

    __mapper_args__ = {
        'polymorphic_on': type
    }

    @staticmethod
    def format_description(field, value):
        # if the field's value is a static localizable field, fetch it.
        if field in localization.get_supported_tables():
            value = localization.get_field(field, value).decode(db_encoding)
        name = localization.get_field(field).decode(db_encoding)
        return u"{0}: {1}".format(name, value)

class HighlightPoint(Point, Base):
    __tablename__ = "highlight_markers"
    __table_args__ = (
        Index('highlight_long_lat_idx', 'latitude', 'longitude'),
    )

    HIGHLIGHT_TYPE_USER_SEARCH = 1
    HIGHLIGHT_TYPE_USER_GPS = 2

    created = Column(DateTime, default=datetime.datetime.now)
    type = Column(Integer)

    def serialize(self):
        return {
            "id": str(self.id),
            "latitude": self.latitude,
            "longitude": self.longitude,
            "type": self.type,
        }

    def update(self, data):
        self.type = data["type"]
        self.latitude = data["latitude"]
        self.longitude = data["longitude"]

    @classmethod
    def parse(cls, data):
        return cls(
            type=data["type"],
            latitude=data["latitude"],
            longitude=data["longitude"]
        )

class Marker(MarkerMixin, Base): # TODO rename to AccidentMarker
    __tablename__ = "markers"
    __table_args__ = (
        Index('acc_long_lat_idx', 'latitude', 'longitude'),
    )

    __mapper_args__ = {
        'polymorphic_identity': MARKER_TYPE_ACCIDENT
    }

    description = Column(Text)
    subtype = Column(Integer)
    severity = Column(Integer)
    address = Column(Text)
    locationAccuracy = Column(Integer)
    roadType = Column(Integer)
    # accidentType
    roadShape = Column(Integer)
    # severityText
    dayType = Column(Integer)
    # igun
    unit = Column(Integer)
    mainStreet = Column(Text)
    secondaryStreet = Column(Text)
    junction = Column(Text)
    one_lane = Column(Integer)
    multi_lane = Column(Integer)
    speed_limit = Column(Integer)
    intactness = Column(Integer)
    road_width = Column(Integer)
    road_sign = Column(Integer)
    road_light = Column(Integer)
    road_control = Column(Integer)
    weather = Column(Integer)
    road_surface = Column(Integer)
    road_object = Column(Integer)
    object_distance = Column(Integer)
    didnt_cross = Column(Integer)
    cross_mode = Column(Integer)
    cross_location = Column(Integer)
    cross_direction = Column(Integer)

    @staticmethod
    def json_to_description(msg):
        description = json.loads(msg, encoding=db_encoding)
        return "\n".join([Marker.format_description(field, value) for field, value in description.iteritems()])

    def serialize(self, is_thin=False):
        fields = {
            "id": str(self.id),
            "latitude": self.latitude,
            "longitude": self.longitude,
            "severity": self.severity,
            "locationAccuracy": self.locationAccuracy,
            "created": self.created.isoformat(),
        }
        if not is_thin:
            fields.update({
                "title": self.title,
                "description": Marker.json_to_description(self.description),
                "address": self.address,
                "type": self.type,
                "subtype": self.subtype,
                "roadType": self.roadType,
                # "accidentType"
                "roadShape": self.roadShape,
                # "severityText"
                "dayType": self.dayType,
                # "igun"
                "unit": self.unit,
                "mainStreet": self.mainStreet,
                "secondaryStreet": self.secondaryStreet,
                "junction": self.junction,
            })
            optional = {
                "one_lane": self.one_lane,
                "multi_lane": self.multi_lane,
                "speed_limit": self.speed_limit,
                "intactness": self.intactness,
                "road_width": self.road_width,
                "road_sign": self.road_sign,
                "road_light": self.road_light,
                "road_control": self.road_control,
                "weather": self.weather,
                "road_surface": self.road_surface,
                "road_object": self.road_object,
                "object_distance": self.object_distance,
                "didnt_cross": self.didnt_cross,
                "cross_mode": self.cross_mode,
                "cross_location": self.cross_location,
                "cross_direction": self.cross_direction,
            }
            for name, value in optional.iteritems():
                if value != 0:
                    fields[name] = value
        return fields

    def update(self, data, current_user):
        self.title = data["title"]
        self.description = data["description"]
        self.type = data["type"]
        self.latitude = data["latitude"]
        self.longitude = data["longitude"]

        self.put()

    @staticmethod
    def bounding_box_query(ne_lat, ne_lng, sw_lat, sw_lng, start_date, end_date,
                           fatal, severe, light, inaccurate, show_markers=True, is_thin=False, yield_per=None):
        # example:
        # ne_lat=32.36292402647484&ne_lng=35.08873443603511&sw_lat=32.29257266524761&sw_lng=34.88445739746089
        # >>>  m = Marker.bounding_box_query(32.36, 35.088, 32.292, 34.884)
        # >>> m.count()
        # 250

        if not show_markers:
            return Marker.query.filter(sql.false())
        accurate = not inaccurate
        markers = Marker.query \
            .filter(Marker.longitude <= ne_lng) \
            .filter(Marker.longitude >= sw_lng) \
            .filter(Marker.latitude <= ne_lat) \
            .filter(Marker.latitude >= sw_lat) \
            .filter(Marker.created >= start_date) \
            .filter(Marker.created < end_date) \
            .order_by(desc(Marker.created))
        if yield_per:
            markers = markers.yield_per(yield_per)
        if accurate:
            markers = markers.filter(Marker.locationAccuracy == 1)
        if not fatal:
            markers = markers.filter(Marker.severity != 1)
        if not severe:
            markers = markers.filter(Marker.severity != 2)
        if not light:
            markers = markers.filter(Marker.severity != 3)
        if is_thin:
            markers = markers.options(load_only("id", "longitude", "latitude"))
        return markers

    @staticmethod
    def get_marker(marker_id):
        return Marker.query.filter_by(id=marker_id)

    @classmethod
    def parse(cls, data):
        return Marker(
            type=MARKER_TYPE_ACCIDENT,
            title=data["title"],
            description=data["description"],
            latitude=data["latitude"],
            longitude=data["longitude"]
        )


class DiscussionMarker(MarkerMixin, Base):
    __tablename__ = "discussions"
    __table_args__ = (
        Index('disc_long_lat_idx', 'latitude', 'longitude'),
    )

    __mapper_args__ = {
        'polymorphic_identity': MARKER_TYPE_DISCUSSION
    }

    identifier = Column(String(50), unique=True)

    def serialize(self, is_thin=False):
        return {
                "id": str(self.id),
                "latitude": self.latitude,
                "longitude": self.longitude,
                "created": self.created.isoformat(),
                "title": self.title,
                "identifier": self.identifier,
                "type": self.type
                }

    @classmethod
    def parse(cls, data):
        # FIXME the id should be generated automatically, but isn't
      last = DiscussionMarker.query.order_by('-id').first()
      return DiscussionMarker(
          id=last.id + 1 if last else 0,
          latitude=data["latitude"],
          longitude=data["longitude"],
          created=datetime.datetime.now(),
          title=data["title"],
          identifier=data["identifier"],
          type=MARKER_TYPE_DISCUSSION
      )

    @staticmethod
    def bounding_box_query(ne_lat, ne_lng, sw_lat, sw_lng, show_discussions):
        if not show_discussions:
            return Marker.query.filter(sql.false())
        markers = DiscussionMarker.query \
            .filter(DiscussionMarker.longitude <= ne_lng) \
            .filter(DiscussionMarker.longitude >= sw_lng) \
            .filter(DiscussionMarker.latitude <= ne_lat) \
            .filter(DiscussionMarker.latitude >= sw_lat) \
            .order_by(desc(DiscussionMarker.created))
        return markers


class Involved(Base):
    __tablename__ = "involved"
    id = Column(Integer, primary_key=True)
    accident_id = Column(Integer, ForeignKey("markers.id"))
    involved_type = Column(Integer)
    license_acquiring_date = Column(Integer)
    age_group = Column(Integer)
    sex = Column(Integer)
    car_type = Column(Integer)
    safety_measures = Column(Integer)
    home_city = Column(Integer)
    injury_severity = Column(Integer)
    injured_type = Column(Integer)
    injured_position = Column(Integer)
    population_type = Column(Integer)
    home_district = Column(Integer)
    home_nafa = Column(Integer)
    home_area = Column(Integer)
    home_municipal_status = Column(Integer)
    home_residence_type = Column(Integer)
    hospital_time = Column(Integer)
    medical_type = Column(Integer)
    release_dest = Column(Integer)
    safety_measures_use = Column(Integer)
    late_deceased = Column(Integer)

    def serialize(self):
        return {
            "id": self.id,
            "accident_id": self.accident_id,
            "involved_type": self.involved_type,
            "license_acquiring_date": self.license_acquiring_date,
            "age_group": self.age_group,
            "sex": self.sex,
            "car_type": self.car_type,
            "safety_measures": self.safety_measures,
            "home_city": self.home_city,
            "injury_severity": self.injury_severity,
            "injured_type": self.injured_type,
            "injured_position": self.injured_position,
            "population_type": self.population_type,
            "home_district": self.home_district,
            "home_nafa": self.home_nafa,
            "home_area": self.home_area,
            "home_municipal_status": self.home_municipal_status,
            "home_residence_type": self.home_residence_type,
            "hospital_time": self.hospital_time,
            "medical_type": self.medical_type,
            "release_dest": self.release_dest,
            "safety_measures_use": self.safety_measures_use,
            "late_deceased": self.late_deceased
        }

    # Flask-Login integration
    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id


class Vehicle(Base):
    __tablename__ = "vehicles"
    id = Column(Integer, primary_key=True)
    accident_id = Column(Integer, ForeignKey("markers.id"))
    engine_volume = Column(Integer)
    manufacturing_year = Column(Integer)
    driving_directions = Column(Integer)
    vehicle_status = Column(Integer)
    vehicle_attribution = Column(Integer)
    vehicle_type = Column(Integer)
    seats = Column(Integer)
    total_weight = Column(Integer)

    def serialize(self):
        return {
            "id": self.id,
            "accident_id": self.accident_id,
            "engine_volume": self.engine_volume,
            "manufacturing_year": self.manufacturing_year,
            "driving_directions": self.driving_directions,
            "vehicle_status": self.vehicle_status,
            "vehicle_attribution": self.vehicle_attribution,
            "vehicle_type": self.vehicle_type,
            "seats": self.seats,
            "total_weight": self.total_weight
        }

    # Flask-Login integration
    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id


def init_db():
    from database import engine
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    print "Importing models"
    print "Creating all tables"
    Base.metadata.create_all(bind=engine)
	



if __name__ == "__main__":
    init_db()
