from datetime import datetime
from ..utilities import chunks
from flask_sqlalchemy import SQLAlchemy
from ..models import TrafficVolume
from ..utilities import init_flask, time_delta
from sqlalchemy.sql.expression import func
import glob
import os
import logging
import pandas as pd
import math

app = init_flask()
db = SQLAlchemy(app)

dictionary = {
    "shana": "year",
    "kvish": "road",
    "keta": "section",
    "maslul": "lane",
    "hodesh": "month",
    "taarich": "day",
    "yom": "day_of_week",
    "shaa": "hour",
    "nefah": "volume"
}


def translate_heb_to_eng(word):
    if word in dictionary:
        return dictionary.get(word)
    else:
        return word


def get_traffic_volume_rows(path):
    logging.info("\tReading traffic volume data from '%s'..." % path)
    traffic_volume_rows = []
    # Getting the last used ID.
    q = db.session.query(func.max(TrafficVolume.id))
    current_id = q.all()[0][0] or 0
    # Deleting all the records for each year that appears in the first line of one of the files being imported.
    # Therefore, if a file includes data for more than one specific year, the process may fail,
    # if that data already exists in the table.
    all_files = glob.glob(os.path.join(path, "*.csv"))
    for file in all_files:
        df = pd.read_csv(file)
        year = df.loc[0]["shana"]
        q = db.session.query(TrafficVolume).filter_by(year=year)
        if q.all():
            q.delete(synchronize_session='fetch')
            db.session.commit()

    for file in all_files:
        df = pd.read_csv(file)
        for _, csv_row in df.iterrows():
            traffic_volume_row = {}
            for key, value in csv_row.iteritems():
                traffic_volume_row[translate_heb_to_eng(key)] = get_value_or_none(value)
            current_id += 1
            traffic_volume_row["id"] = current_id
            traffic_volume_rows.append(traffic_volume_row)
    return traffic_volume_rows


def get_value_or_none(param):
    if math.isnan(param):
        return None
    else:
        return param


def import_to_datastore(path, batch_size):
    try:
        assert batch_size > 0
        started = datetime.now()
        traffic_volume_rows = get_traffic_volume_rows(path)
        new_items = 0
        logging.info('inserting ' + str(len(traffic_volume_rows)) + ' new traffic data rows')
        for traffic_volume_chunk in chunks(traffic_volume_rows, batch_size):
            db.session.bulk_insert_mappings(TrafficVolume, traffic_volume_chunk)
            db.session.commit()
        new_items += len(traffic_volume_rows)
        logging.info("\t{0} items in {1}".format(new_items, time_delta(started)))
        return new_items
    except:
        error = "Traffic Volume import succeeded partially with " + new_items + " traffic data rows"
        raise Exception(error)


def main(path):
    started = datetime.now()
    total = import_to_datastore(path, 100)
    logging.info("Total: {0} traffic data rows in {1}".format(total, time_delta(started)))
