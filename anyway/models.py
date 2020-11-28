#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime
import json
import logging
from collections import namedtuple
from sqlalchemy.sql import func
from flask_security import UserMixin, RoleMixin
from geoalchemy2 import Geometry
from sqlalchemy import (
    Column,
    BigInteger,
    Integer,
    String,
    Boolean,
    Float,
    ForeignKey,
    DateTime,
    Text,
    Index,
    desc,
    sql,
    Table,
    ForeignKeyConstraint,
    func,
    and_,
    TIMESTAMP,
)
import sqlalchemy
from sqlalchemy.orm import relationship, load_only, backref
from sqlalchemy import or_, and_

from anyway import localization
from anyway.backend_constants import BE_CONST
from anyway.database import Base
from anyway.utilities import decode_hebrew
from anyway.app_and_db import db

MarkerResult = namedtuple("MarkerResult", ["accident_markers", "rsa_markers", "total_records"])

db_encoding = "utf-8"

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.DEBUG,
    datefmt="%Y-%m-%d %H:%M:%S",
)

roles_users = Table(
    "roles_users",
    Base.metadata,
    Column("user_id", Integer(), ForeignKey("users.id")),
    Column("role_id", Integer(), ForeignKey("roles.id")),
)


class UserOAuth(Base, UserMixin):
    __tablename__ = "user_oauth"
    id = Column(BigInteger, autoincrement=True, nullable=False, primary_key=True, index=True)
    user_register_date = Column(DateTime, nullable=False)
    user_last_login_date = Column(DateTime, nullable=False)
    email = Column(String(255), nullable=True, index=True)
    name = Column(String(255), nullable=True)
    is_active = Column(Boolean)
    oauth_provider = Column(String(64), nullable=False, index=True)
    oauth_provider_user_id = Column(String, nullable=False, index=True)
    oauth_provider_user_domain = Column(String, nullable=True)
    oauth_provider_user_picture_url = Column(String, nullable=True)
    oauth_provider_user_locale = Column(String(64), nullable=True)
    oauth_provider_user_profile_url = Column(String, nullable=True)
    work_on_behalf_of_organization = Column(String(128), nullable=True)


