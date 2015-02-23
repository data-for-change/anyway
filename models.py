#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import logging

from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, DateTime, Text, BigInteger, Index, desc
from sqlalchemy.orm import relationship, load_only
from flask.ext.sqlalchemy import SQLAlchemy
import datetime
import localization
import utilities
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
    markers = relationship("Marker", backref="users")
    followers = relationship("Follower", backref="users")

    def serialize(self):
        return {
            "id": str(self.id),
            "first_name": self.first_name,
            "last_name": self.last_name,
            "username": self.username,
            "facebook_id": self.facebook_id,
            "facebook_url": self.facebook_url,
            "is_admin": self.is_admin,
        }


class Marker(Base):
    __tablename__ = "markers"
    __table_args__ = (
        Index('long_lat_idx', 'latitude', 'longitude'),
    )

    MARKER_TYPE_ACCIDENT = 1
    MARKER_TYPE_HAZARD = 2
    MARKER_TYPE_OFFER = 3
    MARKER_TYPE_PLEDGE = 4
    MARKER_TYPE_BILL = 5
    MARKER_TYPE_ENGINEERING_PLAN = 6
    MARKER_TYPE_CITY = 7
    MARKER_TYPE_OR_YAROK = 8

    id = Column(BigInteger, primary_key=True)
    user = Column(Integer, ForeignKey("users.id"))
    title = Column(String(100))
    description = Column(Text)
    type = Column(Integer)
    subtype = Column(Integer)
    severity = Column(Integer)
    created = Column(DateTime, default=datetime.datetime.utcnow)
    latitude = Column(Float())
    longitude = Column(Float())
    address = Column(Text)
    locationAccuracy = Column(Integer)
    followers = relationship("Follower", backref="markers")

    def format_description(self, field, value):
        # if the field's value is a static localizable field, fetch it.
        if field in localization.get_supported_tables():
            value = localization.get_field(field, value).decode(db_encoding)
        name = localization.get_field(field).decode(db_encoding)
        return u"{0}: {1}".format(name, value)

    def json_to_description(self, msg):
        description = json.loads(msg, encoding=db_encoding)
        return "\n".join([self.format_description(field, value) for field, value in description.iteritems()])

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
                "description": self.json_to_description(self.description),
                "address": self.address,
                "type": self.type,
                "subtype": self.subtype,

                # TODO: fix relationship
                "user": self.user.serialize() if self.user else "",

                # TODO: fix query
                "followers": [],  # [x.user.serialize() for x in Follower.all().filter("marker", self).fetch(100)],

                # TODO: fix query
                "following": None,
            })
        return fields

    def update(self, data, current_user):
        self.title = data["title"]
        self.description = data["description"]
        self.type = data["type"]
        self.latitude = data["latitude"]
        self.longitude = data["longitude"]

        follower = Follower.query.filter(Follower.marker == self.id).filter(
            Follower.user == current_user).get(1)

        if data["following"]:
            if not follower:
                Follower(marker=self.id, user=current_user)
        else:
            if follower:
                follower[0].delete()

        self.put()

    @staticmethod
    def bounding_box_query(ne_lat, ne_lng, sw_lat, sw_lng, start_date, end_date,
                           fatal, severe, light, inaccurate, is_thin=False, yield_per=None):
        # example:
        # ne_lat=32.36292402647484&ne_lng=35.08873443603511&sw_lat=32.29257266524761&sw_lng=34.88445739746089
        # >>>  m = Marker.bounding_box_query(32.36, 35.088, 32.292, 34.884)
        # >>> m.count()
        # 250
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
            markers = markers.options(load_only("id", "longitude", "latitude",
                                                "created", "severity", "locationAccuracy"))
        return markers

    @staticmethod
    def get_marker(marker_id):
        return Marker.query.filter_by(id=marker_id)

    @classmethod
    def parse(cls, data):
        return Marker(
            title=data["title"],
            description=data["description"],
            type=data["type"],
            latitude=data["latitude"],
            longitude=data["longitude"]
        )


class Follower(Base):
    __tablename__ = "followers"

    user = Column(Integer, ForeignKey("users.id"), primary_key=True)
    marker = Column(BigInteger, ForeignKey("markers.id"), primary_key=True)



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
