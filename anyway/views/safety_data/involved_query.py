from typing import List, Dict
import pandas as pd
from sqlalchemy.orm import aliased
from sqlalchemy import and_
from sqlalchemy.schema import Column
import logging
from flask import request
from anyway.models import (
    SDAccident,
    SDInvolved,
    Streets,
)
from anyway.app_and_db import db


class InvolvedQuery:
    vehiclt_type_to_str = [None for _ in range(1, 27)]
    vehiclt_type_to_str[1] = "רכב נוסעים פרטי"
    vehiclt_type_to_str[2] = "טרנזיט"
    vehiclt_type_to_str[3] = "טנדר"
    vehiclt_type_to_str[4] = "משאית"
    vehiclt_type_to_str[5] = "משאית"
    vehiclt_type_to_str[6] = "משאית"
    vehiclt_type_to_str[7] = "משאית"
    vehiclt_type_to_str[8] = "אופנוע"
    vehiclt_type_to_str[9] = "אופנוע"
    vehiclt_type_to_str[10] = "אופנוע"
    vehiclt_type_to_str[11] = "אוטובוס"
    vehiclt_type_to_str[12] = "מונית"
    vehiclt_type_to_str[13] = "רכב עבודה"
    vehiclt_type_to_str[14] = "טרקטור"
    vehiclt_type_to_str[15] = "אופניים"
    vehiclt_type_to_str[16] = "רכבת"
    vehiclt_type_to_str[17] = "אחר ולא ידוע"
    vehiclt_type_to_str[18] = "אוטובוס"
    vehiclt_type_to_str[19] = "אופנוע"
    vehiclt_type_to_str[20] = None
    vehiclt_type_to_str[21] = "קורקינט חשמלי"
    vehiclt_type_to_str[22] = "קלנועית חשמלית"
    vehiclt_type_to_str[23] = "אופניים חשמליים"
    vehiclt_type_to_str[24] = "משאית"
    vehiclt_type_to_str[25] = "משאית"

    def __init__(self):
        self.S1: Streets = aliased(Streets)
        self.S2: Streets = aliased(Streets)
        self.fill_text_tables()

    def get_data(self):
        params = request.values
        vals = {k: params.getlist(key=k) for k in params.keys()}
        query = self.get_base_query()
        query = ParamFilterExp.add_params_filter(query, vals)
        # pylint: disable=no-member
        df = pd.read_sql_query(query.statement, query.session.bind)
        df.rename(columns={
            'accident_type': 'accident_type_hebrew',
            'day_night': 'day_night_hebrew',
            "multi_lane": "multi_lane_hebrew",
            "one_lane": "one_lane_hebrew",
            "road_type": "road_type_hebrew",
            "road_width": "road_width_hebrew",
            "speed_limit": "speed_limit_hebrew",
            "street1": "street1_hebrew",
            "street2": "street2_hebrew",
            "location_accuracy": "location_accuracy_hebrew",
            "age_group": "age_group_hebrew",
            "injured_type": "injured_type_hebrew",
            "injury_severity": "injury_severity_hebrew",
            "population_type": "population_type_hebrew",
            "sex": "sex_hebrew",
            "vehicle_vehicle_type": "vehicle_vehicle_type_hebrew",
            },
            inplace=True,
            )
        data = df.to_dict(
            orient="records"
        )  # pylint: disable=no-member
        [self.add_text(d) for d in data]
        return data

    def get_base_query(self):
        query = (
            db.session.query(
                SDInvolved,
                SDAccident,
            ).join(
                SDAccident,
                and_(
                    SDInvolved.provider_code == SDAccident.provider_code,
                    SDInvolved.accident_id == SDAccident.accident_id,
                    SDInvolved.accident_year == SDAccident.accident_year,
                ),
            )
            # .filter(Column.__ge__(SDAccident.yishuv_symbol, 5000))
            # .filter(SDInvolved.id == 26833652)
            .with_entities(
                SDAccident.accident_timestamp,
                SDAccident.accident_year,
                SDInvolved.population_type,
                SDAccident.vehicles,
                SDAccident.latitude,
                SDAccident.longitude,
                SDInvolved._id,
                SDInvolved.age_group,
                SDInvolved.injured_type,
                SDInvolved.injury_severity,
                SDInvolved.sex,
            )
        )
        return query

    def add_text(self, d: dict) -> None:
        n = d["injury_severity_hebrew"]
        d["injury_severity_hebrew"] = self.injury_severity[n] if n else None
        n = d["sex_hebrew"]
        d["sex_hebrew"] = self.sex[n] if n else None
        n = d["age_group_hebrew"]
        d["age_group_hebrew"] = ("85+" if n == 99 else self.age_group[n]) if n else None
        n = d["injured_type_hebrew"]
        d["injured_type_hebrew"] = self.injured_type[n] if n else None
        n = d["population_type_hebrew"]
        d["population_type_hebrew"] = self.population_type[n] if n else None
        d["vehicles"] = self.vehicle_type_bit_2_heb(d["vehicles"])

    @staticmethod
    def vehicle_type_bit_2_heb(bit_map: int) -> str:
        if bit_map == 0:
            return ""
        res = [
            InvolvedQuery.vehiclt_type_to_str[vehicle_type]
            for vehicle_type in [
                1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23, 24, 25,
            ]
            if bit_map & (1 << vehicle_type) != 0
        ]
        return ", ".join(res)

    def fill_text_tables(self):
        self.injury_severity = ["0", "הרוג", "פצוע קשה", "פצוע בינוני"]
        self.sex = ["0", "זכר", "נקבה"]
        self.age_group = [
            "0",
            "0-4",
            "5-9",
            "10-14",
            "15-19",
            "20-24",
            "25-29",
            "30-34",
            "35-39",
            "40-44",
            "45-49",
            "50-54",
            "55-59",
            "60-64",
            "65-69",
            "70-74",
            "75-79",
            "80-84",
            "85+",
        ]
        self.injured_type = [
            "0",
            "הולך רגל",
            "נהג - רכב בעל 4 גלגלים ויותר",
            "נוסע - רכב בעל 4 גלגלים ויותר",
            "נהג - אופנוע",
            "נוסע - אופנוע (לא נהג)",
            "נהג - אופניים",
            "נוסע - אופניים (לא נהג)",
            "נהג - רכב לא ידוע",
            "נוסע - רכב לא ידוע",
        ]
        self.population_type = ["0", "יהודים", "ערבים", "אחרים", "זרים"]


