# -*- coding: utf-8 -*-
import json
import math

from ..constants import CONST
from ..models import RoadSegments
from ..utilities import init_flask, ItmToWGS84
from .utils import batch_iterator
from flask_sqlalchemy import SQLAlchemy
from openpyxl import load_workbook

app = init_flask()
db = SQLAlchemy(app)

def _iter_rows(filename):
    workbook = load_workbook(filename, read_only=True)
    sheet = workbook[u"tv_ktaim (2)"]
    rows = sheet.rows
    first_row = next(rows)
    headers = [u'kvish', u'keta', u'km_me', u'shem_km_me', u'ad_km', u'shem_km_ad', u'x  מקום הצבה', u'y מקום הצבה', u'mezahe_keta']
    assert [cell.value for cell in first_row] == headers
    coordinates_converter = ItmToWGS84()
    for row in rows:
        road = row[0].value

        # In order to ignore empty lines
        if not road:
            continue

        segment = row[1].value
        from_km = row[2].value
        from_name = row[3].value
        to_km = row[4].value
        to_name = row[5].value
        x_coord = row[6].value
        y_coord = row[7].value
        segment_id = row[8].value

        if x_coord and not math.isnan(x_coord) and y_coord and not math.isnan(y_coord):
            longitude, latitude = coordinates_converter.convert(x_coord, y_coord)
        else:
            longitude, latitude = None, None # otherwise yield will produce: UnboundLocalError: local variable referenced before assignment

        yield {
            'road': road,
            'segment': segment,
            'from_km': from_km,
            'from_name': from_name,
            'to_km': to_km,
            'to_name': to_name,
            'x_coord': x_coord,
            'y_coord': y_coord,
            'segment_id' : segment_id,
            'longitude' : longitude,
            'latitude' : latitude
        }


def parse(filename):
    app = init_flask()
    db = SQLAlchemy(app)

    for batch in batch_iterator(_iter_rows(filename), batch_size=50):
        db.session.bulk_insert_mappings(RoadSegments, batch)
        db.session.commit()
