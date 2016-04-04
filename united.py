#!/usr/bin/env python
# -*- coding: utf-8 -*-
import calendar
import csv
from datetime import datetime, date
import os
import argparse

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_

from models import Marker, MARKER_TYPE_ACCIDENT
from utilities import init_flask
import importmail

import urllib2
from cookielib import CookieJar

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

def is_nth_weekday(nth, daynum, year, month):  # start counting the daynum from monday = 0
    return calendar.Calendar(nth).monthdatescalendar(
        year,
        month
    )[daynum][0]

def all_station_in_date_frame(created):

    collection =retrive_ims_xml()
    stationDataInDate = collection.getElementsByTagName('date_selected')
    accidentDate = parse_date(created)
    summerClock = is_nth_weekday(4, 4, accidentDate[0], 3)
    winterClock = is_nth_weekday(4,6,accidentDate[0],10)

    # weather is given in UTC time
    # therefore in summer clock we deduct 3 hours from the local time and in winter clock 2 hours
    #[
    #if accident happend between april and september
    if accidentDate.month < 10 & accidentDate.month > 3 :
        accidentDate.hour = accidentDate.hour - 3

    # if accident happend before the last sunday of october at 2:00 o'clock
    elif accidentDate[1] == 10 & (winterClock[2] > accidentDate[2]|( winterClock[2] == accidentDate[2] & accidentDate[3] < 2)):
                accidentDate[3] = accidentDate[3] - 3

    # if accident happend after the last friday of march at 2:00 o'clock
    elif  (accidentDate[1] == 3 & summerClock[2] < accidentDate[2] |( summerClock[2] == accidentDate[2] & accidentDate[3] >= 2)):
                accidentDate[3] = accidentDate[3]-3
    else: # winterClock
        accidentDate[3] = accidentDate[3] - 2
    #]



def retrive_ims_xml():

    cj = CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    file = opener.open("http://www.ims.gov.il/ims/PublicXML/observ.xml")
    data = file.read()
    file.close()
    xmldoc = minidom.parseString(data)
    collection = xmldoc.documentElement
    return collection


def find_station_by_coordinate(latitude, longitude):

    min_distance = 100000 #initialize big starting value so the distance will always be smaller than the initial
    station_lon = 0
    station_lat = 0
    collection =retrive_ims_xml()
    stationData = collection.getElementsByTagName('surface_station')
    i = -1

    for station in stationData:
        i = i+1 #save the place of the station in the file
        station_lon = station.getElementsByTagName('station_lon')
        for lon in station_lon:
            lon_difference = math.pow(float(lon.childNodes[0].nodeValue) - longitude, 2)
        station_lat = station.getElementsByTagName('station_lat')
        for lat in station_lat:
            lat_difference = math.pow(float(lat.childNodes[0].nodeValue) - latitude, 2)
        temp_dis = math.sqrt(lat_difference + lon_difference)
        if (temp_dis < min_distance):
            min_distance = temp_dis
            station_place_in_xml = i

    return station_place_in_xml


def convert_xml_values_toNumbers (rain):

    numConv = rain[:2] # variable to help convert from string to number

    for char in numConv:   # in the xml number are in a three digits format (4-004), we delete the 0es before the number
        if char == '0':
            rain.replace(char, '')
        else:
            break

    rain_in_millimeters = float(rain)

    if rain_in_millimeters >= 990:
        #numbers that are higher then 990 in the xml code equals 0.(the last digit) for example 991 = 0.1
        rain = rain_in_millimeters % 100
        rain = "0." + rain
        rain_in_millimeters = float(rain) #convert string to numbers

    return rain_in_millimeters


def convert_xml_numbers_to_hours (rain_duration):

    #convert the xml code for number of hours, to the actual number of hours

    if rain_duration == 1:
        rain_duration = 6
    elif rain_duration == 2:
        rain_duration = 12
    elif rain_duration == 3:
        rain_duration = 18
    elif rain_duration == 4 |rain_duration == "/":
        rain_duration = 24
    elif rain_duration == 5:
        rain_duration = 1
    elif rain_duration == 6:
        rain_duration = 2
    elif rain_duration == 7:
        rain_duration = 3
    elif rain_duration == 8:
        rain_duration = 9
    elif rain_duration == 9:
        rain_duration = 15
    return rain_duration

