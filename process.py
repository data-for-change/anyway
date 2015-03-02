﻿#!/usr/bin/python
# -*- coding: utf-8 -*-
import csv
import datetime
import json
import sys
from tables_lms import *

from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from flask.ext.sqlalchemy import SQLAlchemy
from database import Base, db_session, engine
from retry import retries, example_exc_handler

def show_progress_spinner():
    d = show_progress_spinner.counter%4
    chars = ('|','/','-','\\')
    s = chars[d]
    sys.stderr.write("\r%s"%s)
    show_progress_spinner.counter +=1
show_progress_spinner.counter=0

data_path = "static/data/"
accidents_file = data_path + "H20101042AccData.csv"
cities_file = data_path + "cities.csv"
streets_file = data_path + "H20101042DicStreets.csv"
dictionary_file = data_path + "H20101042Dictionary.csv"
urban_intersection_file = data_path + "H20101042IntersectUrban.csv"
non_urban_intersection_file = data_path + "H20101042IntersectNonUrban.csv"

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
    "KIVUN_HAZIYA" : ("כיוון חציה", fixed_table, "MEKOM_HAZIYA"),
    "STATUS_IGUN" : ("עיגון", fixed_table, "STATUS_IGUN"),
    "MAHOZ" : ("מחוז", dictionary, 77),
    "NAFA" : ("נפה", dictionary, 79),
    "EZOR_TIVI" : ("אזור טבעי", dictionary, 80),
    "MAAMAD_MINIZIPALI" : ("מעמד מוניציפלי", dictionary, 78),
    "ZURAT_ISHUV" : ("צורת יישוב", dictionary, 81),
}

FIELD_LIST = [
    "SUG_DEREH", "SEMEL_YISHUV", "REHOV1", "REHOV2", "BAYIT", "ZOMET_IRONI", "KVISH1", "KVISH2",
    "ZOMET_LO_IRONI", "YEHIDA", "SUG_YOM", "RAMZOR",
    "HUMRAT_TEUNA", "SUG_TEUNA", "ZURAT_DEREH", "HAD_MASLUL", "RAV_MASLUL", "MEHIRUT_MUTERET", "TKINUT", "ROHAV",
    "SIMUN_TIMRUR", "TEURA","BAKARA", "MEZEG_AVIR", "PNE_KVISH", "SUG_EZEM", "MERHAK_EZEM", "LO_HAZA", "OFEN_HAZIYA",
    "MEKOM_HAZIYA", "KIVUN_HAZIYA", "MAHOZ", "NAFA", "EZOR_TIVI", "MAAMAD_MINIZIPALI", "ZURAT_ISHUV", 
]

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
                        "HUMRAT_TEUNA",
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
        output_fields["id"] = int(accident["pk_teuna_fikt"])
        output_fields["severity"] = int(accident["HUMRAT_TEUNA"])
        output_fields["address"] = address

        output_fields["lat"] = accidents_gps_coordinates[i]["lat"]
        output_fields["lng"] = accidents_gps_coordinates[i]["lng"]
        yield output_fields

@retries(3, delay=1800, hook=example_exc_handler)
def flush_and_commit(session):
    session.commit()
    session.flush()
    print "committed successfully"

def import_to_datastore():
    from models import User, Marker

    i = 0
    session = db_session()
    commit_every = 500
    for irow, data in enumerate(import_data()):
        show_progress_spinner()
        marker = Marker(
            user = None,
            title = "Accident",
            description = data["description"].decode("utf8"),
            address = data["address"].decode("utf8"),
            latitude = data["lat"],
            longitude = data["lng"],
            type = Marker.MARKER_TYPE_ACCIDENT,
            subtype = data["severity"],
            created = data["date"],
        )
        session.add(marker)
        if irow>0 and irow%commit_every == 0:
            flush_and_commit(session)

if __name__ == "__main__":
    import_to_datastore()
