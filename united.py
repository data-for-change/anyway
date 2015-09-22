#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv
from datetime import datetime
from flask.ext.sqlalchemy import SQLAlchemy
from models import Marker
from utilities import init_flask
import os
import importmail
import argparse

############################################################################################
# United.py is responsible for the parsing and deployment of "united hatzala" data to the DB
############################################################################################

def parse_date(created):
    """
    :param created: Date & Time string from csv
    :return: Python datetime object
    """
    time = datetime.strptime(created[:-3], '%m/%d/%Y %I:%M:%S')
    hour = int(time.strftime('%H')) if created[-2:] == 'AM' else int(time.strftime('%H'))+12
    return datetime(time.year, time.month, time.day, hour, time.minute, 0)


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
            if accident[csvmap["lat"]] == "" or accident[csvmap["long"]] == "":
                print "\t\tMissing coordinates! moving on.."
                continue

            marker = {
                "latitude": accident[csvmap["lat"]],
                "longitude": accident[csvmap["long"]],
                "created": parse_date(accident[csvmap["time"]]),
                "provider_code": 2,
                "id": int(''.join(x for x in accident[csvmap["time"]][:-10] if x.isdigit()) + str(inc)),
                "title": unicode(accident[csvmap["type"]], encoding='utf-8'),
                "address": unicode((accident[csvmap["street"]] + ' ' + accident[csvmap["city"]]), encoding='utf-8'),
                "severity": 2 if u"קשה" in unicode(accident[csvmap["type"]], encoding='utf-8') else 3,
                "locationAccuracy": 1,
                "subtype": 21,           # New subtype for United Hatzala
                "description": unicode(accident[csvmap["comment"]], encoding='utf-8')
            }
            # "type": unicode(accident[csvmap["casualties"]], encoding='utf-8'),

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

        # TODO: fix this command to a posgesql compatible execution:
        db.session.merge(Marker.__table__.insert(), accidents)
    except:
        print 'Could not UPSERT, trying SQLite way...'
        accidents = list(create_accidents(path))
        db.session.execute(Marker.__table__.insert().prefix_with("OR IGNORE"), accidents)

    db.session.commit()
    return len(accidents)


def main():
    """
    Calls importmail.py prior to importing to DB
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--light', action='store_true', default=False,
                        help='Allow importing without downloading any new files')
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
