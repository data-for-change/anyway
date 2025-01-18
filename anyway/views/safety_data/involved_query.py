from typing import List, Dict, Optional
import math
import pandas as pd
from sqlalchemy.orm import aliased
from sqlalchemy import and_
from sqlalchemy.schema import Column
from sqlalchemy.orm.query import Query
import logging
from flask import request
from anyway.models import (
    AccidentType,
    AgeGroup,
    City,
    DayNight,
    InjuredType,
    InjurySeverity,
    LocationAccuracy,
    MultiLane,
    OneLane,
    PopulationType,
    RoadSegments,
    RoadType,
    RoadWidth,
    SDAccident,
    SDInvolved,
    Sex,
    SpeedLimit,
    Streets,
)
from anyway.app_and_db import db


class InvolvedQuery:
    PEDESTRIAN_IN_VEHICLE_TYPE_ENRICHED = 99
    INVOLVED_NOT_INJURED_HEBERW = "מעורב שלא נפגע"
    PEDESTRIAN_HEBREW = "הולך רגל"
    INJURED_ENRICHED_MULT_FACTOR = 1000
    INJURED_ENRICHED_ADD_FACTOR = 100
    vehicle_type_to_str = [None for _ in range(1, 27)]
    vehicle_type_to_str[1] = ("רכב נוסעים פרטי", "רכב נוסעים פרטי")
    vehicle_type_to_str[2] = ("טרנזיט", "משא עד 3.5 טון - אחוד (טרנזיט)")
    vehicle_type_to_str[3] = ("טנדר", "משא עד 3.5 טון - לא אחוד (טנדר)")
    vehicle_type_to_str[4] = ("משאית", "משא 3.6 עד 12.0 טון")
    vehicle_type_to_str[5] = ("משאית", "משא 12.1 עד 15.9 טון")
    vehicle_type_to_str[6] = ("משאית", "משא 16.0 עד 33.9 טון")
    vehicle_type_to_str[7] = ("משאית", "משא 34.0+ טון")
    vehicle_type_to_str[8] = ("אופנוע", 'אופנוע עד 50 סמ"ק')
    vehicle_type_to_str[9] = ("אופנוע", 'אופנוע 51 עד 125 סמ"ק')
    vehicle_type_to_str[10] = ("אופנוע", 'אופנוע 126 עד 400 סמ"ק')
    vehicle_type_to_str[11] = ("אוטובוס", 'אופנוע 126 עד 400 סמ"ק')
    vehicle_type_to_str[12] = ("מונית", "מונית")
    vehicle_type_to_str[13] = ("רכב עבודה", "רכב עבודה")
    vehicle_type_to_str[14] = ("טרקטור", "טרקטור")
    vehicle_type_to_str[15] = ("אופניים", "אופניים")
    vehicle_type_to_str[16] = ("רכבת", "רכבת")
    vehicle_type_to_str[17] = ("אחר ולא ידוע", "אחר ולא ידוע")
    vehicle_type_to_str[18] = ("אוטובוס", "אוטובוס זעיר")
    vehicle_type_to_str[19] = ("אופנוע", 'אופנוע 401 סמ"ק ומעלה')
    vehicle_type_to_str[20] = (None, None)
    vehicle_type_to_str[21] = ("קורקינט חשמלי", "קורקינט חשמלי")
    vehicle_type_to_str[22] = ("קלנועית חשמלית", "קלנועית חשמלית")
    vehicle_type_to_str[23] = ("אופניים חשמליים", "אופניים חשמליים")
    vehicle_type_to_str[24] = ("משאית", "משא 3.6 עד 9.9 טון")
    vehicle_type_to_str[25] = ("משאית", "משא 10.0 עד 12.0 טון")

    def __init__(self):
        self.S1: Streets = aliased(Streets)
        self.S2: Streets = aliased(Streets)
        self.fill_text_tables()

    def get_params(self) -> dict:
        def f(v: List[str]) -> List[str]:
            res = []
            [res.extend(x.split(",")) for x in v]
            return res
        params = request.values
        vals = {k: f(params.getlist(key=k)) for k in params.keys()}
        return vals

    def get_data(self):
        def f(v: List[str]) -> List[str]:
            res = []
            [res.extend(x.split(",")) for x in v]
            return res
        vals = self.get_params()
        query = self.get_base_query()
        query = ParamFilterExp.add_params_filter(query, vals)
        # pylint: disable=no-member
        df = pd.read_sql_query(query.statement, query.session.bind)
        # df.rename(
            # columns={
                # "vehicle_type": "vehicle_vehicle_type_hebrew",
            # },
            # inplace=True,
        # )
        data = df.to_dict(orient="records")  # pylint: disable=no-member
        [self.add_text(d) for d in data]
        return data

    def get_base_query(self):
        query = (
            db.session.query(
                SDAccident.accident_timestamp,
                AccidentType.accident_type_hebrew,
                SDAccident.accident_year,
                City.heb_name.label("accident_yishuv_name"),
                SDAccident.day_in_week.label("day_in_week_hebrew"),
                DayNight.day_night_hebrew,
                LocationAccuracy.location_accuracy_hebrew,
                MultiLane.multi_lane_hebrew,
                OneLane.one_lane_hebrew,
                SDAccident.road1.label("road1"),
                SDAccident.road2.label("road2"),
                (RoadSegments.from_name + " - " + RoadSegments.to_name).label("road_segment_name"),
                RoadType.road_type_hebrew,
                RoadWidth.road_width_hebrew,
                SpeedLimit.speed_limit_hebrew,
                self.S1.street_hebrew.label("street1_hebrew"),
                self.S2.street_hebrew.label("street2_hebrew"),
                SDAccident.vehicles,
                SDAccident.latitude,
                SDAccident.longitude,
                SDInvolved._id,
                AgeGroup.age_group_hebrew,
                InjuredType.injured_type_hebrew,
                SDInvolved.injured_type.label("injured_type_short_hebrew"),
                InjurySeverity.injury_severity_hebrew,
                PopulationType.population_type_hebrew,
                SDInvolved.vehicle_type.label("vehicle_vehicle_type_hebrew"),
                Sex.sex_hebrew,
                SDInvolved.vehicle_type.label("TEST-vehicle_type"),
                SDInvolved.injured_type.label("TEST-injured_type"),
            )
            .join(
                SDAccident,
                and_(
                    SDInvolved.provider_code == SDAccident.provider_code,
                    SDInvolved.accident_id == SDAccident.accident_id,
                    SDInvolved.accident_year == SDAccident.accident_year,
                ),
            )
            .outerjoin(
                self.S1,
                and_(
                    SDAccident.street1 == self.S1.street,
                    SDAccident.accident_yishuv_symbol == self.S1.yishuv_symbol,
                ),
            )
            .outerjoin(
                self.S2,
                and_(
                    SDAccident.street2 == self.S2.street,
                    SDAccident.accident_yishuv_symbol == self.S2.yishuv_symbol,
                ),
            )
            .outerjoin(
                AccidentType,
                and_(
                    SDAccident.accident_type == AccidentType.id,
                    SDAccident.accident_year == AccidentType.year,
                    SDAccident.provider_code == AccidentType.provider_code,
                ),
            )
            .outerjoin(
                DayNight,
                and_(
                    SDAccident.accident_type == DayNight.id,
                    SDAccident.accident_year == DayNight.year,
                    SDAccident.provider_code == DayNight.provider_code,
                ),
            )
            .outerjoin(
                LocationAccuracy,
                and_(
                    SDAccident.accident_type == LocationAccuracy.id,
                    SDAccident.accident_year == LocationAccuracy.year,
                    SDAccident.provider_code == LocationAccuracy.provider_code,
                ),
            )
            .outerjoin(
                MultiLane,
                and_(
                    SDAccident.accident_type == MultiLane.id,
                    SDAccident.accident_year == MultiLane.year,
                    SDAccident.provider_code == MultiLane.provider_code,
                ),
            )
            .outerjoin(
                OneLane,
                and_(
                    SDAccident.accident_type == OneLane.id,
                    SDAccident.accident_year == OneLane.year,
                    SDAccident.provider_code == OneLane.provider_code,
                ),
            )
            .outerjoin(
                RoadType,
                and_(
                    SDAccident.accident_type == RoadType.id,
                    SDAccident.accident_year == RoadType.year,
                    SDAccident.provider_code == RoadType.provider_code,
                ),
            )
            .outerjoin(
                RoadWidth,
                and_(
                    SDAccident.accident_type == RoadWidth.id,
                    SDAccident.accident_year == RoadWidth.year,
                    SDAccident.provider_code == RoadWidth.provider_code,
                ),
            )
            .outerjoin(
                SpeedLimit,
                and_(
                    SDAccident.accident_type == SpeedLimit.id,
                    SDAccident.accident_year == SpeedLimit.year,
                    SDAccident.provider_code == SpeedLimit.provider_code,
                ),
            )
            .outerjoin(
                AgeGroup,
                and_(
                    SDAccident.accident_type == AgeGroup.id,
                    SDAccident.accident_year == AgeGroup.year,
                    SDAccident.provider_code == AgeGroup.provider_code,
                ),
            )
            .outerjoin(
                InjuredType,
                and_(
                    SDAccident.accident_type == InjuredType.id,
                    SDAccident.accident_year == InjuredType.year,
                    SDAccident.provider_code == InjuredType.provider_code,
                ),
            )
            .outerjoin(
                InjurySeverity,
                and_(
                    SDAccident.accident_type == InjurySeverity.id,
                    SDAccident.accident_year == InjurySeverity.year,
                    SDAccident.provider_code == InjurySeverity.provider_code,
                ),
            )
            .outerjoin(
                PopulationType,
                and_(
                    SDAccident.accident_type == PopulationType.id,
                    SDAccident.accident_year == PopulationType.year,
                    SDAccident.provider_code == PopulationType.provider_code,
                ),
            )
            .join(
                Sex,
                and_(
                    SDAccident.accident_type == Sex.id,
                    SDAccident.accident_year == Sex.year,
                    SDAccident.provider_code == Sex.provider_code,
                ),
            )
            .outerjoin(City, SDAccident.accident_yishuv_symbol == City.yishuv_symbol)
            .outerjoin(RoadSegments, SDAccident.road_segment_number == RoadSegments.segment)
        )
        return query

    def add_text(self, d: dict) -> None:
        # n = d["injury_severity_hebrew"]
        # d["injury_severity_hebrew"] = self.injury_severity[n] if n else None
        # n = d["sex_hebrew"]
        # d["sex_hebrew"] = self.sex[n] if n else None
        # n = d["age_group_hebrew"]
        # d["age_group_hebrew"] = ("85+" if n == 99 else self.age_group[n]) if n else None
        # n = d["injured_type_hebrew"]
        # d["injured_type_hebrew"] = self.injured_type[n] if n else None
        # n = d["population_type_hebrew"]
        # d["population_type_hebrew"] = self.population_type[n] if n else None
        d["vehicles"] = self.vehicle_type_bit_2_heb(d["vehicles"])
        n = d["day_in_week_hebrew"]
        d["day_in_week_hebrew"] = self.day_in_week[n] if n else None
        injured_type = d["TEST-injured_type"]
        injured_type_hebrew = d["injured_type_hebrew"]
        d["injured_type_short_hebrew"] = (
            injured_type_hebrew.split(" - ")[0] if injured_type_hebrew
            else self.INVOLVED_NOT_INJURED_HEBERW
        )
        vehicle_type = d["vehicle_vehicle_type_hebrew"]
        vehicle_type = None if math.isnan(vehicle_type) else int(vehicle_type)
        d["vehicle_type_short_hebrew"] = self.vehicle_type_to_str[vehicle_type][0] if vehicle_type else None
        d["vehicle_vehicle_type_hebrew"] = (
            self.PEDESTRIAN_HEBREW if injured_type == 1 else (
                self.vehicle_type_to_str[vehicle_type][1] if vehicle_type
                else None
            )
        )
        # d["injured_type_hebrew"] = self.get_injured_type_enriched_hebrew(injured_type, vehicle_type)
        # d["injured_type_hebrew"] = (
        #     f"{self.vehicle_type_to_str[vehicle_type][0]} - מעורב שלא נפגע" if not injured_type
        #     else (f"{self.injured_type[injured_type]}-  "
        #           if vehicle_type is not None else (

        #     )
        #     )
        # )

    def get_injured_type_enriched_hebrew(self, injured_type: Optional[int], vehicle_type: Optional[int]) -> Optional[str]:
        vehicle_hebrew_short = self.vehicle_type_to_str[vehicle_type][0] if vehicle_type else None
        injured_hebrew = self.injured_type[injured_type] if isinstance(injured_type, int) else None
        if not injured_type:
            return f"{vehicle_hebrew_short} - מעורב שלא נפגע"
        elif vehicle_type is not None:
            return f"{injured_hebrew.split(' - ')[0]} - {vehicle_hebrew_short}"
        else:
            return injured_hebrew


    @staticmethod
    def vehicle_type_bit_2_heb(bit_map: int) -> str:
        if bit_map == 0:
            return ""
        res = [
            InvolvedQuery.vehicle_type_to_str[vehicle_type][0]
            for vehicle_type in [
                1,
                2,
                3,
                4,
                5,
                6,
                7,
                8,
                9,
                10,
                11,
                12,
                13,
                14,
                15,
                16,
                17,
                18,
                19,
                21,
                22,
                23,
                24,
                25,
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
        self.day_in_week = ["0", "ראשון", "שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת"]


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
        "acc": {
            "col": SDAccident.accident_type,
        },
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