def convert_xml_numbers_to_current_weather(weather_code):

    if (weather_code is "00" ):
        weather = "בהיר"
    elif (weather_code is "01"):
        weather = "עננים מתפזרים"
    elif (weather_code is "03"):
        weather = "היערמות עננים"
    elif (weather_code is "04"):
        weather = "ראות לקויה כתוצאה מעשן"
    elif (weather_code is "05"):
        weather = "אובך"
    elif any( x in weather_code for x in ("07", "08")):
        weather = "אבק"
    elif (weather_code is "09"):
        weather = "סופת חול"
    elif (weather_code is "10"):
        weather = "ראות לקויה"
    elif (weather_code is "11"):
        weather = " ערפל קל"
    elif (weather_code is "12"):
        weather = "ברקים"
    elif (weather_code is "17"):
        weather = "סופת רעמים"
    elif (weather_code is "18"):
        weather = "סערה"
    elif (weather_code is "19"):
        weather = "סופה באופק"
    elif (weather_code is "20"):
        weather = "טפטוף"
    elif (weather_code is "21"):
        weather = "גשם"
    elif (weather_code is "22"):
        weather = "שלג"
    elif (weather_code is "23"):
        weather = "שלג מעורב בגשם"
    elif (weather_code is "24"):
        weather = "קרה (גשם קפוא)"
    elif (weather_code is "25"):
        weather = "גשם כבד"
    elif (weather_code is "26"):
        weather = "שלג כבד"
    elif (weather_code is "27"):
        weather = "ברד כבד"
    elif (weather_code is "28"):
        weather = "ערפל"
    elif (weather_code is "29"):
        weather = "סופת רעמים וגשם"
    elif any( x in weather_code for x in ("30", "31", "32")):
        weather = "סופת חול קלה"
    elif any( x in weather_code for x in ("33", "34", "35")):
        weather = "סופת חול"
    elif any( x in weather_code for x in ("36", "37", "38", "39")):
        weather = "סחף שלג"
    elif (weather_code is "40"):
        weather = "ערפל באופק"
    elif (weather_code is "41" ):
        weather = "כיסי ערפל"
    elif (weather_code is "42"):
        weather = "ערפל קל, מתפוגג"
    elif (weather_code is "43"):
        weather = "ערפל כבד מתפוגג"
    elif (weather_code is "44"):
        weather = "ערפל קל"
    elif any( x in weather_code for x in ("45", "46", "47")):
        weather = "ערפל כבד"
    elif (weather_code is "48" ):
        weather = "כפור, ערפל קל"
    elif (weather_code is "49"):
        weather = "כפור, ערפל כבד"
    elif (weather_code is "50"):
        weather = "טפטוף קל לסירוגין"
    elif (weather_code is "51"):
        weather = " טפטוף קל"
    elif (weather_code is "52"):
        weather = "טפטוף לסירוגין"
    elif (weather_code is "53"):
        weather = "טפטוף"
    elif (weather_code is "54"):
        weather = "גשם קל לסירוגין"
    elif (weather_code is "55"):
        weather = "גשם קל"
    elif (weather_code is "56"):
        weather = "טפטוף קל קופא במגע עם הקרקע"
    elif (weather_code is "57"):
        weather = "טפטוף קופא במגע עם הקרקע"
    elif (weather_code is "58"):
        weather = "טפטוף כבד"
    elif any( x in weather_code for x in ("59", "61")):
        weather = "גשם קל"
    elif (weather_code is "60"):
        weather = "גשם קל לסירוגין "
    elif (weather_code is "62"):
        weather = "גשם לסירוגין"
    elif (weather_code is "63"):
        weather = "גשם"
    elif (weather_code is "64"):
        weather = "גשם כבד לסירוגין"
    elif (weather_code is "65"):
        weather = "גשם כבד"
    elif (weather_code is "66"):
        weather = "גשם קל קופא במגע עם הקרקע"
    elif (weather_code is "67"):
        weather = "גשם קופא במגע עם הקרקע"
    elif (weather_code is "68"):
        weather = "שלג קל מעורב בגשם"
    elif (weather_code is "69"):
        weather = "שלג כבד מעורב בגשם"
    elif (weather_code is "70"):
        weather = "שלג קל לסירוגין"
    elif (weather_code is "71" ):
        weather = "שלג קל"
    elif (weather_code is "72"):
        weather = "שלג לסירוגין"
    elif (weather_code is "73"):
        weather = "שלג"
    elif (weather_code is "74"):
        weather = "שלג כבד לסירוגין"
    elif (weather_code is "75"):
        weather = "שלג כבד"
    elif (weather_code is "76"):
        weather = "שלג, שמיים בהירים"
    elif (weather_code is "77"):
        weather = " שלג דק"
    elif (weather_code is "78" ):
        weather = "שלג עבה"
    elif (weather_code is "79"):
        weather = "שלג מעורב בגשם, קרח שחור"
    elif (weather_code is "80"):
        weather = "ממטרים קלים"
    elif (weather_code is "81"):
        weather = " ממטרים"
    elif (weather_code is "82"):
        weather = "ממטרים כבדים"
    elif (weather_code is "83"):
        weather = "ממטרים קלים שלג מעורב בגשם"
    elif (weather_code is "84"):
        weather = "ממטרים שלג מעורב בגשם"
    elif (weather_code is "85"):
        weather = "ממטרי שלג קלים"
    elif (weather_code is "86"):
        weather = "ממטרי שלג"
    elif (weather_code is "87"):
        weather = "ממטרי שלג/ברד קלים"
    elif (weather_code is "88"):
        weather = "ממטרי ברד/שלג"
    elif (weather_code is "89" ):
        weather = "ממטרי ברד קלים"
    elif (weather_code is "90" ):
        weather = "ממטרי ברד"
    elif (weather_code is "91"):
        weather = "סופת רעמים, גשם קל"
    elif (weather_code is "92"):
        weather = "גשם, סופת רעמים"
    elif (weather_code is "93"):
        weather = "סופת רעמים, שלג קל/שלג קל מעורב בגשם"
    elif (weather_code is "94"):
        weather = "סופת רעמים, שלג/ שלג מעורב בגשם"
    elif (weather_code is "95"):
        weather = "סופת רעמים"
    elif (weather_code is "96"):
        weather = "סופת רעמים, ברד"
    elif (weather_code is "97"):
        weather = "סופת רעמים כבדה"
    elif (weather_code is "98"):
        weather = "סופת רעמים וחול כבדה"
    elif (weather_code is "99"):
        weather = "סופת רעמים כבדה, ברד"


