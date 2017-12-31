# -*- coding: utf-8 -*-
import json
from ..constants import CONST
from ..models import AccidentMarker
from ..utilities import init_flask
from .utils import batch_iterator
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from openpyxl import load_workbook


def _iter_rows(filename):
    workbook = load_workbook(filename, read_only=True)
    sheet = workbook[u"גיליון1"]
    rows = sheet.rows
    first_row = next(rows)
    assert [cell.value for cell in first_row] == [u'מזהה', u'סוג עבירה', u'סוג רכב', u'נ"צ', u'קישור']
    for row in rows:
        id_ = int(row[0].value)
        violation = row[1].value
        vehicle_type = row[2].value
        coordinates = row[3].value
        video_link = row[4].value
        if not violation:
            continue

        vehicle_type = vehicle_type or ''
        coordinates = coordinates.split(',')
        latitude, longitude = float(coordinates[0]), float(coordinates[1])
        description = {'VIOLATION_TYPE': violation, 'VEHICLE_TYPE': vehicle_type}

        yield {'id': id_,
               'latitude': latitude,
               'longitude': longitude,
               'created': datetime(2017, 12, 30),
               'provider_code': CONST.RSA_PROVIDER_CODE,
               'severity': 0,
               'title': 'שומרי הדרך',
               'description': json.dumps(description),
               'locationAccuracy': 1,
               'type': CONST.MARKER_TYPE_ACCIDENT,
               'video_link': video_link}


def parse(filename):
    app = init_flask()
    db = SQLAlchemy(app)

    for batch in batch_iterator(_iter_rows(filename), batch_size=50):
        db.session.bulk_insert_mappings(AccidentMarker, batch)
        db.session.commit()
