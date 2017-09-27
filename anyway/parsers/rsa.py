# -*- coding: utf-8 -*-
import json
from ..constants import CONST
from ..models import Marker
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
    assert [cell.value for cell in first_row] == [u'סוג עבירה', u'סוג רכב', u'נ"צ']
    for id_, row in enumerate(rows):
        offence = row[0].value
        vehicle_type = row[1].value
        coordinates = row[2].value
        if not offence:
            continue

        vehicle_type = vehicle_type or ''
        coordinates = coordinates.split(',')
        longitude, latitude = float(coordinates[0]), float(coordinates[1])
        description = {'OFFENCE_TYPE': offence, 'VEHICLE_TYPE': vehicle_type}

        yield {'id': id_, 'latitude': longitude,
               'created': datetime(2017, 1, 1),
               'longitude': latitude, 'provider_code': CONST.RSA_PROVIDER_CODE,
               'severity': 3, 'title': 'שומרי הדרך',
               'description': json.dumps(description),
               'locationAccuracy': 1, 'type': CONST.MARKER_TYPE_ACCIDENT}


def parse(filename):
    app = init_flask()
    db = SQLAlchemy(app)

    for batch in batch_iterator(_iter_rows(filename), batch_size=50):
        db.session.bulk_insert_mappings(Marker, batch)
        db.session.commit()