def convert_xml_numbers_to_general_weather( past_weather_code1, past_weather_code2):

    if ("0" in x for x in (past_weather_code2, past_weather_code1)):
        pwc = "שמיים מעוננים חלקית, ראות לקויה "
    elif ("1" in x for x in (past_weather_code2, past_weather_code1)):
        pwc = "שמיים מעוננים לפרקים, ראות לקויה"
    elif ("2" in x for x in (past_weather_code2, past_weather_code1)):
        pwc = "שמיים מעוננים, ראות לקויה"
    elif ("3" in x for x in (past_weather_code2, past_weather_code1)):
        pwc = "סופת חול/אבק/אבק שלג, ראות לקויה מאד"
    elif ("4" in x for x in (past_weather_code2, past_weather_code1)):
        pwc = "ערפל כבד"
    elif ("5" in x for x in (past_weather_code2, past_weather_code1)):
        pwc = "טפטוף"
    elif ("6" in x for x in (past_weather_code2, past_weather_code1)):
        pwc = "גשם"
    elif ("7" in x for x in (past_weather_code2, past_weather_code1)):
        pwc = "שלג/שלג מעורב בגשם"
    elif ("8" in x for x in (past_weather_code2, past_weather_code1)):
        pwc = "ממטרים"
    elif ("9" in x for x in (past_weather_code2, past_weather_code1)):
        pwc = "סופת רעמים"





