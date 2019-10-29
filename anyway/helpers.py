import csv
import datetime
import os
import time

import pandas as pd
import six
from flask import jsonify, abort, request
from six import StringIO, iteritems
from six.moves import http_client
from sqlalchemy import and_
import logging

from anyway.base import db
from anyway.constants import CONST
from .models import (EngineVolume, PopulationType, Region, District, NaturalArea, MunicipalStatus, YishuvShape,
                     TotalWeight, DrivingDirections, AgeGroup)


def generate_json(accidents, rsa_markers, discussions, is_thin, total_records=None):
    markers = accidents.all()
    markers += rsa_markers.all()

    if not is_thin:
        markers += discussions.all()

    if total_records is None:
        total_records = len(markers)

    total_accidents = accidents.count()
    total_rsa = rsa_markers.count()

    entries = [marker.serialize(is_thin) for marker in markers]
    return jsonify({"markers": entries, 'pagination': {'totalRecords': total_records,
                                                       'totalAccidents': total_accidents,
                                                       'totalRSA': total_rsa}})


def generate_csv(results):
    output_file = StringIO()
    yield output_file.getvalue()
    output_file.truncate(0)
    output = None
    for marker in results.all():
        serialized = marker.serialize()
        if not output:
            output = csv.DictWriter(output_file, serialized.keys())
            output.writeheader()

        row = {k: v.encode('utf8')
        if type(v) is six.text_type else v
               for k, v in iteritems(serialized)}
        output.writerow(row)
        yield output_file.getvalue()
        output_file.truncate(0)


ARG_TYPES = {'ne_lat': (float, 32.072427482938345), 'ne_lng': (float, 34.79928962966915),
             'sw_lat': (float, 34.79928962966915), 'sw_lng': (float, 34.78877537033077), 'zoom': (int, 17),
             'show_fatal': (bool, True), 'show_severe': (bool, True), 'show_light': (bool, True),
             'approx': (bool, True), 'accurate': (bool, True), 'show_markers': (bool, True),
             'show_accidents': (bool, True), 'show_rsa': (bool, True), 'show_discussions': (bool, True),
             'show_urban': (int, 3), 'show_intersection': (int, 3), 'show_lane': (int, 3), 'show_day': (int, 0),
             'show_holiday': (int, 0), 'show_time': (int, 24), 'start_time': (int, 25), 'end_time': (int, 25),
             'weather': (int, 0), 'road': (int, 0), 'separation': (int, 0), 'surface': (int, 0), 'acctype': (int, 0),
             'controlmeasure': (int, 0), 'district': (int, 0), 'case_type': (int, 0), 'fetch_markers': (bool, True),
             'fetch_vehicles': (bool, True), 'fetch_involved': (bool, True),
             'age_groups': (str, str(CONST.ALL_AGE_GROUPS_LIST).strip('[]').replace(' ', '')),
             'page': (int, 0), 'per_page': (int, 0)}


def get_kwargs():
    kwargs = {arg: arg_type(request.values.get(arg, default_value)) for (arg, (arg_type, default_value)) in
              iteritems(ARG_TYPES)}
    if request.values.get('age_groups[]') == '1234' or request.values.get('age_groups') == '1234':
        kwargs['age_groups'] = '1,2,3,4'
    try:
        kwargs.update(
            {arg: datetime.date.fromtimestamp(int(request.values[arg])) for arg in ('start_date', 'end_date')})
    except ValueError:
        abort(http_client.BAD_REQUEST)
    return kwargs


def vehicles_data_refinement(vehicle):
    provider_code = vehicle["provider_code"]
    accident_year = vehicle["accident_year"]
    new_vehicle = get_vehicle_dict(provider_code, accident_year)

    vehicle["engine_volume"] = new_vehicle["engine_volume"]
    vehicle["total_weight"] = new_vehicle["total_weight"]
    vehicle["driving_directions"] = new_vehicle["driving_directions"]

    return vehicle


def involved_data_refinement(involved: object) -> object:
    provider_code = involved["provider_code"]
    accident_year = involved["accident_year"]
    new_involved = get_involved_dict(provider_code, accident_year)

    involved["age_group"] = new_involved["age_group"]
    involved["population_type"] = new_involved["population_type"]
    involved["home_region"] = new_involved["home_region"]
    involved["home_district"] = new_involved["home_district"]
    involved["home_natural_area"] = new_involved["home_natural_area"]
    involved["home_municipal_status"] = new_involved["home_municipal_status"]
    involved["home_yishuv_shape"] = new_involved["home_yishuv_shape"]

    return involved


