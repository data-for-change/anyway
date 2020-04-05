# -*- coding: utf-8 -*-
from ..models import EmbeddedReports
from ..utilities import init_flask
from .utils import batch_iterator
import pandas as pd
from flask_sqlalchemy import SQLAlchemy

app = init_flask()
db = SQLAlchemy(app)


def _iter_rows(filename):
    df = pd.read_csv(filename,  encoding='utf8')
    headers = ['id', 'report_name_english', 'report_name_hebrew', 'url']
    assert (df.columns == headers).all()
    for _, row in df.iterrows():
        yield {'id': int(row['id']),
               'report_name_english': row['report_name_english'],
               'report_name_hebrew': row['report_name_hebrew'],
               'url': row['url']}


def parse(filename):
    for batch in batch_iterator(_iter_rows(filename), batch_size=50):
        db.session.bulk_insert_mappings(EmbeddedReports, batch)
        db.session.commit()