def processWeatherData(latitude, longitude):

    station = find_station_by_coordinate(latitude, longitude)
    collection =retrive_ims_xml()
    weatherData = collection.getElementsByTagName('surface_observation')

    wind_force = weatherData[station].getElementsByTagName('FF')
    for wf in wind_force:
        wind_force = wf.childNodes[0].nodeValue

    rain = weatherData[station].getElementsByTagName('RRR')
    for r in rain:
        rain = r.childNodes[0].nodeValue


    rain_duration = weatherData[station].getElementsByTagName('TR') # the duration of time in which  the rain amount was measured
    for rd in rain_duration:
        rain_duration = rd.childNodes[0].nodeValue

    weather_code = weatherData[station].getElementsByTagName('WW')
    for wc in weather_code:
        weather_code = wc.childNodes[0].nodeValue

    past_weather_code1 = weatherData[station].getElementsByTagName('W1')
    for pwc1 in past_weather_code1:
        past_weather_code1 = pwc1.childNodes[0].nodeValue

    past_weather_code2 = weatherData[station].getElementsByTagName('W2')
    for pwc2 in past_weather_code2:
        past_weather_code2 = pwc2.childNodes[0].nodeValue
    if (weather_code):
        weather = convert_xml_numbers_to_current_weather(weather_code)
        if not past_weather_code2 or not past_weather_code1:
            general_weather = convert_xml_numbers_to_general_weather(past_weather_code1, past_weather_code2)

        if (general_weather):
            if (general_weather not in weather):
                s = ", "
                l = (weather, general_weather)
                weather = s.join(l)

    else:
        if rain:
            rain_in_millimeters = convert_xml_values_toNumbers(rain)
        if rain_duration:
            rain_hours = convert_xml_numbers_to_hours (rain_duration)

        weather = "בהיר"  #defualt weather is clear sky
        road_surface = "יבש"


        if wind_force:

            if wind_force > 8 :
                weather = "סופת רוחות"
            elif wind_force > 5 :
                weather = "רוחות חזקות"


                #right now checking only for hour need to check if they enter duration of more than 1 hour
        if rain:
            if rain_duration:
                if rain_in_millimeters > 0 & rain_in_millimeters <= 0.5:  # rain amount is between 0.1 and 0.5 millimeter
                    weather = weather + "גשם קל ,"

                # average rain amount per hour is between 0.5 and 4.0 millimeters
                if ((rain_in_millimeters / rain_hours > 0.5 & rain_in_millimeters / rain_hours <= 4)):
                    weather = weather + "גשם ,"
                    road_surface = "כביש רטוב"

                     # average rain amount per hour is between 4.0 and 8.0 millimeters
                elif rain_in_millimeters / rain_hours > 4 & rain_in_millimeters / rain_hours <= 8:
                    weather = weather + "גשם שוטף ,"
                    road_surface = "כביש רטוב"


              # average rain amount per hour is more than 8.0 millimeters
                elif rain_in_millimeters / rain_hours > 8 :
                    weather = weather + "גשם זלעפות ,"
                    road_surface = "כביש רטוב"


    return {'weather': weather, 'road_surface': road_surface}


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

            weather_road = processWeatherData(accident[csvmap["lat"]], accident[csvmap["long"]])# function returns weather and road surface
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
                "weather":weather_road.get('weather'),
                "road_surface": weather_road.get('road_surface')
              
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

def update_db():
    """
    :param path: Local files directory ('united_path' on main() below)
    :return: length of DB entries after execution
    """
    app = init_flask(__name__)
    db = SQLAlchemy(app)
    united = Marker.query.filter(Marker.provider_code == 2)
    for accident in united:
        weather_road = processWeatherData(accident.latitude, accident.longitude)

        #weather_road.get('road_surface')
        #change later
        accident_history = Marker.query.filter_by(id=accident.id).first()
        weather = weather_road.get('weather')
        accident_history.weather = unicode(weather, "utf-8")
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

   # update_db()

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
