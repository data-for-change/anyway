# -*- coding: utf-8 -*-
from anyway.models import CasualtiesCosts
import pandas as pd
import logging
from anyway.app_and_db import db


def _iter_rows(filename):
    df = pd.read_csv(filename, encoding="utf8")
    headers = ["type_id", "injured_type", "desc_heb", "injuries_cost_k", "year", "data_source"]
    assert (df.columns == headers).all()
    for _, row in df.iterrows():
        yield {
            "id": int(row["type_id"]),
            "injured_type": row["injured_type"],
            "injured_type_hebrew": row["desc_heb"],
            "injuries_cost_k": int(row["injuries_cost_k"].replace(",", "")),
            "year": int(row["year"]),
            "data_source_hebrew": row["data_source"],
        }


def parse(filename):
    for row in _iter_rows(filename):
        current_report = (
            db.session.query(CasualtiesCosts).filter(CasualtiesCosts.id == row["id"]).all()
        )
        if not current_report:
            logging.debug(f"adding line {row}")
            db.session.bulk_insert_mappings(CasualtiesCosts, [row])
        else:
            logging.debug(f"updating line {row}")
            db.session.bulk_update_mappings(CasualtiesCosts, [row])
        db.session.commit()