class User(Base, UserMixin):
    __tablename__ = "users"
    id = Column(BigInteger(), primary_key=True)
    email = Column(String(120), unique=True)
    first_name = Column(String(50))
    last_name = Column(String(50))
    access_token = Column(String(100))
    username = Column(String(50), unique=True)
    facebook_id = Column(String(50))
    facebook_url = Column(String(100))
    is_admin = Column(Boolean(), default=False)
    new_features_subscription = Column(Boolean(), default=False)
    password = Column(String(256))
    active = Column(Boolean())
    confirmed_at = Column(DateTime())
    social_id = Column(String(64), nullable=True, unique=True)
    nickname = Column(String(64), nullable=True)
    provider = Column(String(64), nullable=True)
    roles = relationship("Role", secondary=roles_users, backref=backref("users", lazy="dynamic"))

    def serialize(self):
        return {
            "id": str(self.id),
            "first_name": self.first_name,
            "last_name": self.last_name,
            "username": self.username,
            "facebook_id": self.facebook_id,
            "facebook_url": self.facebook_url,
            "is_admin": self.is_admin,
            "new_features_subscription": self.new_features_subscription,
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


class LocationSubscribers(Base, UserMixin):
    __tablename__ = "locationsubscribers"
    id = Column(BigInteger(), primary_key=True)
    email = Column(String(120))
    first_name = Column(String(50))
    last_name = Column(String(50))
    ne_lng = Column(Float(), nullable=True)
    ne_lat = Column(Float(), nullable=True)
    sw_lng = Column(Float(), nullable=True)
    sw_lat = Column(Float(), nullable=True)
    school_id = Column(Integer(), nullable=True)

    def serialize(self):
        return {
            "id": str(self.id),
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "ne_lng": self.ne_lng,
            "ne_lat": self.ne_lat,
            "sw_lng": self.sw_lng,
            "sw_lat": self.sw_lat,
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


class Role(Base, RoleMixin):
    __tablename__ = "roles"
    id = Column(Integer(), primary_key=True)
    name = Column(String(80), unique=True)
    description = Column(String(255))

    def __unicode__(self):
        return self.name


class Point(object):
    id = Column(Integer(), primary_key=True)
    latitude = Column(Float())
    longitude = Column(Float())


class MarkerMixin(Point):
    type = Column(Integer())
    title = Column(String(100))
    created = Column(DateTime, default=datetime.datetime.now, index=True)

    __mapper_args__ = {"polymorphic_on": type}

    @staticmethod
    def format_description(field, value):
        # if the field's value is a static localizable field, fetch it.
        if field in localization.get_supported_tables():
            value = decode_hebrew(localization.get_field(field, value))
        name = decode_hebrew(localization.get_field(field))
        return "{0}: {1}".format(name, value)


class HighlightPoint(Point, Base):
    __tablename__ = "highlight_markers"
    __table_args__ = (Index("highlight_long_lat_idx", "latitude", "longitude"),)

    created = Column(DateTime, default=datetime.datetime.now)
    type = Column(Integer())

    def serialize(self):
        return {
            "id": str(self.id),
            "latitude": self.latitude,
            "longitude": self.longitude,
            "type": self.type,
        }

    @classmethod
    def parse(cls, data):
        return cls(type=data["type"], latitude=data["latitude"], longitude=data["longitude"])


class AccidentMarker(MarkerMixin, Base):
    __tablename__ = "markers"
    __table_args__ = (
        Index("acc_long_lat_idx", "latitude", "longitude"),
        Index("id_idx_markers", "id", unique=False),
        Index("provider_and_id_idx_markers", "provider_and_id", unique=False),
        Index("idx_markers_geom", "geom", unique=False),
        Index("idx_markers_created", "created", unique=False),
    )

    __mapper_args__ = {"polymorphic_identity": BE_CONST.MARKER_TYPE_ACCIDENT}
    id = Column(BigInteger(), primary_key=True)
    provider_and_id = Column(BigInteger())
    provider_code = Column(Integer(), primary_key=True)
    file_type_police = Column(Integer())
    description = Column(Text())
    accident_type = Column(Integer())
    accident_severity = Column(Integer())
    address = Column(Text())
    location_accuracy = Column(Integer())
    road_type = Column(Integer())
    road_shape = Column(Integer())
    day_type = Column(Integer())
    police_unit = Column(Integer())
    mainStreet = Column(Text())
    secondaryStreet = Column(Text())
    junction = Column(Text())
    one_lane = Column(Integer())
    multi_lane = Column(Integer())
    speed_limit = Column(Integer())
    road_intactness = Column(Integer())
    road_width = Column(Integer())
    road_sign = Column(Integer())
    road_light = Column(Integer())
    road_control = Column(Integer())
    weather = Column(Integer())
    road_surface = Column(Integer())
    road_object = Column(Integer())
    object_distance = Column(Integer())
    didnt_cross = Column(Integer())
    cross_mode = Column(Integer())
    cross_location = Column(Integer())
    cross_direction = Column(Integer())
    involved = relationship("Involved")
    vehicles = relationship("Vehicle")
    video_link = Column(Text())
    road1 = Column(Integer())
    road2 = Column(Integer())
    km = Column(Float())
    km_raw = Column(Text())
    km_accurate = Column(Boolean())
    yishuv_symbol = Column(Integer())
    yishuv_name = Column(Text())
    geo_area = Column(Integer())
    day_night = Column(Integer())
    day_in_week = Column(Integer())
    traffic_light = Column(Integer())
    region = Column(Integer())
    district = Column(Integer())
    natural_area = Column(Integer())
    municipal_status = Column(Integer())
    yishuv_shape = Column(Integer())
    street1 = Column(Integer())
    street1_hebrew = Column(Text())
    street2 = Column(Integer())
    street2_hebrew = Column(Text())
    house_number = Column(Integer())
    urban_intersection = Column(Integer())
    non_urban_intersection = Column(Integer())
    non_urban_intersection_hebrew = Column(Text())
    accident_year = Column(Integer(), primary_key=True)
    accident_month = Column(Integer())
    accident_day = Column(Integer())
    accident_hour_raw = Column(Integer())
    accident_hour = Column(Integer())
    accident_minute = Column(Integer())
    x = Column(Float())
    y = Column(Float())
    vehicle_type_rsa = Column(Text())
    violation_type_rsa = Column(Text())
    geom = Column(Geometry("POINT"))
    non_urban_intersection_by_junction_number = Column(Text())
    rsa_severity = Column(Integer())
    rsa_license_plate = Column(Text())

    @staticmethod
    def get_latest_marker_created_date():
        latest_created_date = (
            db.session.query(func.max(AccidentMarker.created))
            .filter(
                AccidentMarker.provider_code.in_(
                    [BE_CONST.CBS_ACCIDENT_TYPE_1_CODE, BE_CONST.CBS_ACCIDENT_TYPE_3_CODE]
                )
            )
            .first()
        )

        if latest_created_date is None:
            return None
        else:
            return latest_created_date[0]

    @staticmethod
    def json_to_description(msg):
        description = json.loads(msg, encoding=db_encoding)
        return "\n".join(
            [
                AccidentMarker.format_description(field, value)
                for field, value in description.items()
            ]
        )

    def serialize(self, is_thin=False):
        fields = {
            "id": str(self.id),
            "provider_code": self.provider_code,
            "accident_year": self.accident_year,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "accident_severity": self.accident_severity,
            "location_accuracy": self.location_accuracy,
            "created": self.created.isoformat(),
        }
        if not is_thin:
            fields.update(
                {
                    "title": self.title,
                    "address": self.address,
                    "type": self.type,
                    "accident_type": self.accident_type,
                    "road_type": self.road_type,
                    "road_shape": self.road_shape,
                    "day_type": self.day_type,
                    "police_unit": self.police_unit,
                    "mainStreet": self.mainStreet,
                    "secondaryStreet": self.secondaryStreet,
                    "junction": self.junction,
                }
            )
            # United Hatzala accidents description are not json:
            if self.provider_code == BE_CONST.UNITED_HATZALA_CODE:
                fields.update({"description": self.description})
            else:
                fields.update({"description": AccidentMarker.json_to_description(self.description)})

            optional = {
                "one_lane": self.one_lane,
                "multi_lane": self.multi_lane,
                "speed_limit": self.speed_limit,
                "road_intactness": self.road_intactness,
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
                "video_link": self.video_link,
                "road1": self.road1,
                "road2": self.road2,
                "km": self.km,
            }
            for name, value in optional.items():
                if value != 0:
                    fields[name] = value
        return fields

    @staticmethod
    def bounding_box_query(
        is_thin=False, yield_per=None, involved_and_vehicles=False, query_entities=None, **kwargs
    ):
        approx = kwargs.get("approx", True)
        accurate = kwargs.get("accurate", True)
        page = kwargs.get("page")
        per_page = kwargs.get("per_page")

        if not kwargs.get("show_markers", True):
            return MarkerResult(
                accident_markers=db.session.query(AccidentMarker).filter(sql.false()),
                rsa_markers=db.session.query(AccidentMarker).filter(sql.false()),
                total_records=0,
            )

        sw_lat = float(kwargs["sw_lat"])
        sw_lng = float(kwargs["sw_lng"])
        ne_lat = float(kwargs["ne_lat"])
        ne_lng = float(kwargs["ne_lng"])
        polygon_str = "POLYGON(({0} {1},{0} {3},{2} {3},{2} {1},{0} {1}))".format(
            sw_lng, sw_lat, ne_lng, ne_lat
        )

        if query_entities is not None:
            markers = (
                db.session.query(AccidentMarker)
                .with_entities(*query_entities)
                .filter(AccidentMarker.geom.intersects(polygon_str))
                .filter(AccidentMarker.created >= kwargs["start_date"])
                .filter(AccidentMarker.created < kwargs["end_date"])
                .filter(AccidentMarker.provider_code != BE_CONST.RSA_PROVIDER_CODE)
                .order_by(desc(AccidentMarker.created))
            )

            rsa_markers = (
                db.session.query(AccidentMarker)
                .with_entities(*query_entities)
                .filter(AccidentMarker.geom.intersects(polygon_str))
                .filter(AccidentMarker.created >= kwargs["start_date"])
                .filter(AccidentMarker.created < kwargs["end_date"])
                .filter(AccidentMarker.provider_code == BE_CONST.RSA_PROVIDER_CODE)
                .order_by(desc(AccidentMarker.created))
            )
        else:
            markers = (
                db.session.query(AccidentMarker)
                .filter(AccidentMarker.geom.intersects(polygon_str))
                .filter(AccidentMarker.created >= kwargs["start_date"])
                .filter(AccidentMarker.created < kwargs["end_date"])
                .filter(AccidentMarker.provider_code != BE_CONST.RSA_PROVIDER_CODE)
                .order_by(desc(AccidentMarker.created))
            )

            rsa_markers = (
                db.session.query(AccidentMarker)
                .filter(AccidentMarker.geom.intersects(polygon_str))
                .filter(AccidentMarker.created >= kwargs["start_date"])
                .filter(AccidentMarker.created < kwargs["end_date"])
                .filter(AccidentMarker.provider_code == BE_CONST.RSA_PROVIDER_CODE)
                .order_by(desc(AccidentMarker.created))
            )

        if not kwargs["show_rsa"]:
            rsa_markers = db.session.query(AccidentMarker).filter(sql.false())
        if not kwargs["show_accidents"]:
            markers = markers.filter(
                and_(
                    AccidentMarker.provider_code != BE_CONST.CBS_ACCIDENT_TYPE_1_CODE,
                    AccidentMarker.provider_code != BE_CONST.CBS_ACCIDENT_TYPE_3_CODE,
                    AccidentMarker.provider_code != BE_CONST.UNITED_HATZALA_CODE,
                )
            )
        if yield_per:
            markers = markers.yield_per(yield_per)
        if accurate and not approx:
            markers = markers.filter(AccidentMarker.location_accuracy == 1)
        elif approx and not accurate:
            markers = markers.filter(AccidentMarker.location_accuracy != 1)
        elif not accurate and not approx:
            return MarkerResult(
                accident_markers=db.session.query(AccidentMarker).filter(sql.false()),
                rsa_markers=db.session.query(AccidentMarker).filter(sql.false()),
                total_records=0,
            )
        if not kwargs.get("show_fatal", True):
            markers = markers.filter(AccidentMarker.accident_severity != 1)
        if not kwargs.get("show_severe", True):
            markers = markers.filter(AccidentMarker.accident_severity != 2)
        if not kwargs.get("show_light", True):
            markers = markers.filter(AccidentMarker.accident_severity != 3)
        if kwargs.get("show_urban", 3) != 3:
            if kwargs["show_urban"] == 2:
                markers = markers.filter(AccidentMarker.road_type >= 1).filter(
                    AccidentMarker.road_type <= 2
                )
            elif kwargs["show_urban"] == 1:
                markers = markers.filter(AccidentMarker.road_type >= 3).filter(
                    AccidentMarker.road_type <= 4
                )
            else:
                return MarkerResult(
                    accident_markers=db.session.query(AccidentMarker).filter(sql.false()),
                    rsa_markers=rsa_markers,
                    total_records=None,
                )
        if kwargs.get("show_intersection", 3) != 3:
            if kwargs["show_intersection"] == 2:
                markers = markers.filter(AccidentMarker.road_type != 2).filter(
                    AccidentMarker.road_type != 4
                )
            elif kwargs["show_intersection"] == 1:
                markers = markers.filter(AccidentMarker.road_type != 1).filter(
                    AccidentMarker.road_type != 3
                )
            else:
                return MarkerResult(
                    accident_markers=db.session.query(AccidentMarker).filter(sql.false()),
                    rsa_markers=rsa_markers,
                    total_records=None,
                )
        if kwargs.get("show_lane", 3) != 3:
            if kwargs["show_lane"] == 2:
                markers = markers.filter(AccidentMarker.one_lane >= 2).filter(
                    AccidentMarker.one_lane <= 3
                )
            elif kwargs["show_lane"] == 1:
                markers = markers.filter(AccidentMarker.one_lane == 1)
            else:
                return MarkerResult(
                    accident_markers=db.session.query(AccidentMarker).filter(sql.false()),
                    rsa_markers=rsa_markers,
                    total_records=None,
                )

        if kwargs.get("show_day", 7) != 7:
            markers = markers.filter(
                func.extract("dow", AccidentMarker.created) == kwargs["show_day"]
            )
        if kwargs.get("show_holiday", 0) != 0:
            markers = markers.filter(AccidentMarker.day_type == kwargs["show_holiday"])

        if kwargs.get("show_time", 24) != 24:
            if kwargs["show_time"] == 25:  # Daylight (6-18)
                markers = markers.filter(func.extract("hour", AccidentMarker.created) >= 6).filter(
                    func.extract("hour", AccidentMarker.created) < 18
                )
            elif kwargs["show_time"] == 26:  # Darktime (18-6)
                markers = markers.filter(
                    (func.extract("hour", AccidentMarker.created) >= 18)
                    | (func.extract("hour", AccidentMarker.created) < 6)
                )
            else:
                markers = markers.filter(
                    func.extract("hour", AccidentMarker.created) >= kwargs["show_time"]
                ).filter(func.extract("hour", AccidentMarker.created) < kwargs["show_time"] + 6)
        elif kwargs["start_time"] != 25 and kwargs["end_time"] != 25:
            markers = markers.filter(
                func.extract("hour", AccidentMarker.created) >= kwargs["start_time"]
            ).filter(func.extract("hour", AccidentMarker.created) < kwargs["end_time"])
        if kwargs.get("weather", 0) != 0:
            markers = markers.filter(AccidentMarker.weather == kwargs["weather"])
        if kwargs.get("road", 0) != 0:
            markers = markers.filter(AccidentMarker.road_shape == kwargs["road"])
        if kwargs.get("separation", 0) != 0:
            markers = markers.filter(AccidentMarker.multi_lane == kwargs["separation"])
        if kwargs.get("surface", 0) != 0:
            markers = markers.filter(AccidentMarker.road_surface == kwargs["surface"])
        if kwargs.get("acctype", 0) != 0:
            if kwargs["acctype"] <= 20:
                markers = markers.filter(AccidentMarker.accident_type == kwargs["acctype"])
            elif kwargs["acctype"] == BE_CONST.BIKE_ACCIDENTS:
                markers = markers.filter(
                    AccidentMarker.vehicles.any(Vehicle.vehicle_type == BE_CONST.VEHICLE_TYPE_BIKE)
                )
        if kwargs.get("controlmeasure", 0) != 0:
            markers = markers.filter(AccidentMarker.road_control == kwargs["controlmeasure"])
        if kwargs.get("district", 0) != 0:
            markers = markers.filter(AccidentMarker.police_unit == kwargs["district"])

        if kwargs.get("case_type", 0) != 0:
            markers = markers.filter(AccidentMarker.provider_code == kwargs["case_type"])

        if is_thin:
            markers = markers.options(load_only("id", "longitude", "latitude"))

        if kwargs.get("age_groups"):
            age_groups_list = kwargs.get("age_groups").split(",")
            if len(age_groups_list) < (BE_CONST.AGE_GROUPS_NUMBER + 1):
                markers = markers.filter(
                    AccidentMarker.involved.any(Involved.age_group.in_(age_groups_list))
                )
        else:
            markers = db.session.query(AccidentMarker).filter(sql.false())

        if kwargs.get("light_transportation", False) == True:
            age_groups_list = kwargs.get("age_groups").split(",")
            markers = markers.filter(
                or_(
                    AccidentMarker.involved.any(
                        and_(
                            Involved.injured_type == 1,
                            Involved.injury_severity >= 1,
                            Involved.injury_severity <= 3,
                            Involved.age_group.in_(age_groups_list),
                        )
                    ),
                    AccidentMarker.involved.any(
                        and_(
                            Involved.vehicle_type == 15,
                            Involved.injury_severity >= 1,
                            Involved.injury_severity <= 3,
                            Involved.age_group.in_(age_groups_list),
                        )
                    ),
                    AccidentMarker.involved.any(
                        and_(
                            Involved.vehicle_type == 21,
                            Involved.injury_severity >= 1,
                            Involved.injury_severity <= 3,
                            Involved.age_group.in_(age_groups_list),
                        )
                    ),
                    AccidentMarker.involved.any(
                        and_(
                            Involved.vehicle_type == 23,
                            Involved.injury_severity >= 1,
                            Involved.injury_severity <= 3,
                            Involved.age_group.in_(age_groups_list),
                        )
                    ),
                )
            )

        if page and per_page:
            markers = markers.offset((page - 1) * per_page).limit(per_page)

        if involved_and_vehicles:
            fetch_markers = kwargs.get("fetch_markers", True)
            fetch_vehicles = kwargs.get("fetch_vehicles", True)
            fetch_involved = kwargs.get("fetch_involved", True)
            markers_ids = [marker.id for marker in markers]
            markers = None
            vehicles = None
            involved = None
            if fetch_markers:
                markers = db.session.query(AccidentMarker).filter(
                    AccidentMarker.id.in_(markers_ids)
                )
            if fetch_vehicles:
                vehicles = db.session.query(Vehicle).filter(Vehicle.accident_id.in_(markers_ids))
            if fetch_involved:
                involved = db.session.query(Involved).filter(Involved.accident_id.in_(markers_ids))
            result = (
                markers.all() if markers is not None else [],
                vehicles.all() if vehicles is not None else [],
                involved.all() if involved is not None else [],
            )
            return MarkerResult(
                accident_markers=result,
                rsa_markers=db.session.query(AccidentMarker).filter(sql.false()),
                total_records=len(result),
            )
        else:
            return MarkerResult(
                accident_markers=markers, rsa_markers=rsa_markers, total_records=None
            )

    @staticmethod
    def get_marker(marker_id):
        return db.session.query(AccidentMarker).filter_by(id=marker_id)

    @classmethod
    def parse(cls, data):
        return AccidentMarker(
            type=BE_CONST.MARKER_TYPE_ACCIDENT,
            title=data["title"],
            description=data["description"],
            latitude=data["latitude"],
            longitude=data["longitude"],
        )


class DiscussionMarker(MarkerMixin, Base):
    __tablename__ = "discussions"
    __table_args__ = (
        Index("disc_long_lat_idx", "latitude", "longitude"),
        Index("idx_discussions_geom", "geom", unique=False),
    )

    __mapper_args__ = {"polymorphic_identity": BE_CONST.MARKER_TYPE_DISCUSSION}

    identifier = Column(String(50), unique=True)
    geom = Column(Geometry("POINT"))

    def serialize(self, is_thin=False):
        return {
            "id": str(self.id),
            "latitude": self.latitude,
            "longitude": self.longitude,
            "created": self.created.isoformat(),
            "title": self.title,
            "identifier": self.identifier,
            "type": self.type,
        }

    @staticmethod
    def get_by_identifier(identifier):
        return db.session.query(DiscussionMarker).filter_by(identifier=identifier)

    @classmethod
    def parse(cls, data):
        # FIXME the id should be generated automatically, but isn't
        last = db.session.query(DiscussionMarker).order_by("-id").first()
        return DiscussionMarker(
            id=last.id + 1 if last else 0,
            latitude=data["latitude"],
            longitude=data["longitude"],
            created=datetime.datetime.now(),
            title=data["title"],
            identifier=data["identifier"],
            type=BE_CONST.MARKER_TYPE_DISCUSSION,
        )

    @staticmethod
    def bounding_box_query(ne_lat, ne_lng, sw_lat, sw_lng, show_discussions):
        if not show_discussions:
            return db.session.query(AccidentMarker).filter(sql.false())
        markers = (
            db.session.query(DiscussionMarker)
            .filter(DiscussionMarker.longitude <= ne_lng)
            .filter(DiscussionMarker.longitude >= sw_lng)
            .filter(DiscussionMarker.latitude <= ne_lat)
            .filter(DiscussionMarker.latitude >= sw_lat)
            .order_by(desc(DiscussionMarker.created))
        )
        return markers


class Involved(Base):
    __tablename__ = "involved"
    id = Column(BigInteger(), primary_key=True)
    provider_and_id = Column(BigInteger())
    provider_code = Column(Integer())
    file_type_police = Column(Integer())
    accident_id = Column(BigInteger())
    involved_type = Column(Integer())
    license_acquiring_date = Column(Integer())
    age_group = Column(Integer())
    sex = Column(Integer())
    vehicle_type = Column(Integer())
    safety_measures = Column(Integer())
    involve_yishuv_symbol = Column(Integer())
    involve_yishuv_name = Column(Text())
    injury_severity = Column(Integer())
    injured_type = Column(Integer())
    injured_position = Column(Integer())
    population_type = Column(Integer())
    home_region = Column(Integer())
    home_district = Column(Integer())
    home_natural_area = Column(Integer())
    home_municipal_status = Column(Integer())
    home_yishuv_shape = Column(Integer())
    hospital_time = Column(Integer())
    medical_type = Column(Integer())
    release_dest = Column(Integer())
    safety_measures_use = Column(Integer())
    late_deceased = Column(Integer())
    car_id = Column(Integer())
    involve_id = Column(Integer())
    accident_year = Column(Integer())
    accident_month = Column(Integer())
    injury_severity_mais = Column(Integer())
    __table_args__ = (
        ForeignKeyConstraint(
            [accident_id, provider_code, accident_year],
            [AccidentMarker.id, AccidentMarker.provider_code, AccidentMarker.accident_year],
            ondelete="CASCADE",
        ),
        Index("accident_id_idx_involved", "accident_id", unique=False),
        Index("provider_and_id_idx_involved", "provider_and_id", unique=False),
        {},
    )

    def serialize(self):
        return {
            "id": self.id,
            "provider_code": self.provider_code,
            "accident_id": self.accident_id,
            "involved_type": self.involved_type,
            "license_acquiring_date": self.license_acquiring_date,
            "age_group": self.age_group,
            "sex": self.sex,
            "vehicle_type": self.vehicle_type,
            "safety_measures": self.safety_measures,
            "involve_yishuv_symbol": self.involve_yishuv_symbol,
            "injury_severity": self.injury_severity,
            "injured_type": self.injured_type,
            "injured_position": self.injured_position,
            "population_type": self.population_type,
            "home_region": self.home_region,
            "home_district": self.home_district,
            "home_natural_area": self.home_natural_area,
            "home_municipal_status": self.home_municipal_status,
            "home_yishuv_shape": self.home_yishuv_shape,
            "hospital_time": self.hospital_time,
            "medical_type": self.medical_type,
            "release_dest": self.release_dest,
            "safety_measures_use": self.safety_measures_use,
            "late_deceased": self.late_deceased,
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


class NewsFlash(Base):
    __tablename__ = "news_flash"
    id = Column(BigInteger(), primary_key=True)
    accident = Column(Boolean(), nullable=False)
    author = Column(Text(), nullable=True)
    date = Column(TIMESTAMP(), nullable=True)
    description = Column(Text(), nullable=True)
    lat = Column(Float(), nullable=True)
    link = Column(Text(), nullable=True)
    lon = Column(Float(), nullable=True)
    road1 = Column(Float(), nullable=True)
    road2 = Column(Float(), nullable=True)
    resolution = Column(Text(), nullable=True)
    title = Column(Text(), nullable=True)
    source = Column(Text(), nullable=True)
    organization = Column(Text(), nullable=True)
    location = Column(Text(), nullable=True)
    tweet_id = Column(BigInteger(), nullable=True)
    region_hebrew = Column(Text(), nullable=True)
    district_hebrew = Column(Text(), nullable=True)
    yishuv_name = Column(Text(), nullable=True)
    street1_hebrew = Column(Text(), nullable=True)
    street2_hebrew = Column(Text(), nullable=True)
    non_urban_intersection_hebrew = Column(Text(), nullable=True)
    road_segment_name = Column(Text(), nullable=True)
    waze_alert = Column(Integer(), ForeignKey("waze_alerts.id"), nullable=True)

    def serialize(self):
        return {
            "id": self.id,
            "accident": self.accident,
            "author": self.author,
            "date": self.date,
            "description": self.description,
            "lat": self.lat,
            "link": self.link,
            "lon": self.lon,
            "road1": self.road1,
            "road2": self.road2,
            "resolution": self.resolution,
            "title": self.title,
            "source": self.source,
            "organization": self.organization,
            "location": self.location,
            "tweet_id": self.tweet_id,
            "region_hebrew": self.region_hebrew,
            "district_hebrew": self.district_hebrew,
            "yishuv_name": self.yishuv_name,
            "street1_hebrew": self.street1_hebrew,
            "street2_hebrew": self.street2_hebrew,
            "non_urban_intersection_hebrew": self.non_urban_intersection_hebrew,
            "road_segment_name": self.road_segment_name,
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


class City(Base):
    __tablename__ = "cities"
    id = Column(Integer(), primary_key=True)
    symbol_code = Column(Integer())
    name = Column(String())
    search_heb = Column(String())
    search_eng = Column(String())
    search_priority = Column(Integer())

    def serialize(self):
        return {
            "id": self.id,
            "symbol_code": self.symbol_code,
            "name": self.name,
            "search_heb": self.search_heb,
            "search_eng": self.search_eng,
            "search_priority": self.search_priority,
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


class RegisteredVehicle(Base):
    __tablename__ = "cities_vehicles_registered"
    id = Column(Integer(), primary_key=True)
    city_id = Column(Integer())
    year = Column(Integer())
    name = Column(String())
    name_eng = Column(String())
    search_name = Column(String())
    motorcycle = Column(Integer())
    special = Column(Integer())
    taxi = Column(Integer())
    bus = Column(Integer())
    minibus = Column(Integer())
    truck_over3500 = Column(Integer())
    truck_upto3500 = Column(Integer())
    private = Column(Integer())
    population_year = Column(Integer())
    population = Column(Integer())
    total = Column(Integer())

    def serialize(self):
        return {
            "id": self.id,
            "city_id": self.city_id,
            "year": self.year,
            "name": self.name,
            "name_eng": self.name_eng,
            "search_name": self.search_name,
            "motorcycle": self.motorcycle,
            "special": self.special,
            "taxi": self.taxi,
            "bus": self.bus,
            "minibus": self.minibus,
            "truck_over3500": self.truck_over3500,
            "truck_upto3500": self.truck_upto3500,
            "private": self.private,
            "population_year": self.population_year,
            "population": self.population,
            "total": self.total,
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
    id = Column(BigInteger(), primary_key=True)
    provider_and_id = Column(BigInteger())
    provider_code = Column(Integer())
    file_type_police = Column(Integer())
    accident_id = Column(BigInteger())
    engine_volume = Column(Integer())
    manufacturing_year = Column(Integer())
    driving_directions = Column(Integer())
    vehicle_status = Column(Integer())
    vehicle_attribution = Column(Integer())
    vehicle_type = Column(Integer())
    seats = Column(Integer())
    total_weight = Column(Integer())
    car_id = Column(Integer())
    accident_year = Column(Integer())
    accident_month = Column(Integer())
    vehicle_damage = Column(Integer())
    __table_args__ = (
        ForeignKeyConstraint(
            [accident_id, provider_code, accident_year],
            [AccidentMarker.id, AccidentMarker.provider_code, AccidentMarker.accident_year],
            ondelete="CASCADE",
        ),
        Index("accident_id_idx_vehicles", "accident_id", unique=False),
        Index("provider_and_id_idx_vehicles", "provider_and_id", unique=False),
        {},
    )

    def serialize(self):
        return {
            "id": self.id,
            "provider_code": self.provider_code,
            "accident_id": self.accident_id,
            "engine_volume": self.engine_volume,
            "manufacturing_year": self.manufacturing_year,
            "driving_directions": self.driving_directions,
            "vehicle_status": self.vehicle_status,
            "vehicle_attribution": self.vehicle_attribution,
            "vehicle_type": self.vehicle_type,
            "seats": self.seats,
            "total_weight": self.total_weight,
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


class GeneralPreferences(Base):
    __tablename__ = "general_preferences"
    user_id = Column(Integer(), ForeignKey("users.id"), primary_key=True)
    minimum_displayed_severity = Column(Integer(), nullable=True)
    resource_type = Column(String(64), nullable=True)

    def serialize(self):
        return {
            "user_id": self.user_id,
            "minimum_displayed_severity": self.minimum_displayed_severity,
            "resource_type": self.resource_type,
        }


class ReportPreferences(Base):
    __tablename__ = "report_preferences"
    user_id = Column(Integer(), ForeignKey("users.id"), primary_key=True)
    line_number = Column(Integer(), primary_key=True)
    historical_report = Column(Boolean(), default=False)
    how_many_months_back = Column(Integer(), nullable=True)
    latitude = Column(Float())
    longitude = Column(Float())
    radius = Column(Float())
    minimum_severity = Column(Integer())

    def serialize(self):
        return {
            "user_id": self.user_id,
            "line_number": self.line_number,
            "historical_report": self.historical_report,
            "how_many_months_back": self.how_many_months_back,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "radius": self.radius,
            "minimum_severity": self.minimum_severity,
        }


class School(Base):
    __tablename__ = "schools"
    id = Column(BigInteger(), primary_key=True, index=True)
    fcode_type = Column(Integer(), nullable=True)
    yishuv_symbol = Column(Integer(), nullable=True, index=True)
    yishuv_name = Column(Text(), nullable=True)
    school_name = Column(Text(), nullable=True)
    school_latin_name = Column(Text(), nullable=True)
    usg = Column(Integer(), nullable=True)
    usg_code = Column(Integer(), nullable=True)
    e_ord = Column(Float(), nullable=True)
    n_ord = Column(Float(), nullable=True)
    longitude = Column(Float(), nullable=True)
    latitude = Column(Float(), nullable=True)
    geom = Column(Geometry("POINT", srid=4326), index=True)
    data_year = Column(Integer(), nullable=True)
    prdct_ver = Column(DateTime, default=None)
    x = Column(Float(), nullable=True)
    y = Column(Float(), nullable=True)


class SchoolWithDescription(Base):
    __tablename__ = "schools_with_description"
    id = Column(BigInteger(), autoincrement=True, primary_key=True, index=True)
    data_year = Column(Integer(), nullable=True)
    school_id = Column(Integer(), nullable=True, index=True)
    school_name = Column(Text(), nullable=True)
    students_number = Column(Integer(), nullable=True)
    municipality_name = Column(Text(), nullable=True, index=True)
    yishuv_name = Column(Text(), nullable=True, index=True)
    sector = Column(Text(), nullable=True)
    inspection = Column(Text(), nullable=True)
    legal_status = Column(Text(), nullable=True)
    reporter = Column(Text(), nullable=True)
    geo_district = Column(Text(), nullable=True)
    education_type = Column(Text(), nullable=True)
    school_type = Column(Text(), nullable=True)
    institution_type = Column(Text(), nullable=True)
    lowest_grade = Column(Integer(), nullable=True)
    highest_grade = Column(Integer(), nullable=True)
    foundation_year = Column(Integer(), nullable=True)
    location_accuracy = Column(Text(), nullable=True)
    geom = Column(Geometry("POINT", srid=4326), index=True)
    x = Column(Float(), nullable=True)
    y = Column(Float(), nullable=True)
    longitude = Column(Float(), nullable=True)
    latitude = Column(Float(), nullable=True)


class InjuredAroundSchool(Base):
    __tablename__ = "injured_around_school"
    id = Column(BigInteger(), autoincrement=True, primary_key=True, index=True)
    school_id = Column(Integer(), nullable=True, index=True)
    school_name = Column(Text(), nullable=True)
    school_type = Column(Text(), nullable=True)
    school_longitude = Column(Float(), nullable=True)
    school_latitude = Column(Float(), nullable=True)
    school_yishuv_name = Column(Text(), nullable=True, index=True)
    school_anyway_link = Column(Text(), nullable=True)
    accident_year = Column(Integer(), nullable=True)
    distance_in_km = Column(Float(), nullable=True)
    killed_count = Column(Integer(), nullable=True)
    severly_injured_count = Column(Integer(), nullable=True)
    light_injured_count = Column(Integer(), nullable=True)
    total_injured_killed_count = Column(Integer(), nullable=True)
    rank_in_yishuv = Column(Integer(), nullable=True)


class InjuredAroundSchoolAllData(Base):
    __tablename__ = "injured_around_school_all_data"
    id = Column(BigInteger(), autoincrement=True, primary_key=True, index=True)
    school_id = Column(Float(), nullable=False, index=True)
    markers_provider_and_id = Column(BigInteger())
    markers_provider_code = Column(Float())
    markers_description = Column(Text())
    markers_accident_type = Column(Float())
    markers_accident_severity = Column(Float())
    markers_address = Column(Text())
    markers_location_accuracy = Column(Float())
    markers_road_type = Column(Float())
    markers_road_shape = Column(Float())
    markers_day_type = Column(Float())
    markers_police_unit = Column(Float())
    markers_mainStreet = Column(Text())
    markers_secondaryStreet = Column(Text())
    markers_junction = Column(Text())
    markers_one_lane = Column(Float())
    markers_multi_lane = Column(Float())
    markers_speed_limit = Column(Float())
    markers_road_intactness = Column(Float())
    markers_road_width = Column(Float())
    markers_road_sign = Column(Float())
    markers_road_light = Column(Float())
    markers_road_control = Column(Float())
    markers_weather = Column(Float())
    markers_road_surface = Column(Float())
    markers_road_object = Column(Float())
    markers_object_distance = Column(Float())
    markers_didnt_cross = Column(Float())
    markers_cross_mode = Column(Float())
    markers_cross_location = Column(Float())
    markers_cross_direction = Column(Float())
    markers_video_link = Column(Text())
    markers_road1 = Column(Float())
    markers_road2 = Column(Float())
    markers_km = Column(Float())
    markers_yishuv_symbol = Column(Float())
    markers_yishuv_name = Column(Text())
    markers_geo_area = Column(Float())
    markers_day_night = Column(Float())
    markers_day_in_week = Column(Float())
    markers_traffic_light = Column(Float())
    markers_region = Column(Float())
    markers_district = Column(Float())
    markers_natural_area = Column(Float())
    markers_municipal_status = Column(Float())
    markers_yishuv_shape = Column(Float())
    markers_street1 = Column(Float())
    markers_street1_hebrew = Column(Text())
    markers_street2 = Column(Float())
    markers_street2_hebrew = Column(Text())
    markers_house_number = Column(Float())
    markers_urban_intersection = Column(Float())
    markers_non_urban_intersection = Column(Float())
    markers_non_urban_intersection_hebrew = Column(Text())
    markers_accident_year = Column(Float())
    markers_accident_month = Column(Float())
    markers_accident_day = Column(Float())
    markers_accident_hour_raw = Column(Float())
    markers_accident_hour = Column(Float())
    markers_accident_minute = Column(Float())
    markers_x = Column(Float())
    markers_y = Column(Float())
    markers_vehicle_type_rsa = Column(Text())
    markers_violation_type_rsa = Column(Text())
    markers_geom = Column(Geometry("POINT"))
    involved_provider_and_id = Column(BigInteger())
    involved_provider_code = Column(Float())
    involved_accident_id = Column(BigInteger())
    involved_involved_type = Column(Float())
    involved_license_acquiring_date = Column(Float())
    involved_age_group = Column(Float())
    involved_sex = Column(Float())
    involved_vehicle_type = Column(Float())
    involved_safety_measures = Column(Float())
    involved_involve_yishuv_symbol = Column(Float())
    involved_involve_yishuv_name = Column(Text())
    involved_injury_severity = Column(Float())
    involved_injured_type = Column(Float())
    involved_injured_position = Column(Float())
    involved_population_type = Column(Float())
    involved_home_region = Column(Float())
    involved_home_district = Column(Float())
    involved_home_natural_area = Column(Float())
    involved_home_municipal_status = Column(Float())
    involved_home_yishuv_shape = Column(Float())
    involved_hospital_time = Column(Float())
    involved_medical_type = Column(Float())
    involved_release_dest = Column(Float())
    involved_safety_measures_use = Column(Float())
    involved_late_deceased = Column(Float())
    involved_car_id = Column(Float())
    involved_involve_id = Column(Float())
    involved_accident_year = Column(Float())
    involved_accident_month = Column(Float())
    involved_injury_severity_mais = Column(Float())


class ColumnsDescription(Base):
    __tablename__ = "columns_description"
    id = Column(Integer(), primary_key=True, index=True)
    year = Column(Integer(), primary_key=True, index=True)
    provider_code = Column(Integer(), primary_key=True, index=True)
    column_description = Column(Text(), nullable=True)


class TrafficVolume(Base):
    __tablename__ = "traffic_volume"
    id = Column(Integer(), primary_key=True, index=True)
    year = Column(Integer())
    road = Column(Integer())
    section = Column(Integer())
    lane = Column(Integer())
    month = Column(Integer())
    day = Column(Integer())
    day_of_week = Column(Integer())
    hour = Column(Integer())
    volume = Column(Integer())
    status = Column(Integer())
    duplicate_count = Column(Integer())


class PoliceUnit(Base):
    __tablename__ = "police_unit"
    id = Column(Integer(), primary_key=True, index=True)
    year = Column(Integer(), primary_key=True, index=True)
    provider_code = Column(Integer(), primary_key=True, index=True)
    police_unit_hebrew = Column(Text(), nullable=True)


class RoadType(Base):
    __tablename__ = "road_type"
    id = Column(Integer(), primary_key=True, index=True)
    year = Column(Integer(), primary_key=True, index=True)
    provider_code = Column(Integer(), primary_key=True, index=True)
    road_type_hebrew = Column(Text(), nullable=True)


class AccidentSeverity(Base):
    __tablename__ = "accident_severity"
    id = Column(Integer(), primary_key=True, index=True)
    year = Column(Integer(), primary_key=True, index=True)
    provider_code = Column(Integer(), primary_key=True, index=True)
    accident_severity_hebrew = Column(Text(), nullable=True)


class AccidentType(Base):
    __tablename__ = "accident_type"
    id = Column(Integer(), primary_key=True, index=True)
    year = Column(Integer(), primary_key=True, index=True)
    provider_code = Column(Integer(), primary_key=True, index=True)
    accident_type_hebrew = Column(Text(), nullable=True)


class RoadShape(Base):
    __tablename__ = "road_shape"
    id = Column(Integer(), primary_key=True, index=True)
    year = Column(Integer(), primary_key=True, index=True)
    provider_code = Column(Integer(), primary_key=True, index=True)
    road_shape_hebrew = Column(Text(), nullable=True)


class OneLane(Base):
    __tablename__ = "one_lane"
    id = Column(Integer(), primary_key=True, index=True)
    year = Column(Integer(), primary_key=True, index=True)
    provider_code = Column(Integer(), primary_key=True, index=True)
    one_lane_hebrew = Column(Text(), nullable=True)


class MultiLane(Base):
    __tablename__ = "multi_lane"
    id = Column(Integer(), primary_key=True, index=True)
    year = Column(Integer(), primary_key=True, index=True)
    provider_code = Column(Integer(), primary_key=True, index=True)
    multi_lane_hebrew = Column(Text(), nullable=True)


class SpeedLimit(Base):
    __tablename__ = "speed_limit"
    id = Column(Integer(), primary_key=True, index=True)
    year = Column(Integer(), primary_key=True, index=True)
    provider_code = Column(Integer(), primary_key=True, index=True)
    speed_limit_hebrew = Column(Text(), nullable=True)


class RoadIntactness(Base):
    __tablename__ = "road_intactness"
    id = Column(Integer(), primary_key=True, index=True)
    year = Column(Integer(), primary_key=True, index=True)
    provider_code = Column(Integer(), primary_key=True, index=True)
    road_intactness_hebrew = Column(Text(), nullable=True)


class RoadWidth(Base):
    __tablename__ = "road_width"
    id = Column(Integer(), primary_key=True, index=True)
    year = Column(Integer(), primary_key=True, index=True)
    provider_code = Column(Integer(), primary_key=True, index=True)
    road_width_hebrew = Column(Text(), nullable=True)


class RoadSign(Base):
    __tablename__ = "road_sign"
    id = Column(Integer(), primary_key=True, index=True)
    year = Column(Integer(), primary_key=True, index=True)
    provider_code = Column(Integer(), primary_key=True, index=True)
    road_sign_hebrew = Column(Text(), nullable=True)


class RoadLight(Base):
    __tablename__ = "road_light"
    id = Column(Integer(), primary_key=True, index=True)
    year = Column(Integer(), primary_key=True, index=True)
    provider_code = Column(Integer(), primary_key=True, index=True)
    road_light_hebrew = Column(Text(), nullable=True)


class RoadControl(Base):
    __tablename__ = "road_control"
    id = Column(Integer(), primary_key=True, index=True)
    year = Column(Integer(), primary_key=True, index=True)
    provider_code = Column(Integer(), primary_key=True, index=True)
    road_control_hebrew = Column(Text(), nullable=True)


class Weather(Base):
    __tablename__ = "weather"
    id = Column(Integer(), primary_key=True, index=True)
    year = Column(Integer(), primary_key=True, index=True)
    provider_code = Column(Integer(), primary_key=True, index=True)
    weather_hebrew = Column(Text(), nullable=True)


class RoadSurface(Base):
    __tablename__ = "road_surface"
    id = Column(Integer(), primary_key=True, index=True)
    year = Column(Integer(), primary_key=True, index=True)
    provider_code = Column(Integer(), primary_key=True, index=True)
    road_surface_hebrew = Column(Text(), nullable=True)


class RoadObjecte(Base):
    __tablename__ = "road_object"
    id = Column(Integer(), primary_key=True, index=True)
    year = Column(Integer(), primary_key=True, index=True)
    provider_code = Column(Integer(), primary_key=True, index=True)
    road_object_hebrew = Column(Text(), nullable=True)


class ObjectDistance(Base):
    __tablename__ = "object_distance"
    id = Column(Integer(), primary_key=True, index=True)
    year = Column(Integer(), primary_key=True, index=True)
    provider_code = Column(Integer(), primary_key=True, index=True)
    object_distance_hebrew = Column(Text(), nullable=True)


class DidntCross(Base):
    __tablename__ = "didnt_cross"
    id = Column(Integer(), primary_key=True, index=True)
    year = Column(Integer(), primary_key=True, index=True)
    provider_code = Column(Integer(), primary_key=True, index=True)
    didnt_cross_hebrew = Column(Text(), nullable=True)


class CrossMode(Base):
    __tablename__ = "cross_mode"
    id = Column(Integer(), primary_key=True, index=True)
    year = Column(Integer(), primary_key=True, index=True)
    provider_code = Column(Integer(), primary_key=True, index=True)
    cross_mode_hebrew = Column(Text(), nullable=True)


class CrossLocation(Base):
    __tablename__ = "cross_location"
    id = Column(Integer(), primary_key=True, index=True)
    year = Column(Integer(), primary_key=True, index=True)
    provider_code = Column(Integer(), primary_key=True, index=True)
    cross_location_hebrew = Column(Text(), nullable=True)


class CrossDirection(Base):
    __tablename__ = "cross_direction"
    id = Column(Integer(), primary_key=True, index=True)
    year = Column(Integer(), primary_key=True, index=True)
    provider_code = Column(Integer(), primary_key=True, index=True)
    cross_direction_hebrew = Column(Text(), nullable=True)


class DrivingDirections(Base):
    __tablename__ = "driving_directions"
    id = Column(Integer(), primary_key=True, index=True)
    year = Column(Integer(), primary_key=True, index=True)
    provider_code = Column(Integer(), primary_key=True, index=True)
    driving_directions_hebrew = Column(Text(), nullable=True)


class VehicleStatus(Base):
    __tablename__ = "vehicle_status"
    id = Column(Integer(), primary_key=True, index=True)
    year = Column(Integer(), primary_key=True, index=True)
    provider_code = Column(Integer(), primary_key=True, index=True)
    vehicle_status_hebrew = Column(Text(), nullable=True)


class InvolvedType(Base):
    __tablename__ = "involved_type"
    id = Column(Integer(), primary_key=True, index=True)
    year = Column(Integer(), primary_key=True, index=True)
    provider_code = Column(Integer(), primary_key=True, index=True)
    involved_type_hebrew = Column(Text(), nullable=True)


class SafetyMeasures(Base):
    __tablename__ = "safety_measures"
    id = Column(Integer(), primary_key=True, index=True)
    year = Column(Integer(), primary_key=True, index=True)
    provider_code = Column(Integer(), primary_key=True, index=True)
    safety_measures_hebrew = Column(Text(), nullable=True)


class InjurySeverity(Base):
    __tablename__ = "injury_severity"
    id = Column(Integer(), primary_key=True, index=True)
    year = Column(Integer(), primary_key=True, index=True)
    provider_code = Column(Integer(), primary_key=True, index=True)
    injury_severity_hebrew = Column(Text(), nullable=True)


class DayType(Base):
    __tablename__ = "day_type"
    id = Column(Integer(), primary_key=True, index=True)
    year = Column(Integer(), primary_key=True, index=True)
    provider_code = Column(Integer(), primary_key=True, index=True)
    day_type_hebrew = Column(Text(), nullable=True)


class DayNight(Base):
    __tablename__ = "day_night"
    id = Column(Integer(), primary_key=True, index=True)
    year = Column(Integer(), primary_key=True, index=True)
    provider_code = Column(Integer(), primary_key=True, index=True)
    day_night_hebrew = Column(Text(), nullable=True)


class DayInWeek(Base):
    __tablename__ = "day_in_week"
    id = Column(Integer(), primary_key=True, index=True)
    year = Column(Integer(), primary_key=True, index=True)
    provider_code = Column(Integer(), primary_key=True, index=True)
    day_in_week_hebrew = Column(Text(), nullable=True)


class TrafficLight(Base):
    __tablename__ = "traffic_light"
    id = Column(Integer(), primary_key=True, index=True)
    year = Column(Integer(), primary_key=True, index=True)
    provider_code = Column(Integer(), primary_key=True, index=True)
    traffic_light_hebrew = Column(Text(), nullable=True)


class VehicleAttribution(Base):
    __tablename__ = "vehicle_attribution"
    id = Column(Integer(), primary_key=True, index=True)
    year = Column(Integer(), primary_key=True, index=True)
    provider_code = Column(Integer(), primary_key=True, index=True)
    vehicle_attribution_hebrew = Column(Text(), nullable=True)


class VehicleType(Base):
    __tablename__ = "vehicle_type"
    id = Column(Integer(), primary_key=True, index=True)
    year = Column(Integer(), primary_key=True, index=True)
    provider_code = Column(Integer(), primary_key=True, index=True)
    vehicle_type_hebrew = Column(Text(), nullable=True)


class InjuredType(Base):
    __tablename__ = "injured_type"
    id = Column(Integer(), primary_key=True, index=True)
    year = Column(Integer(), primary_key=True, index=True)
    provider_code = Column(Integer(), primary_key=True, index=True)
    injured_type_hebrew = Column(Text(), nullable=True)


class InjuredPosition(Base):
    __tablename__ = "injured_position"
    id = Column(Integer(), primary_key=True, index=True)
    year = Column(Integer(), primary_key=True, index=True)
    provider_code = Column(Integer(), primary_key=True, index=True)
    injured_position_hebrew = Column(Text(), nullable=True)


class AccidentMonth(Base):
    __tablename__ = "accident_month"
    id = Column(Integer(), primary_key=True, index=True)
    year = Column(Integer(), primary_key=True, index=True)
    provider_code = Column(Integer(), primary_key=True, index=True)
    accident_month_hebrew = Column(Text(), nullable=True)


class PopulationType(Base):
    __tablename__ = "population_type"
    id = Column(Integer(), primary_key=True, index=True)
    year = Column(Integer(), primary_key=True, index=True)
    provider_code = Column(Integer(), primary_key=True, index=True)
    population_type_hebrew = Column(Text(), nullable=True)


class Sex(Base):
    __tablename__ = "sex"
    id = Column(Integer(), primary_key=True, index=True)
    year = Column(Integer(), primary_key=True, index=True)
    provider_code = Column(Integer(), primary_key=True, index=True)
    sex_hebrew = Column(Text(), nullable=True)


class GeoArea(Base):
    __tablename__ = "geo_area"
    id = Column(Integer(), primary_key=True, index=True)
    year = Column(Integer(), primary_key=True, index=True)
    provider_code = Column(Integer(), primary_key=True, index=True)
    geo_area_hebrew = Column(Text(), nullable=True)


class Region(Base):
    __tablename__ = "region"
    id = Column(Integer(), primary_key=True, index=True)
    year = Column(Integer(), primary_key=True, index=True)
    provider_code = Column(Integer(), primary_key=True, index=True)
    region_hebrew = Column(Text(), nullable=True)


class MunicipalStatus(Base):
    __tablename__ = "municipal_status"
    id = Column(Integer(), primary_key=True, index=True)
    year = Column(Integer(), primary_key=True, index=True)
    provider_code = Column(Integer(), primary_key=True, index=True)
    municipal_status_hebrew = Column(Text(), nullable=True)


class District(Base):
    __tablename__ = "district"
    id = Column(Integer(), primary_key=True, index=True)
    year = Column(Integer(), primary_key=True, index=True)
    provider_code = Column(Integer(), primary_key=True, index=True)
    district_hebrew = Column(Text(), nullable=True)


class NaturalArea(Base):
    __tablename__ = "natural_area"
    id = Column(Integer(), primary_key=True, index=True)
    year = Column(Integer(), primary_key=True, index=True)
    provider_code = Column(Integer(), primary_key=True, index=True)
    natural_area_hebrew = Column(Text(), nullable=True)


class YishuvShape(Base):
    __tablename__ = "yishuv_shape"
    id = Column(Integer(), primary_key=True, index=True)
    year = Column(Integer(), primary_key=True, index=True)
    provider_code = Column(Integer(), primary_key=True, index=True)
    yishuv_shape_hebrew = Column(Text(), nullable=True)


class AgeGroup(Base):
    __tablename__ = "age_group"
    id = Column(Integer(), primary_key=True, index=True)
    year = Column(Integer(), primary_key=True, index=True)
    provider_code = Column(Integer(), primary_key=True, index=True)
    age_group_hebrew = Column(Text(), nullable=True)


class AccidentHourRaw(Base):
    __tablename__ = "accident_hour_raw"
    id = Column(Integer(), primary_key=True, index=True)
    year = Column(Integer(), primary_key=True, index=True)
    provider_code = Column(Integer(), primary_key=True, index=True)
    accident_hour_raw_hebrew = Column(Text(), nullable=True)


class EngineVolume(Base):
    __tablename__ = "engine_volume"
    id = Column(Integer(), primary_key=True, index=True)
    year = Column(Integer(), primary_key=True, index=True)
    provider_code = Column(Integer(), primary_key=True, index=True)
    engine_volume_hebrew = Column(Text(), nullable=True)


class TotalWeight(Base):
    __tablename__ = "total_weight"
    id = Column(Integer(), primary_key=True, index=True)
    year = Column(Integer(), primary_key=True, index=True)
    provider_code = Column(Integer(), primary_key=True, index=True)
    total_weight_hebrew = Column(Text(), nullable=True)


class HospitalTime(Base):
    __tablename__ = "hospital_time"
    id = Column(Integer(), primary_key=True, index=True)
    year = Column(Integer(), primary_key=True, index=True)
    provider_code = Column(Integer(), primary_key=True, index=True)
    hospital_time_hebrew = Column(Text(), nullable=True)


class MedicalType(Base):
    __tablename__ = "medical_type"
    id = Column(Integer(), primary_key=True, index=True)
    year = Column(Integer(), primary_key=True, index=True)
    provider_code = Column(Integer(), primary_key=True, index=True)
    medical_type_hebrew = Column(Text(), nullable=True)


class ReleaseDest(Base):
    __tablename__ = "release_dest"
    id = Column(Integer(), primary_key=True, index=True)
    year = Column(Integer(), primary_key=True, index=True)
    provider_code = Column(Integer(), primary_key=True, index=True)
    release_dest_hebrew = Column(Text(), nullable=True)


class SafetyMeasuresUse(Base):
    __tablename__ = "safety_measures_use"
    id = Column(Integer(), primary_key=True, index=True)
    year = Column(Integer(), primary_key=True, index=True)
    provider_code = Column(Integer(), primary_key=True, index=True)
    safety_measures_use_hebrew = Column(Text(), nullable=True)


class LateDeceased(Base):
    __tablename__ = "late_deceased"
    id = Column(Integer(), primary_key=True, index=True)
    year = Column(Integer(), primary_key=True, index=True)
    provider_code = Column(Integer(), primary_key=True, index=True)
    late_deceased_hebrew = Column(Text(), nullable=True)


class LocationAccuracy(Base):
    __tablename__ = "location_accuracy"
    id = Column(Integer(), primary_key=True, index=True)
    year = Column(Integer(), primary_key=True, index=True)
    provider_code = Column(Integer(), primary_key=True, index=True)
    location_accuracy_hebrew = Column(Text(), nullable=True)


class ProviderCode(Base):
    __tablename__ = "provider_code"
    id = Column(Integer(), primary_key=True, index=True)
    provider_code_hebrew = Column(Text(), nullable=True)


class VehicleDamage(Base):
    __tablename__ = "vehicle_damage"
    id = Column(Integer(), primary_key=True, index=True)
    year = Column(Integer(), primary_key=True, index=True)
    provider_code = Column(Integer(), primary_key=True, index=True)
    vehicle_damage_hebrew = Column(Text(), nullable=True)


class AccidentMarkerView(Base):
    __tablename__ = "markers_hebrew"
    id = Column(BigInteger(), primary_key=True)
    provider_and_id = Column(BigInteger())
    provider_code = Column(Integer(), primary_key=True)
    provider_code_hebrew = Column(Text())
    file_type_police = Column(Integer())
    accident_type = Column(Integer(), index=True)
    accident_type_hebrew = Column(Text(), index=True)
    accident_severity = Column(Integer(), index=True)
    accident_severity_hebrew = Column(Text(), index=True)
    accident_timestamp = Column(DateTime, default=None, index=True)
    location_accuracy = Column(Integer())
    location_accuracy_hebrew = Column(Text())
    road_type = Column(Integer())
    road_type_hebrew = Column(Text())
    road_shape = Column(Integer())
    road_shape_hebrew = Column(Text())
    day_type = Column(Integer())
    day_type_hebrew = Column(Text())
    police_unit = Column(Integer())
    police_unit_hebrew = Column(Text())
    one_lane = Column(Integer())
    one_lane_hebrew = Column(Text())
    multi_lane = Column(Integer())
    multi_lane_hebrew = Column(Text())
    speed_limit = Column(Integer())
    speed_limit_hebrew = Column(Text())
    road_intactness = Column(Integer())
    road_intactness_hebrew = Column(Text())
    road_width = Column(Integer())
    road_width_hebrew = Column(Text())
    road_sign = Column(Integer())
    road_sign_hebrew = Column(Text())
    road_light = Column(Integer())
    road_light_hebrew = Column(Text())
    road_control = Column(Integer())
    road_control_hebrew = Column(Text())
    weather = Column(Integer())
    weather_hebrew = Column(Text())
    road_surface = Column(Integer())
    road_surface_hebrew = Column(Text())
    road_object = Column(Integer())
    road_object_hebrew = Column(Text())
    object_distance = Column(Integer())
    object_distance_hebrew = Column(Text())
    didnt_cross = Column(Integer())
    didnt_cross_hebrew = Column(Text())
    cross_mode = Column(Integer())
    cross_mode_hebrew = Column(Text())
    cross_location = Column(Integer())
    cross_location_hebrew = Column(Text())
    cross_direction = Column(Integer())
    cross_direction_hebrew = Column(Text())
    road1 = Column(Integer(), index=True)
    road2 = Column(Integer(), index=True)
    km = Column(Float())
    km_raw = Column(Text())
    km_accurate = Column(Boolean())
    road_segment_id = Column(Integer(), index=True)
    road_segment_number = Column(Integer(), index=True)
    road_segment_name = Column(Text(), index=True)
    road_segment_from_km = Column(Float())
    road_segment_to_km = Column(Float())
    road_segment_length_km = Column(Float())
    yishuv_symbol = Column(Integer())
    yishuv_name = Column(Text(), index=True)
    geo_area = Column(Integer())
    geo_area_hebrew = Column(Text())
    day_night = Column(Integer())
    day_night_hebrew = Column(Text())
    day_in_week = Column(Integer())
    day_in_week_hebrew = Column(Text())
    traffic_light = Column(Integer())
    traffic_light_hebrew = Column(Text())
    region = Column(Integer())
    region_hebrew = Column(Text())
    district = Column(Integer())
    district_hebrew = Column(Text())
    natural_area = Column(Integer())
    natural_area_hebrew = Column(Text())
    municipal_status = Column(Integer())
    municipal_status_hebrew = Column(Text())
    yishuv_shape = Column(Integer())
    yishuv_shape_hebrew = Column(Text())
    street1 = Column(Integer())
    street1_hebrew = Column(Text(), index=True)
    street2 = Column(Integer())
    street2_hebrew = Column(Text(), index=True)
    house_number = Column(Integer())
    non_urban_intersection = Column(Integer())
    non_urban_intersection_hebrew = Column(Text())
    non_urban_intersection_by_junction_number = Column(Text())
    urban_intersection = Column(Integer())
    accident_year = Column(Integer(), primary_key=True, index=True)
    accident_month = Column(Integer())
    accident_day = Column(Integer())
    accident_hour_raw = Column(Integer())
    accident_hour_raw_hebrew = Column(Text())
    accident_hour = Column(Integer())
    accident_minute = Column(Integer())
    geom = Column(Geometry("POINT"), index=True)
    latitude = Column(Float())
    longitude = Column(Float())
    x = Column(Float())
    y = Column(Float())

    def serialize(self):
        return {
            "id": self.id,
            "provider_code": self.provider_code,
            "provider_code_hebrew": self.provider_code_hebrew,
            "accident_type": self.accident_type,
            "accident_type_hebrew": self.accident_type_hebrew,
            "accident_severity": self.accident_severity,
            "accident_severity_hebrew": self.accident_severity_hebrew,
            "location_accuracy": self.location_accuracy,
            "location_accuracy_hebrew": self.location_accuracy_hebrew,
            "road_type": self.road_type,
            "road_type_hebrew": self.road_type_hebrew,
            "road_shape": self.road_shape,
            "road_shape_hebrew": self.road_shape_hebrew,
            "day_type": self.day_type,
            "day_type_hebrew": self.day_type_hebrew,
            "police_unit": self.police_unit,
            "police_unit_hebrew": self.police_unit_hebrew,
            "one_lane": self.one_lane,
            "one_lane_hebrew": self.one_lane_hebrew,
            "multi_lane": self.multi_lane,
            "multi_lane_hebrew": self.multi_lane_hebrew,
            "speed_limit": self.speed_limit,
            "speed_limit_hebrew": self.speed_limit_hebrew,
            "road_intactness": self.road_intactness,
            "road_intactness_hebrew": self.road_intactness_hebrew,
            "road_width": self.road_width,
            "road_width_hebrew": self.road_width_hebrew,
            "road_sign": self.road_sign,
            "road_sign_hebrew": self.road_sign_hebrew,
            "road_light": self.road_light,
            "road_light_hebrew": self.road_light_hebrew,
            "road_control": self.road_control,
            "road_control_hebrew": self.road_control_hebrew,
            "weather": self.weather,
            "weather_hebrew": self.weather_hebrew,
            "road_surface": self.road_surface,
            "road_surface_hebrew": self.road_surface_hebrew,
            "road_object": self.road_object,
            "road_object_hebrew": self.road_object_hebrew,
            "object_distance": self.object_distance,
            "object_distance_hebrew": self.object_distance_hebrew,
            "didnt_cross": self.didnt_cross,
            "didnt_cross_hebrew": self.didnt_cross_hebrew,
            "cross_mode": self.cross_mode,
            "cross_mode_hebrew": self.cross_mode_hebrew,
            "cross_location": self.cross_location,
            "cross_location_hebrew": self.cross_location_hebrew,
            "cross_direction": self.cross_direction,
            "cross_direction_hebrew": self.cross_direction_hebrew,
            "road1": self.road1,
            "road2": self.road2,
            "km": self.km,
            "km_raw": self.km_raw,
            "km_accurate": self.km_accurate,
            "yishuv_symbol": self.km_accurate,
            "yishuv_name": self.yishuv_name,
            "geo_area": self.geo_area,
            "geo_area_hebrew": self.geo_area_hebrew,
            "day_night": self.day_night,
            "day_night_hebrew": self.day_night_hebrew,
            "day_in_week": self.day_in_week,
            "day_in_week_hebrew": self.day_in_week_hebrew,
            "traffic_light": self.traffic_light,
            "traffic_light_hebrew": self.traffic_light_hebrew,
            "region": self.region,
            "region_hebrew": self.region_hebrew,
            "district": self.district,
            "district_hebrew": self.district_hebrew,
            "natural_area": self.natural_area,
            "natural_area_hebrew": self.natural_area_hebrew,
            "municipal_status": self.municipal_status,
            "municipal_status_hebrew": self.municipal_status_hebrew,
            "yishuv_shape": self.yishuv_shape,
            "yishuv_shape_hebrew": self.yishuv_shape_hebrew,
            "street1": self.street1,
            "street1_hebrew": self.street1_hebrew,
            "street2": self.street2,
            "street2_hebrew": self.street2_hebrew,
            "non_urban_intersection_hebrew": self.non_urban_intersection_hebrew,
            "accident_year": self.accident_year,
            "accident_month": self.accident_month,
            "accident_day": self.accident_day,
            "accident_hour_raw": self.accident_hour_raw,
            "accident_hour_raw_hebrew": self.accident_hour_raw_hebrew,
            "accident_hour": self.accident_hour,
            "accident_minute": self.accident_minute,
            "geom": self.geom,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "x": self.x,
            "y": self.y,
        }


class RoadSegments(Base):
    __tablename__ = "road_segments"
    id = Column(Integer(), primary_key=True)
    segment_id = Column(Integer())
    road = Column(Integer())
    segment = Column(Integer())
    from_km = Column(Float())
    from_name = Column(Text())
    to_km = Column(Float())
    to_name = Column(Text())


class ReportProblem(Base):
    __tablename__ = "report_problem"
    id = Column(BigInteger(), autoincrement=True, primary_key=True, index=True)
    latitude = Column(Float())
    longitude = Column(Float())
    problem_description = Column(Text())
    signs_on_the_road_not_clear = Column(Boolean())
    signs_problem = Column(Boolean())
    pothole = Column(Boolean())
    no_light = Column(Boolean())
    no_sign = Column(Boolean())
    crossing_missing = Column(Boolean())
    sidewalk_is_blocked = Column(Boolean())
    street_light_issue = Column(Boolean())
    road_hazard = Column(Boolean())
    first_name = Column(String(50))
    last_name = Column(String(50))
    phone_number = Column(String(50))
    email = Column(String(100))
    send_to_municipality = Column(Boolean())
    image_data = Column(String())
    personal_id = Column(String(20))


class InvolvedMarkerView(Base):
    __tablename__ = "involved_markers_hebrew"
    accident_id = Column(BigInteger(), primary_key=True)
    provider_and_id = Column(BigInteger())
    provider_code = Column(Integer(), primary_key=True)
    file_type_police = Column(Integer())
    involved_type = Column(Integer(), index=True)
    involved_type_hebrew = Column(Text(), index=True)
    license_acquiring_date = Column(Integer())
    age_group = Column(Integer())
    age_group_hebrew = Column(Text())
    sex = Column(Integer())
    sex_hebrew = Column(Text())
    involve_vehicle_type = Column(Integer(), index=True)
    involve_vehicle_type_hebrew = Column(Text(), index=True)
    safety_measures = Column(Integer())
    safety_measures_hebrew = Column(Text())
    involve_yishuv_symbol = Column(Integer())
    involve_yishuv_name = Column(Text())
    injury_severity = Column(Integer())
    injury_severity_hebrew = Column(Text())
    injured_type = Column(Integer())
    injured_type_hebrew = Column(Text())
    injured_position = Column(Integer())
    injured_position_hebrew = Column(Text())
    population_type = Column(Integer())
    population_type_hebrew = Column(Text())
    involve_home_region = Column(Integer())
    involve_home_region_hebrew = Column(Text())
    involve_home_district = Column(Integer())
    involve_home_district_hebrew = Column(Text())
    involve_home_natural_area = Column(Integer())
    involve_home_natural_area_hebrew = Column(Text())
    involve_home_municipal_status = Column(Integer())
    involve_home_municipal_status_hebrew = Column(Text())
    involve_home_yishuv_shape = Column(Integer())
    involve_home_yishuv_shape_hebrew = Column(Text())
    hospital_time = Column(Integer())
    hospital_time_hebrew = Column(Text())
    medical_type = Column(Integer())
    medical_type_hebrew = Column(Text())
    release_dest = Column(Integer())
    release_dest_hebrew = Column(Text())
    safety_measures_use = Column(Integer())
    safety_measures_use_hebrew = Column(Text())
    late_deceased = Column(Integer())
    late_deceased_hebrew = Column(Text())
    car_id = Column(Integer())
    involve_id = Column(Integer(), primary_key=True)
    accident_year = Column(Integer(), index=True, primary_key=True)
    accident_month = Column(Integer())
    provider_code_hebrew = Column(Text())
    accident_timestamp = Column(DateTime, default=None, index=True)
    accident_type = Column(Integer())
    accident_type_hebrew = Column(Text())
    accident_severity = Column(Integer(), index=True)
    accident_severity_hebrew = Column(Text(), index=True)
    location_accuracy = Column(Integer())
    location_accuracy_hebrew = Column(Text())
    road_type = Column(Integer(), index=True)
    road_type_hebrew = Column(Text(), index=True)
    road_shape = Column(Integer())
    road_shape_hebrew = Column(Text())
    day_type = Column(Integer())
    day_type_hebrew = Column(Text())
    police_unit = Column(Integer())
    police_unit_hebrew = Column(Text())
    one_lane = Column(Integer())
    one_lane_hebrew = Column(Text())
    multi_lane = Column(Integer())
    multi_lane_hebrew = Column(Text())
    speed_limit = Column(Integer())
    speed_limit_hebrew = Column(Text())
    road_intactness = Column(Integer())
    road_intactness_hebrew = Column(Text())
    road_width = Column(Integer())
    road_width_hebrew = Column(Text())
    road_sign = Column(Integer())
    road_sign_hebrew = Column(Text())
    road_light = Column(Integer())
    road_light_hebrew = Column(Text())
    road_control = Column(Integer())
    road_control_hebrew = Column(Text())
    weather = Column(Integer())
    weather_hebrew = Column(Text())
    road_surface = Column(Integer())
    road_surface_hebrew = Column(Text())
    road_object = Column(Integer())
    road_object_hebrew = Column(Text())
    object_distance = Column(Integer())
    object_distance_hebrew = Column(Text())
    didnt_cross = Column(Integer())
    didnt_cross_hebrew = Column(Text())
    cross_mode = Column(Integer())
    cross_mode_hebrew = Column(Text())
    cross_location = Column(Integer())
    cross_location_hebrew = Column(Text())
    cross_direction = Column(Integer())
    cross_direction_hebrew = Column(Text())
    road1 = Column(Integer(), index=True)
    road2 = Column(Integer(), index=True)
    km = Column(Float())
    km_raw = Column(Text())
    km_accurate = Column(Boolean())
    road_segment_id = Column(Integer(), index=True)
    road_segment_number = Column(Integer(), index=True)
    road_segment_name = Column(Text(), index=True)
    road_segment_from_km = Column(Float())
    road_segment_to_km = Column(Float())
    road_segment_length_km = Column(Float())
    accident_yishuv_symbol = Column(Integer())
    accident_yishuv_name = Column(Text(), index=True)
    geo_area = Column(Integer())
    geo_area_hebrew = Column(Text())
    day_night = Column(Integer())
    day_night_hebrew = Column(Text())
    day_in_week = Column(Integer())
    day_in_week_hebrew = Column(Text())
    traffic_light = Column(Integer())
    traffic_light_hebrew = Column(Text())
    accident_region = Column(Integer())
    accident_region_hebrew = Column(Text())
    accident_district = Column(Integer())
    accident_district_hebrew = Column(Text())
    accident_natural_area = Column(Integer())
    accident_natural_area_hebrew = Column(Text())
    accident_municipal_status = Column(Integer())
    accident_municipal_status_hebrew = Column(Text())
    accident_yishuv_shape = Column(Integer())
    accident_yishuv_shape_hebrew = Column(Text())
    street1 = Column(Integer())
    street1_hebrew = Column(Text(), index=True)
    street2 = Column(Integer())
    street2_hebrew = Column(Text(), index=True)
    non_urban_intersection = Column(Integer())
    non_urban_intersection_hebrew = Column(Text())
    non_urban_intersection_by_junction_number = Column(Text())
    accident_day = Column(Integer())
    accident_hour_raw = Column(Integer())
    accident_hour_raw_hebrew = Column(Text())
    accident_hour = Column(Integer())
    accident_minute = Column(Integer())
    geom = Column(Geometry("POINT"), index=True)
    latitude = Column(Float())
    longitude = Column(Float())
    x = Column(Float())
    y = Column(Float())
    engine_volume = Column(Integer())
    engine_volume_hebrew = Column(Text())
    manufacturing_year = Column(Integer())
    driving_directions = Column(Integer())
    driving_directions_hebrew = Column(Text())
    vehicle_status = Column(Integer())
    vehicle_status_hebrew = Column(Text())
    vehicle_attribution = Column(Integer())
    vehicle_attribution_hebrew = Column(Text())
    seats = Column(Integer())
    total_weight = Column(Integer())
    total_weight_hebrew = Column(Text())
    vehicle_vehicle_type = Column(Integer())
    vehicle_vehicle_type_hebrew = Column(Text())
    vehicle_damage = Column(Integer())
    vehicle_damage_hebrew = Column(Text())


class InvolvedView(Base):
    __tablename__ = "involved_hebrew"
    accident_id = Column(BigInteger(), primary_key=True)
    provider_and_id = Column(BigInteger())
    provider_code = Column(Integer(), primary_key=True)
    file_type_police = Column(Integer())
    involved_type = Column(Integer(), index=True)
    involved_type_hebrew = Column(Text(), index=True)
    license_acquiring_date = Column(Integer())
    age_group = Column(Integer())
    age_group_hebrew = Column(Text())
    sex = Column(Integer())
    sex_hebrew = Column(Text())
    vehicle_type = Column(Integer(), index=True)
    vehicle_type_hebrew = Column(Text(), index=True)
    safety_measures = Column(Integer())
    safety_measures_hebrew = Column(Text())
    involve_yishuv_symbol = Column(Integer())
    involve_yishuv_name = Column(Text())
    injury_severity = Column(Integer())
    injury_severity_hebrew = Column(Text())
    injured_type = Column(Integer())
    injured_type_hebrew = Column(Text())
    injured_position = Column(Integer())
    injured_position_hebrew = Column(Text())
    population_type = Column(Integer())
    population_type_hebrew = Column(Text())
    home_region = Column(Integer())
    home_region_hebrew = Column(Text())
    home_district = Column(Integer())
    home_district_hebrew = Column(Text())
    home_natural_area = Column(Integer())
    home_natural_area_hebrew = Column(Text())
    home_municipal_status = Column(Integer())
    home_municipal_status_hebrew = Column(Text())
    home_yishuv_shape = Column(Integer())
    home_yishuv_shape_hebrew = Column(Text())
    hospital_time = Column(Integer())
    hospital_time_hebrew = Column(Text())
    medical_type = Column(Integer())
    medical_type_hebrew = Column(Text())
    release_dest = Column(Integer())
    release_dest_hebrew = Column(Text())
    safety_measures_use = Column(Integer())
    safety_measures_use_hebrew = Column(Text())
    late_deceased = Column(Integer())
    late_deceased_hebrew = Column(Text())
    car_id = Column(Integer())
    involve_id = Column(Integer(), primary_key=True)
    accident_year = Column(Integer(), primary_key=True, index=True)
    accident_month = Column(Integer())


class VehiclesView(Base):
    __tablename__ = "vehicles_hebrew"
    id = Column(BigInteger(), primary_key=True)
    accident_id = Column(BigInteger(), primary_key=True)
    provider_and_id = Column(BigInteger())
    provider_code = Column(Integer(), primary_key=True)
    file_type_police = Column(Integer())
    car_id = Column(Integer())
    engine_volume = Column(Integer())
    engine_volume_hebrew = Column(Text())
    manufacturing_year = Column(Integer())
    driving_directions = Column(Integer())
    driving_directions_hebrew = Column(Text())
    vehicle_status = Column(Integer())
    vehicle_status_hebrew = Column(Text())
    vehicle_attribution = Column(Integer())
    vehicle_attribution_hebrew = Column(Text())
    seats = Column(Integer())
    total_weight = Column(Integer())
    total_weight_hebrew = Column(Text())
    vehicle_type = Column(Integer(), index=True)
    vehicle_type_hebrew = Column(Text(), index=True)
    vehicle_damage = Column(Integer())
    vehicle_damage_hebrew = Column(Text())
    accident_year = Column(Integer(), primary_key=True, index=True)
    accident_month = Column(Integer())


class VehicleMarkerView(Base):
    __tablename__ = "vehicles_markers_hebrew"
    accident_timestamp = Column(DateTime, default=None)
    accident_type = Column(Integer(), index=True)
    accident_type_hebrew = Column(Text(), index=True)
    accident_severity = Column(Integer(), index=True)
    accident_severity_hebrew = Column(Text(), index=True)
    location_accuracy = Column(Integer())
    location_accuracy_hebrew = Column(Text())
    road_type = Column(Integer())
    road_type_hebrew = Column(Text())
    road_shape = Column(Integer())
    road_shape_hebrew = Column(Text())
    day_type = Column(Integer())
    day_type_hebrew = Column(Text())
    police_unit = Column(Integer())
    police_unit_hebrew = Column(Text())
    one_lane = Column(Integer())
    one_lane_hebrew = Column(Text())
    multi_lane = Column(Integer())
    multi_lane_hebrew = Column(Text())
    speed_limit = Column(Integer())
    speed_limit_hebrew = Column(Text())
    road_intactness = Column(Integer())
    road_intactness_hebrew = Column(Text())
    road_width = Column(Integer())
    road_width_hebrew = Column(Text())
    road_sign = Column(Integer())
    road_sign_hebrew = Column(Text())
    road_light = Column(Integer())
    road_light_hebrew = Column(Text())
    road_control = Column(Integer())
    road_control_hebrew = Column(Text())
    weather = Column(Integer())
    weather_hebrew = Column(Text())
    road_surface = Column(Integer())
    road_surface_hebrew = Column(Text())
    road_object = Column(Integer())
    road_object_hebrew = Column(Text())
    object_distance = Column(Integer())
    object_distance_hebrew = Column(Text())
    didnt_cross = Column(Integer())
    didnt_cross_hebrew = Column(Text())
    cross_mode = Column(Integer())
    cross_mode_hebrew = Column(Text())
    cross_location = Column(Integer())
    cross_location_hebrew = Column(Text())
    cross_direction = Column(Integer())
    cross_direction_hebrew = Column(Text())
    road1 = Column(Integer(), index=True)
    road2 = Column(Integer(), index=True)
    km = Column(Float())
    km_raw = Column(Text())
    km_accurate = Column(Boolean())
    road_segment_id = Column(Integer(), index=True)
    road_segment_number = Column(Integer(), index=True)
    road_segment_name = Column(Text(), index=True)
    road_segment_from_km = Column(Float())
    road_segment_to_km = Column(Float())
    road_segment_length_km = Column(Float())
    accident_yishuv_symbol = Column(Integer())
    accident_yishuv_name = Column(Text(), index=True)
    geo_area = Column(Integer())
    geo_area_hebrew = Column(Text())
    day_night = Column(Integer())
    day_night_hebrew = Column(Text())
    day_in_week = Column(Integer())
    day_in_week_hebrew = Column(Text())
    traffic_light = Column(Integer())
    traffic_light_hebrew = Column(Text())
    accident_region = Column(Integer())
    accident_region_hebrew = Column(Text())
    accident_district = Column(Integer())
    accident_district_hebrew = Column(Text())
    accident_natural_area = Column(Integer())
    accident_natural_area_hebrew = Column(Text())
    accident_municipal_status = Column(Integer())
    accident_municipal_status_hebrew = Column(Text())
    accident_yishuv_shape = Column(Integer())
    accident_yishuv_shape_hebrew = Column(Text())
    street1 = Column(Integer())
    street1_hebrew = Column(Text(), index=True)
    street2 = Column(Integer())
    street2_hebrew = Column(Text(), index=True)
    non_urban_intersection = Column(Integer())
    non_urban_intersection_hebrew = Column(Text())
    non_urban_intersection_by_junction_number = Column(Text())
    accident_month = Column(Integer())
    accident_day = Column(Integer())
    accident_hour_raw = Column(Integer())
    accident_hour_raw_hebrew = Column(Text())
    accident_hour = Column(Integer())
    accident_minute = Column(Integer())
    accident_year = Column(Integer(), primary_key=True, index=True)
    accident_month = Column(Integer())
    geom = Column(Geometry("POINT"), index=True)
    latitude = Column(Float())
    longitude = Column(Float())
    x = Column(Float())
    y = Column(Float())
    id = Column(BigInteger(), primary_key=True)
    accident_id = Column(BigInteger(), primary_key=True)
    provider_and_id = Column(BigInteger())
    provider_code = Column(Integer(), primary_key=True)
    file_type_police = Column(Integer())
    engine_volume = Column(Integer())
    engine_volume_hebrew = Column(Text())
    manufacturing_year = Column(Integer())
    driving_directions = Column(Integer())
    driving_directions_hebrew = Column(Text())
    vehicle_status = Column(Integer())
    vehicle_status_hebrew = Column(Text())
    vehicle_attribution = Column(Integer())
    vehicle_attribution_hebrew = Column(Text())
    seats = Column(Integer())
    total_weight = Column(Integer())
    total_weight_hebrew = Column(Text())
    vehicle_type = Column(Integer(), index=True)
    vehicle_type_hebrew = Column(Text(), index=True)
    vehicle_damage = Column(Integer())
    vehicle_damage_hebrew = Column(Text())
    car_id = Column(Integer())


class WazeAlert(Base):
    __tablename__ = "waze_alerts"

    id = Column(BigInteger(), primary_key=True)
    city = Column(Text())
    confidence = Column(Integer())
    created_at = Column(DateTime, index=True)
    ended_at_estimate = Column(DateTime, index=True, nullable=True)
    back_filled = Column(Boolean(), index=True, default=False)
    longitude = Column(Float())
    latitude = Column(Float())
    magvar = Column(Integer())
    number_thumbs_up = Column(Integer())
    report_rating = Column(Integer())
    reliability = Column(Integer())
    alert_type = Column(Text())
    alert_subtype = Column(Text())
    uuid = Column(Text(), unique=True, index=True)
    report_by_municipality_user = Column(Boolean(), default=False)
    street = Column(Text())
    road_type = Column(Integer())
    report_description = Column(Text())
    jam_uuid = Column(Text())
    geom = Column(Geometry("POINT"))


class WazeTrafficJams(Base):
    __tablename__ = "waze_traffic_jams"

    id = Column(BigInteger(), primary_key=True)
    level = Column(Integer())
    line = Column(Text())
    speed_kmh = Column(Integer())
    turn_type = Column(Integer())
    length = Column(Float())
    type = Column(Text())
    uuid = Column(Text(), unique=True, index=True)
    speed = Column(Integer())
    segments = Column(Text())
    road_type = Column(Integer())
    delay = Column(Integer())
    street = Column(Text())
    city = Column(Text())
    end_node = Column(Text())
    blocking_alert_uuid = Column(Text())
    start_node = Column(Text())
    created_at = Column(DateTime, index=True)
    ended_at_estimate = Column(DateTime, index=True, nullable=True)
    back_filled = Column(Boolean(), index=True, default=False)
    geom = Column(Geometry("LINESTRING"))


class EmbeddedReports(Base):
    __tablename__ = "embedded_reports"
    id = Column(Integer(), primary_key=True)
    report_name_english = Column(String(), primary_key=True)
    report_name_hebrew = Column(String())
    url = Column(String())


class InfographicsDataCacheFields(object):
    news_flash_id = Column(BigInteger(), primary_key=True)
    years_ago = Column(Integer(), primary_key=True)
    data = Column(sqlalchemy.types.JSON())


class InfographicsDataCache(InfographicsDataCacheFields, Base):
    __tablename__ = "infographics_data_cache"
    __table_args__ = (
        Index("infographics_data_cache_id_years_idx", "news_flash_id", "years_ago", unique=True),
    )

    def get_data(self):
        return self.data

    def serialize(self):
        return {"news_flash_id": self.news_flash_id, "years_ago": self.years_ago, "data": self.data}


class InfographicsDataCacheTemp(InfographicsDataCacheFields, Base):
    __tablename__ = "infographics_data_cache_temp"

    def serialize(self):
        return {"news_flash_id": self.news_flash_id, "years_ago": self.years_ago, "data": self.data}

    # Flask-Login integration
    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.news_flash_id


class CasualtiesCosts(Base):
    __tablename__ = "casualties_costs"
    id = Column(Integer(), primary_key=True)
    injured_type = Column(String())
    injured_type_hebrew = Column(String())
    injuries_cost_k = Column(Integer())
    year = Column(Integer())
    data_source_hebrew = Column(String())

    def toStr(self):
        return f"{self.id}:{self.injured_type}:{self.injuries_cost_k}"


class SchoolWithDescription2020(Base):
    __tablename__ = "schools_with_description2020"
    id = Column(BigInteger(), autoincrement=True, primary_key=True, index=True)
    school_id = Column(Integer(), nullable=True, index=True)
    school_name = Column(Text(), nullable=True)
    municipality_name = Column(Text(), nullable=True, index=True)
    yishuv_name = Column(Text(), nullable=True, index=True)
    institution_type = Column(Text(), nullable=True)
    lowest_grade = Column(Text(), nullable=True)
    highest_grade = Column(Text(), nullable=True)
    location_accuracy = Column(Text(), nullable=True)
    geom = Column(Geometry("POINT", srid=4326), index=True)
    x = Column(Float(), nullable=True)
    y = Column(Float(), nullable=True)
    longitude = Column(Float(), nullable=True)
    latitude = Column(Float(), nullable=True)
