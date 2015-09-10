import csv
from datetime import datetime
from flask.ext.sqlalchemy import SQLAlchemy
from models import Marker
from utilities import init_flask
from process import time_delta

app = init_flask(__name__)
db = SQLAlchemy(app)

def parse_date(created):
    time = datetime.strptime(created, '%m/%d/%y %H:%M')
    year = int(time.strftime('20%y'))
    month = int(time.strftime('%m'))
    day = int(time.strftime('%d'))
    hour = int(time.strftime('%H'))
    minute = int(time.strftime('%M'))
    return datetime(year, month, day, hour, minute, 0)

def import_accidents():
    # print("\tReading accidents data from '%s'..." % os.path.basename(accidents))
    print("\tReading accidents data from united files")
    header = True
    with open("static/data/united/united_data.csv", 'rU') as f:
        reader = csv.reader(f, delimiter=',', dialect=csv.excel_tab)
        for accident in reader:
            if header:
                header = False
                continue

            """
            if "Latitude" not in accident or "Longtitude" not in accident:
                raise ValueError("Missing x and y coordinates")
            """
            marker = {
                "latitude": accident[1],
                "longitude": accident[2],
                "created": parse_date(accident[0]),
                # "provider_code": int(''.join(x for x in accident[0] if x.isdigit()))*2,
                "provider_code": 3,
                "id": int(''.join(x for x in accident[0] if x.isdigit())),
                "title": "Accident",
                "description": "",
                "address": accident[3] + ' ' + accident[5],
                "subtype": 15,
                "roadType": 5,
                "roadShape": 9,
                "dayType": 4,
                "unit": 0,
                "mainStreet": "",
                "secondaryStreet": "",
                "junction": "",
                "one_lane": 9,
                "multi_lane": -1,
                "speed_limit": -1,
                "intactness": -1,
                "road_width": -1,
                "road_sign": 5,
                "road_light": 1,
                "road_control": -1,
                "weather": 9,
                "road_surface": 9,
                "road_object": 9,
                "object_distance": 9,
                "didnt_cross": 9,
                "cross_mode": -1,
                "cross_location": -1,
                "cross_direction": 9,
                "severity": 4,
                "locationAccuracy": 1

            }

            yield marker


def import_to_datastore():
    """
    goes through all the files in a given directory, parses and commits them
    """
    try:
        started = datetime.now()

        accidents = list(import_accidents())
        db.session.execute(Marker.__table__.insert(), accidents)
        db.session.commit()

        print("\t{0} items in {1}".format(len(accidents), time_delta(started)))
        return len(accidents)
    except ValueError as e:
        print e.message
        return 0


def main():
    # TODO: implement only import of incremental data
    # TODO 2: Handle unique id's!!!
    import_to_datastore()
    # print parse_date("8/31/15 12:08")

if __name__ == "__main__":
    main()
