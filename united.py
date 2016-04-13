#!/usr/bin/env python
# -*- coding: utf-8 -*-
import calendar
import csv
from datetime import datetime
import os
import argparse
from wsgiref import headers
from xml.etree import ElementTree

import re
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_

from models import Marker, MARKER_TYPE_ACCIDENT
from utilities import init_flask
import importmail

import urllib2
from cookielib import CookieJar

from xml.dom import minidom
from xml.dom.minidom import Document

import math

import requests
import logging


import Cookie

############################################################################################
# United.py is responsible for the parsing and deployment of "united hatzala" data to the DB
############################################################################################

PROVIDER_CODE = 2


def parse_date(created):
    """
    :param created: Date & Time string from csv
    :return: Python datetime object
    """
    time = datetime.strptime(created[:-3], '%m/%d/%Y %I:%M:%S')
    hour = time.strftime('%H')
    hour = int(hour) if created.endswith('AM') else int(hour) + 12
    return datetime(time.year, time.month, time.day, hour, time.minute, 0)


def is_nth_weekday(nth, daynum, year, month):  # start counting the daynum from monday = 0
    return calendar.Calendar(nth).monthdatescalendar(
        year,
        month
    )[daynum][0]


def get_parent_object_node(node):
    while node.parentNode:
        node = node.parentNode
        if node.nodeName == "Object":
            return node


def all_station_in_date_frame(created):
    collection = retrive_ims_xml()
    station_data_in_date = collection.getElementsByTagName('date_selected')
    station_data_in_date.sort(key=lambda x: int(x.attributes['Position'].value))
    accident_date = parse_date(created)
    summer_clock = is_nth_weekday(4, 4, accident_date[0], 3)
    winter_clock = is_nth_weekday(4, 6, accident_date[0], 10)

    # weather is given in UTC time
    # therefore in summer clock we deduct 3 hours from the local time and in winter clock 2 hours
    # [
    # if accident happend between april and september
    if accident_date.month < 10 & accident_date.month > 3:
        accident_date.hour -= 3

    # if accident happend before the last sunday of october at 2:00 o'clock
    elif accident_date[1] == 10 & (
                winter_clock[2] > accident_date[2] | (winter_clock[2] == accident_date[2] & accident_date[3] < 2)):
        accident_date[3] -= 3

    # if accident happend after the last friday of march at 2:00 o'clock
    elif (accident_date[1] == 3 & summer_clock[2] < accident_date[2] | (
                    summer_clock[2] == accident_date[2] & accident_date[3] >= 2)):
        accident_date[3] -= 3
    else:  # winter_clock
        accident_date[3] -= 2
    # ]
    adate = ''.join((accident_date.year, accident_date.month, accident_date.day, accident_date.hour))

    i = -1

    doc = Document()
    base = doc.createElement('accident_date')
    doc.appendChild(base)

    for station in station_data_in_date:
        i += 1
        if adate in str(station.childNodes[i].nodeValue):
            base.appendChild(get_parent_object_node(station))
    print doc.toprettyxml(indent="    ", encoding="utf-8")


def retrive_ims_xml():

    logging.basicConfig(level=logging.DEBUG)
    s = requests.session()
    r = s.get('http://www.ims.gov.il/ims/PublicXML/observ.xml')
    txt = r.text
    for e in ElementTree.fromstring(txt).findall('body/script'):
        m = re.search("document.cookie='[^']*'", e.text)
        cookie = m.group()
    print cookie
    C= Cookie.SimpleCookie()
    C.load(headers['cookie'])
    print C
    xml_doc = minidom.parseString(r.text)
    collection = xml_doc.documentElement
    return collection


def find_station_by_coordinate(collection, latitude, longitude):
    station_place_in_xml = -1
    lat_difference = 0
    lon_difference = 0
    min_distance = 100000  # initialize big starting value so the distance will always be smaller than the initial
    station_data = collection.getElementsByTagName('surface_station')
    i = -1

    for station in station_data:
        i += 1  # save the place of the station in the file
        station_lon = station.getElementsByTagName('station_lon')
        for lon in station_lon:
            lon_difference = math.pow(float(lon.childNodes[0].nodeValue) - float(longitude), 2)
        station_lat = station.getElementsByTagName('station_lat')
        for lat in station_lat:
            lat_difference = math.pow(float(lat.childNodes[0].nodeValue) - float(latitude), 2)
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
        # str_rain = "0." + rain
        # rain_in_millimeters = float(str_rain)  # convert string to numbers

    return rain_in_millimeters


