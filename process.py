#!/usr/bin/env python
# -*- coding: utf-8 -*-
import csv
import datetime
import json
import sys
import os
import argparse
import subprocess
from tables_lms import *

from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from flask import Flask, request, make_response
from flask.ext.sqlalchemy import SQLAlchemy

class ItmToGpsConverter(object):
    def __init__(self):
        self.process = subprocess.Popen(['node', 'static/data/input.js'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)

    def convert(self, x, y):
        """
        Convert ITM to GPS coordinates

        :type x: float
        :type y: float
        :rtype: dict
        :return: {u'lat': 26.06199702841902, u'lng': 33.01173637265791, u'alt': 0, u'precision': 5}
        """

        self.process.stdin.write(json.dumps({'x': x, 'y': y}))
        return json.loads(self.process.stdout.readline())

app = Flask(__name__)
#app.config['SQLALCHEMY_ECHO'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('CLEARDB_DATABASE_URL')
db = SQLAlchemy(app)

def show_progress_spinner():
    d = show_progress_spinner.counter%4
    chars = ('|','/','-','\\')
    s = chars[d]
    sys.stderr.write("\r%s"%s)
    show_progress_spinner.counter +=1
show_progress_spinner.counter=0

data_path = "static/data/"
accidents_file = data_path + "2010_10_42_AccData.csv"
cities_file = data_path + "cities.csv"
streets_file = data_path + "2010_10_42_DicStreets.csv"
dictionary_file = data_path + "2010_10_42_Dictionary.csv"
urban_intersection_file = data_path + "2010_10_42_IntersectUrban.csv"
non_urban_intersection_file = data_path + "2010_10_42_IntersectNonUrban.csv"

cities = [x for x in csv.DictReader(open(cities_file))]
streets = [x for x in csv.DictReader(open(streets_file))]
dictionary_data = [x for x in csv.DictReader(open(dictionary_file))]
urban_intersection = [x for x in csv.DictReader(open(urban_intersection_file))]
non_urban_intersection = [x for x in csv.DictReader(open(non_urban_intersection_file))]

cities_dict = {x["SEMEL"] : x["NAME"] for x in cities}

def number(param, value, accident):
    return int(value) if value else None

def fixed_table(param, value, accident):
    return TABLES[param][int(value)] if value and int(value) in TABLES[param] else None

def dictionary(param, value, accident):
    for item in dictionary_data:
        if item["MS_TAVLA"] == param and item["KOD"] == value:
            return dictionary_data[2]

    return  None

def boolean(param, value, accident):
    return True if value == 1 else False

def cities_map(param, value, accident):
    return cities_dict[value] if value in cities_dict else ""

def streets_map(param, value, accident):
    for street in streets:
        if street["ishuv"] == accident["SEMEL_YISHUV"] and value == street["SEMEL_RECHOV"]:
            return street["SHEM_RECHOV"]

def urban_intersection_map(param, value, accident):
    return value

def non_urban_intersection_map(param, value, accident):
    return value

FIELD_FUNCTIONS = {
    "pk_teuna_fikt" : ("מזהה", number, None),
    "SUG_DEREH" : ("סוג דרך", fixed_table, "SUG_DEREH"),
    "SEMEL_YISHUV" : ("ישוב", cities_map, None), #from dictionary
    "REHOV1" : ("רחוב 1", streets_map, None), #from dicstreets (with SEMEL_YISHUV)
    "REHOV2" : ("רחוב 2", streets_map, None), #from dicstreets (with SEMEL_YISHUV)
    "BAYIT" : ("מספר בית", number, None),
    "ZOMET_IRONI" : ("צומת עירוני", urban_intersection_map, None),#from intersect urban dictionary
    "KVISH1" : ("כביש 1", urban_intersection_map, None), #from intersect urban dictionary
    "KVISH2" : ("כביש 2", urban_intersection_map, None),#from intersect urban dictionary
    "ZOMET_LO_IRONI" : ("צומת לא עירוני", non_urban_intersection_map, None),#from non urban dictionary
    "YEHIDA" : ("יחידה", fixed_table, "YEHIDA"),
    "SUG_YOM" : ("סוג יום", fixed_table, "SUG_YOM"),
    "RAMZOR" : ("רמזור", boolean, None),
    "HUMRAT_TEUNA" : ("חומרת תאונה", fixed_table, "HUMRAT_TEUNA"),
    "SUG_TEUNA" : ("סוג תאונה", fixed_table, "SUG_TEUNA"),
    "ZURAT_DEREH" : ("צורת דרך", fixed_table, "ZURAT_DEREH"),
    "HAD_MASLUL" : ("חד מסלול", fixed_table, "HAD_MASLUL"),
    "RAV_MASLUL" : ("רב מסלול", fixed_table, "RAV_MASLUL"),
    "MEHIRUT_MUTERET" : ("מהירות מותרת", fixed_table, "MEHIRUT_MUTERET"),
    "TKINUT" : ("תקינות", fixed_table, "TKINUT"),
    "ROHAV" : ("רוחב", fixed_table, "ROHAV"),
    "SIMUN_TIMRUR" : ("סימון תמרור", fixed_table, "SIMUN_TIMRUR"),
    "TEURA" :  ("תאורה", fixed_table, "TEURA"),
    "BAKARA" :  ("בקרה", fixed_table, "BAKARA"),
    "MEZEG_AVIR" :  ("מזג אוויר", fixed_table, "MEZEG_AVIR"),
    "PNE_KVISH" :  ("פני כביש", fixed_table, "PNE_KVISH"),
    "SUG_EZEM" :  ("סוג עצם", fixed_table, "SUG_EZEM"),
    "MERHAK_EZEM" :  ("מרחק עצם", fixed_table, "MERHAK_EZEM"),
    "LO_HAZA" :  ("לא חצה", fixed_table, "LO_HAZA"),
    "OFEN_HAZIYA" : ("אופן חציה", fixed_table, "OFEN_HAZIYA"),
    "MEKOM_HAZIYA" : ("מקום חציה", fixed_table, "MEKOM_HAZIYA"),
    "KIVUN_HAZIYA" : ("כיוון חציה", fixed_table, "KIVUN_HAZIYA"),
    "STATUS_IGUN" : ("עיגון", fixed_table, "STATUS_IGUN"),
    "MAHOZ" : ("מחוז", dictionary, 77),
    "NAFA" : ("נפה", dictionary, 79),
    "EZOR_TIVI" : ("אזור טבעי", dictionary, 80),
    "MAAMAD_MINIZIPALI" : ("מעמד מוניציפלי", dictionary, 78),
    "ZURAT_ISHUV" : ("צורת יישוב", dictionary, 81),
}

FIELD_LIST = FIELD_FUNCTIONS.keys()

def import_data():
    accidents_csv = csv.DictReader(open(accidents_file))
    accidents_gps_coordinates = json.loads(open(data_path+"gps.json").read())

    # oh dear.
    i = -1

    for accident in accidents_csv:
        i += 1
        output_line = {}
        output_fields = {}
        description_strings = []
        for field in FIELD_LIST:
            field_name, processor, parameter = FIELD_FUNCTIONS[field]
            output_line[field] = processor(parameter, accident[field], accident)
            if output_line[field]:
                if field in [
                        "SHNAT_TEUNA",
                        "HODESH_TEUNA",
                        "YOM_BE_HODESH",
                        "SHAA",
                        "REHOV1",
                        "REHOV2",
                        "BAYIT",
                        "SEMEL_YISHUV",
                        "X",
                        "Y"]:
                    continue
                description_strings.append("%s: %s" % (field_name, output_line[field]))

        if not accident["X"] or not accident["Y"]:
            continue

        accident_date = datetime.datetime(int(accident["SHNAT_TEUNA"]), int(accident["HODESH_TEUNA"]), int(accident["YOM_BE_HODESH"]), int(accident["SHAA"]) % 24, 0, 0)
        address = "%s%s, %s" % (output_line["REHOV1"], " %s" % output_line["BAYIT"] if output_line["BAYIT"] != 9999 else "", output_line["SEMEL_YISHUV"])

        description = "\n".join(description_strings)

        output_fields["date"] = accident_date    
        output_fields["description"] = description
        output_fields["id"] = accident["pk_teuna_fikt"]
        output_fields["severity"] = int(accident["HUMRAT_TEUNA"])
        output_fields["subType"] = int(accident["SUG_TEUNA"])
        output_fields["address"] = address

        output_fields["lat"] = accidents_gps_coordinates[i]["lat"]
        output_fields["lng"] = accidents_gps_coordinates[i]["lng"]
        yield output_fields


def import_to_datastore(provider_code, ratio=1):
    print "importing with ratio = %s"%(ratio,)
    from models import User, Marker

    i = 0
    # wipe all the Markers first
    db.session.query(Marker).delete()
    db.session.commit()

    commit_every = 100

    for irow, data in enumerate(import_data()):
        show_progress_spinner()
        if irow % ratio == 0:
            marker = Marker(
                user = None,
                id = provider_code + data['id'],
                title = "Accident",
                description = data["description"].decode("utf8"),
                address = data["address"].decode("utf8"),
                latitude = data["lat"],
                longitude = data["lng"],
                type = Marker.MARKER_TYPE_ACCIDENT,
                subtype = data["subType"],
                severity = data["severity"],
                created = data["date"],
            )

            db.session.add(marker)
            i += 1

            if i % commit_every == 0:
                print "committing (%d items done)..." % (i,)
                db.session.commit()
                print "done."

    if i % commit_every != 0: # we still have data in our transaction, flush it
        print "committing..."
        db.session.commit()
        print "done."

    print "imported %d items" % (i,)

def main(provider_code):
    parser = argparse.ArgumentParser()
    parser.add_argument('--ratio', type=int, metavar='n', default=1,
                        help='Import ratio 1:n')
    args = parser.parse_args()

    import_to_datastore(provider_code, args.ratio)

PROVIDER_CODE = '100' # CBS
if __name__ == "__main__":
    main(PROVIDER_CODE)
