import csv
from datetime import datetime
from flask.ext.sqlalchemy import SQLAlchemy
from models import Marker
from utilities import init_flask

app = init_flask(__name__)
db = SQLAlchemy(app)
location = "static/data/united/united_data.csv"

def parse_date(created):
    time = datetime.strptime(created, '%m/%d/%y %H:%M')
    year = int(time.strftime('20%y'))
    month = int(time.strftime('%m'))
    day = int(time.strftime('%d'))
    hour = int(time.strftime('%H'))
    minute = int(time.strftime('%M'))
    return datetime(year, month, day, hour, minute, 0)

def import_accidents():
    print("\tReading accidents data from '%s'..." % location)
    header = True
    inc = 1
    with open(location, 'rU') as f:
        reader = csv.reader(f, delimiter=',', dialect=csv.excel_tab)
        for accident in reader:
            if header:
                header = False
                continue

            marker = {
                "latitude": accident[1],
                "longitude": accident[2],
                "created": parse_date(accident[0]),
                "provider_code": 0,
                "id": int(''.join(x for x in accident[0] if x.isdigit()) + str(inc)),
                "title": "Accident",
                "address": accident[3] + ' ' + accident[5],
                "severity": 3,
                "locationAccuracy": 1,
                "subtype": 21           # New subtype for United Hatzala
            }

            inc += 1
            yield marker


def import_to_datastore():
    try:
        accidents = list(import_accidents())
        db.session.execute(Marker.__table__.insert().prefix_with("OR IGNORE"), accidents)
        db.session.commit()

        print("\tImported {0} items".format(len(accidents)))
        return len(accidents)
    except ValueError as e:
        print e.message
        return 0


def main():
    import_to_datastore()

if __name__ == "__main__":
    main()
