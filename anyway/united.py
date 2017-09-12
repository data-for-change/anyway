#!/usr/bin/env python
# -*- coding: utf-8 -*-
import calendar
import csv
from datetime import datetime
import os

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_

from .constants import CONST
from .models import Marker
from .utilities import init_flask
from .import importmail

from xml.dom import minidom

import math

import requests
import logging

############################################################################################
# United.py is responsible for the parsing and deployment of "united hatzala" data to the DB
############################################################################################

PROVIDER_CODE = CONST.UNITED_HATZALA_CODE
TIME_ZONE = 2
# convert IMS hours code to hours
RAIN_DURATION_CODE_TO_HOURS = {"1": 6, "2": 12, "3": 18, "4": 24, "/": 24, "5": 1, "6": 2, "7": 3, "8": 9, "9": 15}
WEATHER = {"0": 1, "1": 2, "3": 3, "4": 4, "5": 5, "7": 6, "8": 6, "9": 7, "10": 8, "11": 9,
           "12": 10, "17": 11, "18": 12, "19": 13, "20": 14, "21": 15, "22": 16, "23": 17, "24": 18,
           "25": 19, "26": 20, "27": 21, "28": 22, "29": 23, "30": 24, "31": 24, "32": 24, "33": 7,
           "34": 7, "35": 7, "36": 25, "37": 25, "38": 25, "39": 25, "40": 26, "41": 27, "42": 28,
           "43": 29, "44": 9, "45": 30, "46": 30, "47": 30, "48": 31, "49": 32, "50": 33, "51": 34,
           "52": 33, "53": 35, "54": 36, "55": 37, "56": 38, "57": 39, "58": 37, "59": 37, "61": 37, "60": 36,
           "62": 40, "63": 15, "64": 41, "65": 19, "66": 42, "67": 43, "68": 44, "69": 45, "70": 46, "71": 47,
           "72": 48, "73": 16, "74": 50, "75": 51, "76": 52, "77": 53, "78": 54, "79": 55, "80": 56, "81": 57,
           "82": 58, "83": 59, "84": 60, "85": 61, "86": 62, "87": 63, "88": 64, "89": 65, "90": 66, "91": 67,
           "92": 68, "93": 69, "94": 70, "95": 71, "96": 72, "97": 73, "98": 74, "99": 75}



def retrieve_ims_xml():  # getting an xml document from the ims(israel meteorological service) website
    logging.basicConfig(level=logging.DEBUG)
    s = requests.session()
    r = s.get('http://www.ims.gov.il/ims/PublicXML/observ.xml')
    xml_doc = minidom.parseString(r.text)
    collection = xml_doc.documentElement
    return collection


def parse_date(created):
    """
    :param created: Date & Time string from csv
    :return: Python datetime object
    """
    global time
    global hour
    DATE_FORMATS = ['%m/%d/%Y %I:%M:%S', '%Y-%m-%d %H:%M:%S', '%Y/%m/%d %I:%M:%S', '%d/%m/%Y %I:%M', '%Y/%m/%d %I:%M', '%m/%d/%Y %I:%M']

    for date_format in DATE_FORMATS:
        try:
            if date_format == '%Y-%m-%d %H:%M:%S':
                time = datetime.strptime(str(created)[:-4], date_format)
                hour = time.strftime('%H')
                hour = int(hour)
            else:
                time = datetime.strptime(str(created)[:-3], date_format)
                hour = time.strftime('%H')
                hour = int(hour) if str(created).endswith('AM') else int(hour) + 12
            break
        except ValueError:
            pass
    return datetime(time.year, time.month, time.day, hour, time.minute, 0)


def is_nth_weekday(nth, daynum, year,
                   month):  # find if date is the nth occurrence of the daynum day of the week (ex: the forth sunday of april 2016)
    # start counting the daynum from monday = 0
    return calendar.Calendar(nth).monthdatescalendar(
        year,
        month
    )[nth][daynum]


def get_parent_object_node(node):
    while node.parentNode:
        node = node.parentNode
        if node.nodeName == "Object":
            return node


def accident_time_zone_adjustment(created):  # return accident time in UTC time

    accident_date = parse_date(created)
    daylight_saving_time = is_nth_weekday(4, 4, accident_date.year, 3)
    winter_clock = is_nth_weekday(4, 6, accident_date.year, 10)

    # weather is given in UTC time
    # therefore in daylight_saving_time we deduct 3 hours from the local time and in winter clock 2 hours
    # [

    accident_date = accident_date.replace(hour=accident_date.hour - TIME_ZONE)

    # if accident happend between april and september
    if accident_date.month < 10 & accident_date.month > 3:
        accident_date.replace(hour=accident_date.hour - 1)

    # if accident happend before the last sunday of october at 2:00 o'clock
    elif accident_date.month == 10 & (
                winter_clock.day > accident_date.day | (
                            winter_clock.day == accident_date.day & accident_date.hour < 2)):
        accident_date.replace(hour=accident_date.hour - 1)

    # if accident happend after the last friday of march at 2:00 o'clock
    elif (accident_date.month == 3 & daylight_saving_time.day < accident_date.day | (
                    daylight_saving_time.day == accident_date.day & accident_date.hour >= 2)):
        accident_date.replace(hour=accident_date.hour - 1)
    # ]
    adate = ''.join(
        (str(accident_date.year), str(accident_date.month), str(accident_date.day), str(accident_date.hour)))
    return adate