class ParamFilterExp:
    PFE = {
        "sy": {
            "col": SDAccident.accident_year,
            "op": Column.__ge__,  # default is __eq__ or in_ for a list
            "single": True,  # default is multipe values
        },
        "ey": {
            "col": SDAccident.accident_year,
            "op": Column.__le__,
            "single": True,  # default is multipe values
        },
        "sev": {
            "col": SDInvolved.injury_severity,
        },
        "injt": {
            "col": SDInvolved.injured_type,
        },
        "city": {
            "col": SDAccident.accident_yishuv_symbol,
        },
        "st": {
            "col": SDAccident.street1,
        },
        "rd": {
            "col": SDAccident.road1,
        },
        "rds": {
            "col": SDAccident.road_segment_number,
        },
        "sex": {
            "col": SDInvolved.sex,
        },
        "age": {
            "col": SDInvolved.age_group,
        },
        "pt": {
            "col": SDInvolved.population_type,
        },
        "dn": {
            "col": SDAccident.day_night,
        },
        "mn": {
            "col": SDAccident.accident_month,
        },
        # "acc": {
        #     "col": SDAccident.accident_type,
        # },
        # "vcl": {
        #     "col": SDAccident.vehicle_types,
        # },
        "rt": {
            "col": SDAccident.road_type,
        },
        "sp": {
            "col": SDAccident.speed_limit,
        },
        "rw": {
            "col": SDAccident.road_width,
        },
        "ml": {
            "col": SDAccident.multi_lane,
        },
        "ol": {
            "col": SDAccident.one_lane,
        },
    }

    def __init__(self):
        pass

    @staticmethod
    def add_params_filter(query, params: Dict[str, List[str]]):
        for k, v in params.items():
            p = ParamFilterExp.PFE.get(k)
            if (
                p is not None
                and all([x.isdigit() for x in v])
                and ("single" not in p or len(v) == 1)
            ):
                f = (
                    ParamFilterExp.PFE[k]["op"]
                    if "op" in ParamFilterExp.PFE[k]
                    else (Column.__eq__ if len(v) == 1 else Column.in_)
                )
                val = v[0] if len(v) == 1 else v
                query = query.filter(f(ParamFilterExp.PFE[k]["col"], val))
            else:
                msg = f"Unsupported filter: {k}={v}{', param def:'+str(p) if p else ''}"
                logging.error(msg)
                raise ValueError(msg)
        return query
