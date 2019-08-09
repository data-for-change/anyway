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
import numpy as np
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
index_columns = ['road', 'section', 'lane', 'year', 'month', 'day', 'day_of_week', 'hour']

def get_value_or_none(param):
    if math.isnan(param):
        return None
    else:
        return int(param)

def delete_traffic_volume_of_year(year):
    q = db.session.query(TrafficVolume).filter_by(year=year)
    if q.all():
        logging.info("Deleting traffic volume of year: " + str(int(year)))
        q.delete(synchronize_session='fetch')
        db.session.commit()

def delete_traffic_volume_of_directory(path):
    traffic_volume_rows = []
    all_rows = []
    df_traffic_volume = pd.DataFrame()
    # Deleting all the records for each year that appears in the relevant file
    for file in os.listdir(path):
        file_path = os.path.join(path, file)
        if file_path.lower().endswith("tabmef.csv"):
            df = pd.read_csv(file_path)
            years = df.loc[:,"shana"].unique()
            for year in years:
                delete_traffic_volume_of_year(int(year))

def get_traffic_volume_rows(path):
    logging.info("\tReading traffic volume data from '%s'..." % path)
    all_rows = []

    for file in os.listdir(path):
        file_path = os.path.join(path, file)
        if file_path.lower().endswith("tabmef.csv"):
            df = pd.read_csv(file_path)
            df.rename(columns = dictionary,
                      inplace = True)

            # count duplicates in data
            count_df = (df.groupby(index_columns)
                          .size()
                          .to_frame())
            count_df = count_df.rename(columns={0: 'duplicate_count'})

            # remove duplicates from data, set index columns
            df.drop_duplicates(index_columns,
                                              inplace=True)
            df.set_index(index_columns,
                                        inplace=True)
            joint_df = (pd.merge(df,
                                count_df,
                                how='left',
                                right_index=True,
                                left_index=True)
                          .reset_index())
            traffic_volume_rows_float = joint_df.to_dict(orient='records')

            # modify all values to int - can't be done in dataframe due to presense of Nans in data
            for float_row in traffic_volume_rows_float:
                int_row = {k: get_value_or_none(v) for k, v in float_row.items()}
                all_rows.append(int_row)
    return all_rows


def import_to_datastore(path, batch_size):
    try:
        assert batch_size > 0
        dir_list = glob.glob("{0}/*".format(path))
        for directory in sorted(dir_list, reverse=False):
            started = datetime.now()
            delete_traffic_volume_of_directory(directory)
            traffic_volume_rows = get_traffic_volume_rows(directory)
            new_items = 0
            logging.info('inserting ' + str(len(traffic_volume_rows)) + ' new traffic data rows')
            for traffic_volume_chunk in chunks(traffic_volume_rows, batch_size):
                db.session.bulk_insert_mappings(TrafficVolume, traffic_volume_chunk)
                db.session.commit()
            new_items += len(traffic_volume_rows)
            logging.info("\t{0} items in {1}".format(new_items, time_delta(started)))
        db.session.commit()
        return new_items
    except:
        error = "Traffic Volume import succeeded partially with " + str(new_items) + " traffic data rows"
        raise Exception(error)


def main(path):
    started = datetime.now()
    total = import_to_datastore(path, 100)
    logging.info("Total: {0} traffic data rows in {1}".format(total, time_delta(started)))
