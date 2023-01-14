# -*- coding: utf-8 -*-
from anyway.models import EmbeddedReports
import pandas as pd
from anyway.app_and_db import db


def _iter_rows(filename):
    df = pd.read_csv(filename, encoding="utf8")
    headers = ["id", "report_name_english", "report_name_hebrew", "url"]
    assert (df.columns == headers).all()
    for _, row in df.iterrows():
        yield {
            "id": int(row["id"]),
            "report_name_english": row["report_name_english"],
            "report_name_hebrew": row["report_name_hebrew"],
            "url": row["url"],
        }


def parse(filename):
    for row in _iter_rows(filename):
        current_report = (
            db.session.query(EmbeddedReports)
            .filter(EmbeddedReports.report_name_english == row["report_name_english"])
            .all()
        )
        if not current_report:
            db.session.bulk_insert_mappings(EmbeddedReports, [row])
        else:
            db.session.bulk_update_mappings(EmbeddedReports, [row])
        db.session.commit()