def all_station_in_date_frame(collection, created):  # return the stations data in the time of the accident

    doc = minidom.Document()
    base = doc.createElement('accident_date')
    doc.appendChild(base)

    station_data_in_date = collection.getElementsByTagName('date_selected')
    station_data_in_date.sort()

    accident_date = accident_time_zone_adjustment(created)

    for station in enumerate(station_data_in_date):
        if accident_date in str(station.childNodes[0].nodeValue):
            base.appendChild(get_parent_object_node(station))
    return base


def find_station_by_coordinate(collection, latitude, longitude):

    station_place_in_xml = -1
    min_distance = float("inf")  # initialize big starting value so the distance will always be smaller than the initial
    station_data = collection.getElementsByTagName('surface_station')

    for i, station in enumerate(station_data):
        station_lon = station.getElementsByTagName('station_lon')
        assert len(station_lon) == 1
        lon = float(station_lon[0].childNodes[0].nodeValue)
        lon_difference = (lon - float(longitude)) ** 2
        station_lat = station.getElementsByTagName('station_lat')
        assert len(station_lat) == 1
        lat = float(station_lat[0].childNodes[0].nodeValue)
        lat_difference = (lat - float(latitude)) ** 2
        temp_dis = math.sqrt(lat_difference + lon_difference)
        if temp_dis < min_distance:
            min_distance = temp_dis
            station_place_in_xml = i

    return station_place_in_xml


def convert_xml_values_to_numbers(rain):
    num_conv = rain[:2]  # variable to help convert from string to number

    for char in num_conv:  # in the xml number are in a three digits format (4-004), we delete the 0es before the number
        if char == '0':
            rain.replace(char, '')
        else:
            break

    rain_in_millimeters = float(rain)

    if rain_in_millimeters >= 990:
        # numbers that are higher then 990 in the xml code equals 0.(the last digit) for example 991 = 0.1
        rain_in_millimeters *= 0.01
    return rain_in_millimeters

def get_weather_element(station, weather_data, tag):
    element = weather_data[station].getElementsByTagName(tag)
    if element:
        weather_element = element[0].childNodes[0].nodeValue
    else:
        weather_element = None
    return weather_element


def process_weather_data(collection, latitude, longitude):
    weather = 1  # default weather is clear sky

    station = find_station_by_coordinate(collection, latitude, longitude)
    weather_data = collection.getElementsByTagName('surface_observation')

    wind_force = get_weather_element(station, weather_data, 'FF')

    rain = get_weather_element(station, weather_data, 'RRR')

    rain_duration = get_weather_element(station, weather_data,
                                        'TR')  # the duration of time in which  the rain amount was measured
    weather_code = get_weather_element(station, weather_data, 'WW')
    if weather_code is not None:
        return WEATHER[weather_code.strip()]

    if wind_force is not None:

        if int(wind_force) > 8:
            weather = 76  # סופת רוחות
        elif int(wind_force) > 5:
            weather = 77  # רוחות חזקות

    if rain is not None and rain_duration is not None:
        rain_in_millimeters = convert_xml_values_to_numbers(rain)
        rain_hours = RAIN_DURATION_CODE_TO_HOURS[str(rain_duration).strip()]
        # rain amount is between 0.1 and 0.5 millimeter
        if 0.0 < rain_in_millimeters <= 0.5 or (
                        0.0 < rain_in_millimeters / rain_hours <= 0.5):
            if weather == 76:
                weather = 80  # סופת רוחות, גשם קל
            elif weather == 77:
                weather = 84  # רוחות חזקות, גשם קל
            else:
                weather = 37  # גשם קל

        # average rain amount per hour is between 0.5 and 4.0 millimeters
        if 0.5 < rain_in_millimeters / rain_hours <= 4:
            if weather == 76:
                weather = 81  # גשם וסופת רוחות
            elif weather == 77:
                weather = 85  # גשם ורוחות חזקות
            else:
                weather = 15  # גשם

        # average rain amount per hour is between 4.0 and 8.0 millimeters
        elif 4 < rain_in_millimeters / rain_hours <= 8:
            if 76 == weather:
                weather = 82  # סופת רוחות, גשם שוטף
            if weather == 77:
                weather = 86  # רוחות חזקות, גשם שוטף
            else:
                weather = 78  # גשם שוטף

        # average rain amount per hour is more than 8.0 millimeters
        elif rain_in_millimeters / rain_hours > 8:
            if weather == 76:
                weather = 83  # סופת רוחות, גשם זלעפות
            if weather == 77:
                weather = 87  # רוחות חזקות, גשם זלעפות
            else:
                weather = 79  # גשם זלעפות
    return weather

