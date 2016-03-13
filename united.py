#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv
from datetime import datetime
import os
import argparse

from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import and_

from models import Marker, MARKER_TYPE_ACCIDENT
from utilities import init_flask
import importmail

import urllib2
from xml.dom import minidom
import math


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
    hour = int(hour) if created.endswith('AM') else int(hour)+12
    return datetime(time.year, time.month, time.day, hour, time.minute, 0)


def retrive_ims_xml():

    file = urllib2.urlopen('wwww.ims.gov.il/ims/PublicXML/observ.xml')
    data = file.read()
    file.close()
    xmldoc = minidom.parse(data)
    collection = xmldoc.documentElement
    return collection


def find_station_by_coordinate(latitude, longitude):

    min_distance = 100000 #initialize big starting
    station_lon = 0
    station_lat = 0
    collection =retrive_ims_xml()
    stationData = collection.getElementsByTagName('surface_station')
    i = -1

    for station in stationData:
        i = i+1 #save the place of the station in the file
        station_lon = station.getElementsByTagName('station_lon')
        station_lat = station.getElementsByTagName('station_lat')
        lat_difference = math.pow(station_lat - latitude, 2)
        lon_difference = math.pow(station_lon - longitude, 2)
        temp_dis = math.sqrt(lat_difference + lon_difference)
        if (temp_dis < min_distance):
            min_distance = temp_dis
            station_place_in_xml = i

    return station_place_in_xml






def processWeatherData(latitude, longitude):

    station = find_station_by_coordinate(latitude, longitude)
    collection =retrive_ims_xml()
    weatherData = collection.getElementsByTagName('surface_observation')
    wind_force = weatherData[station].find('FF')
    rain = weatherData[station].find('RRR')
    rain_duration = weatherData[station].find('TR') # the duration of time in which  the rain amount was measured
    if wind_force is not None:
        if wind_force > 5 :
            weather = "חזקות רוחות"
        if wind_force > 8 :
            weather = "רוחות סופת"
    if rain is not None & rain_duration is not None:
        if rain > 990 & rain <= 995:  # rain amount is between 0.1 and 0.5 millimeter
            weather = weather + "קל גשם ,"

            # rain_duration is one hour and rain amount is between 0.5 and 4.0 millimeters
        if ((rain > 0 & rain <= 004) | rain > 995) & rain_duration == 5:
            weather = weather + "גשם ,"

             # rain_duration is one hour and rain amount is between 4.0 and 8.0 millimeters
        if rain > 004 & rain <= 008 & rain_duration == 5:
            weather = weather + "שוטף גשם ,"





def create_accidents(file_location):
    """
    :param file_location: local location of .csv
    :return: Yields a marker object with every iteration
    """
    print("\tReading accidents data from '%s'..." % file_location)
    csvmap = {"id": 0, "time": 1, "lat": 2, "long": 3, "street": 4, "city": 6, "comment": 7, "type": 8, "casualties": 9}

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
            marker = {
                "id": accident[csvmap["id"]],
                "latitude": accident[csvmap["lat"]],
                "longitude": accident[csvmap["long"]],
                "created": created,
                "provider_code": PROVIDER_CODE,
                "title": unicode(accident[csvmap["type"]], encoding='utf-8')[:100],
                "address": unicode((accident[csvmap["street"]] + ' ' + accident[csvmap["city"]]), encoding='utf-8'),
                "severity": 2 if u"קשה" in unicode(accident[csvmap["type"]], encoding='utf-8') else 3,
                "locationAccuracy": 1,
                "subtype": 21,           # New subtype for United Hatzala
                "type": MARKER_TYPE_ACCIDENT,
                "intactness": "".join(x for x in accident[csvmap["casualties"]] if x.isdigit()) or 0,
                "description": unicode(accident[csvmap["comment"]], encoding='utf-8'),
                "weather": processWeatherData(accident[csvmap["lat"]], accident[csvmap["long"]] )
              
            }

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