def convert_xml_numbers_to_hours(rain_duration):
    # convert the xml code for number of hours, to the actual number of hours
    hours = {"1": 6, "2": 12, "3": 18, "4": 24, "/": 24, "5": 1, "6": 2, "7": 3, "8": 9, "9": 15}

    return hours[str(rain_duration)]


def convert_xml_numbers_to_current_weather(weather_code):
    str_weather = str(weather_code)
    str_weather = str_weather.strip(' ')
    weather = {"00": 1, "01": 2, "03": 3, "04": 4, "05": 5, "07": 6, "08": 6, "09": 7, "10": 8, "11": 9,
               "12": 10, "17": 11, "18": 12, "19": 13, "20": 14, "21": 15, "22": 16, "23": 17, "24": 18,
               "25": 19, "26": 20, "27": 21, "28": 22, "29": 23, "30": 24, "31": 24, "32": 24, "33": 7,
               "34": 7, "35": 7, "36": 25, "37": 25, "38": 25, "39": 25, "40": 26, "41": 27, "42": 28,
               "43": 29, "44": 9, "45": 30, "46": 30, "47": 30, "48": 31, "49": 32, "50": 33, "51": 34,
               "52": 33, "53": 35, "54": 36, "55": 37, "56": 38, "57": 39, "58": 37, "59": 37, "61": 37, "60": 36,
               "62": 40, "63": 15, "64": 41, "65": 19, "66": 42, "67": 43, "68": 44, "69": 45, "70": 46, "71": 47,
               "72": 48, "73": 16, "74": 50, "75": 51, "76": 52, "77": 53, "78": 54, "79": 55, "80": 56, "81": 57,
               "82": 58, "83": 59, "84": 60, "85": 61, "86": 62, "87": 63, "88": 64, "89": 65, "90": 66, "91": 67,
               "92": 68, "93": 69, "94": 70, "95": 71, "96": 72, "97": 73, "98": 74, "99": 75}

    return weather[str_weather]


def process_weather_data(collection, latitude, longitude):
    weather = 1  # default weather is clear sky
    rain_in_millimeters = 0
    rain_hours = 0

    station = find_station_by_coordinate(collection, latitude, longitude)
    weather_data = collection.getElementsByTagName('surface_observation')

    wind_force = weather_data[station].getElementsByTagName('FF')
    for wf in wind_force:
        wind_force = wf.childNodes[0].nodeValue

    rain = weather_data[station].getElementsByTagName('RRR')
    for r in rain:
        rain = r.childNodes[0].nodeValue

    rain_duration = weather_data[station].getElementsByTagName(
        'TR')  # the duration of time in which  the rain amount was measured
    for rd in rain_duration:
        rain_duration = rd.childNodes[0].nodeValue

    weather_code = weather_data[station].getElementsByTagName('WW')
    for wc in weather_code:
        weather_code = wc.childNodes[0].nodeValue

    if weather_code:
        weather = convert_xml_numbers_to_current_weather(weather_code)

    else:
        if rain:
            rain_in_millimeters = convert_xml_values_to_numbers(rain)
        if rain_duration:
            rain_hours = convert_xml_numbers_to_hours(rain_duration)

        if wind_force:

            if int(wind_force) > 8:
                weather = 76  # סופת רוחות
            elif int(wind_force) > 5:
                weather = 77  # רוחות חזקות

        if rain:
            if rain_duration:
                # rain amount is between 0.1 and 0.5 millimeter
                if rain_in_millimeters > 0 & rain_in_millimeters <= 0.5:
                    if weather == 76:
                        weather = 80  # סופת רוחות, גשם קל
                    elif weather == 77:
                        weather = 84  # רוחות חזקות, גשם קל
                    else:
                        weather = 37  # גשם קל

                # average rain amount per hour is between 0.5 and 4.0 millimeters
                if rain_in_millimeters / rain_hours > 0.5 & rain_in_millimeters / rain_hours <= 4:
                    if weather == 76:
                        weather = 81  # גשם וסופת רוחות
                    elif weather == 77:
                        weather = 85  # גשם ורוחות חזקות
                    else:
                        weather = 15  # גשם

                # average rain amount per hour is between 4.0 and 8.0 millimeters
                elif rain_in_millimeters / rain_hours > 4 & rain_in_millimeters / rain_hours <= 8:
                    if 76 == weather:
                        weather = 82  # סופת רוחות, גשם שוטך
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