CSVMAP = [
        {"id": 0, "time": 1, "lat": 2, "long": 3, "street": 4, "city": 6, "comment": 7, "type": 8, "casualties": 9},
        {"id": 0, "time": 1, "type": 2, "long": 3, "lat": 4,  "city": 5, "street": 6, "comment": 7, "casualties": 8},
        ]

def create_accidents(collection, file_location):
    """
    :param file_location: local location of .csv
    :return: Yields a marker object with every iteration
    """
    logging.info("\tReading accidents data from '%s'..." % file_location)

    with open(file_location, 'rU') as f:
        reader = csv.reader(f, delimiter=',', dialect=csv.excel_tab)

        for line, accident in enumerate(reader):
            if line == 0:  # header
                format_version = 0 if "MissionID" in accident[0] else 1
                continue
            if not accident:  # empty line
                continue
            if line == 1 and accident[0] == "":
                logging.warn("\t\tEmpty File!")
                continue
            csvmap = CSVMAP[format_version]
            if accident[csvmap["lat"]] == "" or accident[csvmap["long"]] == "" or \
                            accident[csvmap["lat"]] is None or accident[csvmap["long"]] is None or \
                            accident[csvmap["lat"]] == "NULL" or accident[csvmap["long"]] == "NULL":
                logging.warn("\t\tMissing coordinates in line {0}. Moving on...".format(line + 1))
                continue

            created = parse_date(accident[csvmap["time"]])
            marker = {'id': accident[csvmap["id"]], 'latitude': accident[csvmap["lat"]],
                      'longitude': accident[csvmap["long"]], 'created': created, 'provider_code': PROVIDER_CODE,
                      'title': unicode(accident[csvmap["type"]], encoding='utf-8')[:100],
                      'address': unicode((accident[csvmap["street"]] + ' ' + accident[csvmap["city"]]),
                                         encoding='utf-8'),
                      'severity': 2 if u"קשה" in unicode(accident[csvmap["type"]], encoding='utf-8') else 3,
                      'locationAccuracy': 1, 'subtype': 21, 'type': CONST.MARKER_TYPE_ACCIDENT,
                      'description': unicode(accident[csvmap["comment"]], encoding='utf-8'),
                      'weather': process_weather_data(collection, accident[csvmap["lat"]],
                                                      accident[csvmap["long"]])}
            if format_version == 0:
                casualties = accident[csvmap["casualties"]]
                marker['intactness'] = casualties if casualties.isdigit() else 0

            yield marker


def import_to_db(collection, path):
    """
    :param path: Local files directory ('united_path' on main() below)
    :return: length of DB entries after execution
    """
    app = init_flask(__name__)
    db = SQLAlchemy(app)
    accidents = list(create_accidents(collection, path))
    if not accidents:
        return 0

    new_ids = [m["id"] for m in accidents
               if 0 == Marker.query.filter(and_(Marker.id == m["id"],
                                                Marker.provider_code == m["provider_code"])).count()]
    if not new_ids:
        logging.info("\t\tNothing loaded, all accidents already in DB")
        return 0

    db.session.execute(Marker.__table__.insert(), [m for m in accidents if m["id"] in new_ids])
    db.session.commit()
    return len(new_ids)


def update_db(collection):
    """
    :return: length of DB entries after execution
    """
    app = init_flask(__name__)
    db = SQLAlchemy(app)
    united = Marker.query.filter(Marker.provider_code == 2)
    for accident in united:
        if not accident.weather:
            accident.weather = process_weather_data(collection, accident.latitude, accident.longitude)
    db.session.commit()
    logging.info("\tFinished commiting the changes")


def main(light=True, username='', password='', lastmail=False):
    """
    Calls importmail.py prior to importing to DB
    """
    collection = retrieve_ims_xml()

    if not light:
        logging.info("Importing data from mail...")
        importmail.main(username, password, lastmail)
    united_path = "static/data/united/"
    total = 0
    logging.info("Loading United accidents...")
    for united_file in os.listdir(united_path):
        if united_file.endswith(".csv"):
            total += import_to_db(collection, united_path + united_file)
    logging.info("\tImported {0} items".format(total))

    update_db(collection)
