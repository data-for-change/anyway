import json
from typing import List
import pandas as pd
from sqlalchemy.orm import aliased
from sqlalchemy import and_
from flask import request, Response
from anyway.models import (
    SDAccident, SDInvolved,
    City, InjurySeverity, Streets, Sex, RoadLight, RoadType, AgeGroup,
)
from anyway.app_and_db import app, db

class InvolvedQuery:
    def __init__(self):
        self.S1: Streets = aliased(Streets)
        self.S2: Streets = aliased(Streets)
        self.fill_text_tables()


    def get_data(self):
        data = self.get_data_from_db()
        [self.add_text(d) for d in data]
        return data

    def get_data_from_db(self):
        query = (
            db.session.query(SDInvolved, SDAccident, )
            .join(SDAccident,
                and_(SDInvolved.provider_code == SDAccident.provider_code,
                    SDInvolved.accident_id == SDAccident.accident_id,
                    SDInvolved.accident_year == SDAccident.accident_year))
            # .filter(SDAccident.yishuv_symbol == 5000)
            # .filter(SDInvolved.id == 26833652)
            .with_entities(
                SDInvolved.involve_id,
                SDInvolved.injury_severity,
                SDInvolved.injured_type,
                SDInvolved.age_group,
                SDInvolved.sex,
                SDInvolved.population_type,
                SDAccident.accident_year,
                SDAccident.accident_timestamp,
                SDAccident.lat,
                SDAccident.lon,
            )
            .limit(50)
        )
        # pylint: disable=no-member
        results = pd.read_sql_query(query.statement, query.session.bind).to_dict(
            orient="records"
        )  # pylint: disable=no-member
        return results

    def add_text(self, d: dict) -> None:
        n = d["injury_severity"]
        d["injury_severity"] = self.injury_severity[n] if n else None
        n = d["sex"]
        d["sex"] = self.sex[n] if n else None
        n = d["age_group"]
        d["age_group"] = ("85+" if n == 99 else self.age_group[n]) if n else None
        n = d["injured_type"]
        d["injured_type"] = self.injured_type[n] if n else None
        n = d["population_type"]
        d["population_type"] = self.population_type[n] if n else None

    def fill_text_tables(self):
        self.injury_severity = ["0", "הרוג", "פצוע קשה", "פצוע בינוני"]
        self.sex = ["0", "זכר", "נקבה"]
        self.age_group = ["0", "0-4", "5-9", "10-14", "15-19", "20-24", "25-29", "30-34", "35-39", "40-44", "45-49", "50-54", "55-59", "60-64", "65-69", "70-74", "75-79", "80-84", "85+"]
        self.injured_type = ["0", "הולך רגל", "נהג - רכב בעל 4 גלגלים ויותר", "נוסע - רכב בעל 4 גלגלים ויותר", "נהג - אופנוע", "נוסע - אופנוע (לא נהג)", "נהג - אופניים", "נוסע - אופניים (לא נהג)", "נהג - רכב לא ידוע", "נוסע - רכב לא ידוע"]
        self.population_type = ["0", "יהודים", "ערבים", "אחרים", "זרים"]