def get_involved_dict(provider_code, accident_year):
    involved = {}
    age_group = db.session.query(AgeGroup).filter(and_(AgeGroup.provider_code == provider_code,
                                                       AgeGroup.year == accident_year)).first()
    involved["age_group"] = age_group.age_group_hebrew if age_group else None

    population_type = db.session.query(PopulationType).filter(and_(PopulationType.provider_code == provider_code,
                                                                   PopulationType.year == accident_year)).first()

    involved["population_type"] = population_type.population_type_hebrew if population_type else None

    home_region = db.session.query(Region).filter(and_(Region.provider_code == provider_code,
                                                       Region.year == accident_year)).first()
    involved["home_region"] = home_region.region_hebrew if home_region else None

    home_district = db.session.query(District).filter(and_(District.provider_code == provider_code,
                                                           District.year == accident_year)).first()
    involved["home_district"] = home_district.district_hebrew if home_district else None

    home_natural_area = db.session.query(NaturalArea).filter(and_(NaturalArea.provider_code == provider_code,
                                                                  NaturalArea.year == accident_year)).first()
    involved["home_natural_area"] = home_natural_area.natural_area_hebrew if home_natural_area else None

    home_municipal_status = db.session.query(MunicipalStatus).filter(
        and_(MunicipalStatus.provider_code == provider_code,
             MunicipalStatus.year == accident_year)).first()
    involved[
        "home_municipal_status"] = home_municipal_status.municipal_status_hebrew if home_municipal_status else None

    home_yishuv_shape = db.session.query(YishuvShape).filter(and_(YishuvShape.provider_code == provider_code,
                                                                  YishuvShape.year == accident_year)).first()
    involved["home_yishuv_shape"] = home_yishuv_shape.yishuv_shape_hebrew if home_yishuv_shape else None

    return involved


def get_vehicle_dict(provider_code, accident_year):
    vehicle = {}
    engine_volume = db.session.query(EngineVolume) \
        .filter(and_(EngineVolume.provider_code == provider_code, EngineVolume.year == accident_year)) \
        .first()
    vehicle["engine_volume"] = engine_volume.engine_volume_hebrew if engine_volume else None

    total_weight = db.session.query(TotalWeight) \
        .filter(and_(TotalWeight.provider_code == provider_code, TotalWeight.year == accident_year)) \
        .first()
    vehicle["total_weight"] = total_weight.total_weight_hebrew if engine_volume else None

    driving_directions = db.session.query(DrivingDirections) \
        .filter(and_(DrivingDirections.provider_code == provider_code, DrivingDirections.year == accident_year)) \
        .first()
    vehicle["driving_directions"] = driving_directions.driving_directions_hebrew if engine_volume else None

    return vehicle


# Post handler for a generic REST API
def post_handler(obj):
    try:
        db.session.add(obj)
        db.session.commit()
        return jsonify(obj.serialize())
    except Exception as e:
        logging.debug("could not handle a post for object:{0}, error:{1}".format(obj, e))
        return ""


# Safely parsing an object
# cls: the ORM Model class that implement a parse method
def parse_data(cls, data):
    try:
        return cls.parse(data) if data is not None else None
    except Exception as e:
        logging.debug("Could not parse the requested data, for class:{0}, data:{1}. Error:{2}".format(cls, data, e))
        return


def get_json_object(request):
    try:
        return request.get_json(force=True)
    except Exception as e:
        logging.debug("Could not get json from a request. request:{0}. Error:{1}".format(request, e))
        return


def log_bad_request(request):
    try:
        logging.debug(
            "Bad {0} Request over {1}. Values: {2} {3}".format(request.method, request.url, request.form, request.args))
    except AttributeError:
        logging.debug("Bad request:{0}".format(str(request)))


def string2timestamp(s):
    return time.mktime(datetime.datetime.strptime(s, "%Y-%m-%d").timetuple())


def year2timestamp(y):
    return time.mktime(datetime.date(y, 1, 1).timetuple())


class PreferenceObject:
    def __init__(self, id, value, string):
        self.id = id
        self.value = value
        self.string = string


class HistoricalReportPeriods:
    def __init__(self, period_id, period_value, severity_string):
        self.period_id = period_id
        self.period_value = period_value
        self.severity_string = severity_string


DICTIONARY = "Dictionary"
cbs_dict_files = {DICTIONARY: "Dictionary.csv"}


def get_dict_file(directory):
    for name, filename in iteritems(cbs_dict_files):
        files = [path for path in os.listdir(directory)
                 if filename.lower() in path.lower()]
        amount = len(files)
        if amount == 0:
            raise ValueError("file not found: " + filename + " in directory " + directory)
        if amount > 1:
            raise ValueError("there are too many matches: " + filename)
        df = pd.read_csv(os.path.join(directory, files[0]), encoding="cp1255")
        yield name, df