def create_accidents(file_location):
    """
    :param file_location: local location of .csv
    :return: Yields a marker object with every iteration
    """
    print("\tReading accidents data from '%s'..." % file_location)
    csvmap = {"id": 0, "time": 1, "lat": 2, "long": 3, "street": 4, "city": 6, "comment": 7, "type": 8, "casualties": 9}

    collection = retrive_ims_xml()

    with open(file_location, 'rU') as f:
        reader = csv.reader(f, delimiter=',', dialect=csv.excel_tab)

        for line, accident in enumerate(reader):
            if line == 0 or not accident:  # header or empty line
                continue
            if line == 1 and accident[0] == "":
                print "\t\tEmpty File!"
                continue
            if accident[csvmap["lat"]] == "" or accident[csvmap["long"]] == "":
                print "\t\tMissing coordinates in line {0}. Moving on...".format(line + 1)
                continue

            created = parse_date(accident[csvmap["time"]])
            marker = dict(id=accident[csvmap["id"]], latitude=accident[csvmap["lat"]],
                          longitude=accident[csvmap["long"]], created=created, provider_code=PROVIDER_CODE,
                          title=unicode(accident[csvmap["type"]], encoding='utf-8')[:100],
                          address=unicode((accident[csvmap["street"]] + ' ' + accident[csvmap["city"]]),
                                          encoding='utf-8'),
                          severity=2 if u"קשה" in unicode(accident[csvmap["type"]], encoding='utf-8') else 3,
                          locationAccuracy=1, subtype=21, type=MARKER_TYPE_ACCIDENT,
                          intactness="".join(x for x in accident[csvmap["casualties"]] if x.isdigit()) or 0,
                          description=unicode(accident[csvmap["comment"]], encoding='utf-8'),
                          weather=process_weather_data(collection, accident[csvmap["lat"]], accident[csvmap["long"]]))

            yield marker


def import_to_db(path):
    """
    :param path: Local files directory ('united_path' on main() below)
    :return: length of DB entries after execution
    """
    app = init_flask(__name__)
    db = SQLAlchemy(app)
    accidents = list(create_accidents(path))
    if not accidents:
        return 0

    new_ids = [m["id"] for m in accidents
               if 0 == Marker.query.filter(and_(Marker.id == m["id"],
                                                Marker.provider_code == m["provider_code"])).count()]
    if not new_ids:
        print "\t\tNothing loaded, all accidents already in DB"
        return 0

    db.session.execute(Marker.__table__.insert(), [m for m in accidents if m["id"] in new_ids])
    db.session.commit()
    return len(new_ids)


def update_db():
    """
    :return: length of DB entries after execution
    """
    collection = retrive_ims_xml()

    app = init_flask(__name__)
    db = SQLAlchemy(app)
    united = Marker.query.filter(Marker.provider_code == 2)
    for accident in united:
        weather_road = process_weather_data(collection, accident.latitude, accident.longitude)
        accident.weather = weather_road
    db.session.commit()


def main():
    """
    Calls importmail.py prior to importing to DB
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--light', action='store_true', default=False,
                        help='Import without downloading any new files')
    parser.add_argument('--username', default='')
    parser.add_argument('--password', default='')
    parser.add_argument('--lastmail', action='store_true', default=False)
    args = parser.parse_args()

    update_db()

    if not args.light:
        importmail.main(args.username, args.password, args.lastmail)
    united_path = "static/data/united/"
    total = 0
    for united_file in os.listdir(united_path):
        if united_file.endswith(".csv"):
            total += import_to_db(united_path + united_file)
    print("\tImported {0} items".format(total))


if __name__ == "__main__":
    main()
