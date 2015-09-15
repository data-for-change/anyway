#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv
from datetime import datetime
from flask.ext.sqlalchemy import SQLAlchemy
from models import Marker
from utilities import init_flask
import os

############################################################################################
# United.py is responsible for the parsing and deployment of "united hatzala" data to the DB
############################################################################################

def parse_date(created):
    """
    :param created: Date & Time string from csv
    :return: Python datetime object
    """
    time = datetime.strptime(created[:-3], '%m/%d/%Y %I:%M:%S')
    year = int(time.strftime('20%y'))
    month = int(time.strftime('%m'))
    day = int(time.strftime('%d'))
    hour = int(time.strftime('%H')) if created[-2:] == 'AM' else int(time.strftime('%H'))+12
    minute = int(time.strftime('%M'))
    return datetime(year, month, day, hour, minute, 0)


def create_accidents(file_location):
    """
    :param file_location: local location of .csv
    :return: Yields a marker object with every iteration
    """
    print("\tReading accidents data from '%s'..." % file_location)
    header = True
    first_line = True
    inc = 1
    csvmap = {"time": 0, "lat": 1, "long": 2, "street": 3, "city": 5, "comment": 6, "type": 7, "casualties": 8}

    with open(file_location, 'rU') as f:
        reader = csv.reader(f, delimiter=',', dialect=csv.excel_tab)

        for accident in reader:
            if header:
                header = False
                continue
            if not accident:
                continue
            if first_line:
                first_line = False
                if accident[0] == "":
                    print "\t\tEmpty File!"
                    continue
            if accident[1] == "" or accident[2] == "":
                print "\t\tMissing coordinates! moving on.."
                continue

            marker = {
                "latitude": accident[csvmap["lat"]],
                "longitude": accident[csvmap["long"]],
                "created": parse_date(accident[csvmap["time"]]),
                "provider_code": 2,
                "id": int(''.join(x for x in accident[csvmap["time"]] if x.isdigit()) + str(inc)),
                "title": unicode(accident[csvmap["type"]], encoding='utf-8'),
                "address": unicode((accident[csvmap["street"]] + ' ' + accident[csvmap["city"]]), encoding='utf-8'),
                "severity": 2 if u"קשה" in unicode(accident[csvmap["type"]], encoding='utf-8') else 3,
                "locationAccuracy": 1,
                "subtype": 21,           # New subtype for United Hatzala
                "type": unicode(accident[csvmap["casualties"]], encoding='utf-8'),
                "description": unicode(accident[csvmap["comment"]], encoding='utf-8')
            }

            inc += 1
            yield marker


def import_to_db(path):
    """
    :param path: Local files directory ('united_path' on main() below)
    :return: length of DB entries after execution
    """
    app = init_flask(__name__)
    db = SQLAlchemy(app)
    try:
        accidents = list(create_accidents(path))
        db.session.execute(Marker.__table__.insert().prefix_with("OR IGNORE"), accidents)
        db.session.commit()
        return len(accidents)
    except ValueError as e:
        print e.message
        return 0


def main():
    united_path = "static/data/united/"
    total = 0
    for united_file in os.listdir(united_path):
        if united_file.endswith(".csv"):
            total += import_to_db(united_path + united_file)
    print("\tImported {0} items".format(total))

if __name__ == "__main__":
    main()
