from typing import List, Dict, Optional, Tuple, Any
from copy import copy
from sqlalchemy import or_
from sqlalchemy.schema import Column
from sqlalchemy.orm.query import Query
import logging
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
    RoadType,
    RoadWidth,
    SDAccident,
    SDInvolved,
    Sex,
    SpeedLimit,
)
from anyway.app_and_db import db
from anyway.widgets import widget_utils as wd
from anyway.views.safety_data.involved_query import InvolvedQuery, ParamFilterExp
from anyway.views.safety_data import sd_utils as sdu

GB = "gb"
GB2 = "gb2"


class InvolvedQuery_GB(InvolvedQuery):
    def __init__(self):
        super().__init__()
        self.gb_filt = GBFilt2Col(self.S1)

    def get_data(self) -> List[Dict[str, Optional[str]]]:
        vals = sdu.get_params()
        gb = vals.pop(GB, None)
        if gb is None or len(gb) != 1:
            msg = f"'gb' missing or invalid: params: {vals}"
            logging.error(msg)
            raise ValueError(msg)
        gb = gb[0]
        gb2 = vals.pop(GB2, None)
        if gb2 is not None:
            if len(gb2) != 1:
                msg = f"'gb2' should contain a single value: params: {vals}"
                logging.error(msg)
                raise ValueError(msg)
            gb2 = gb2[0]
        query = self.get_base_query()
        query, _, _ = self.add_params_filter(query, vals)
        query = self.add_gb_filter(query, gb, gb2)
        # pylint: disable=no-member
        data = query.all()
        if gb2 is None:
            res = [{"_id": x[0], "count": x[1]} for x in data]
        else:
            res = self.dictify_double_group_by(data)
        # [self.add_text(d) for d in data]
        return res

    def add_gb_filter(self, query: Query, gb: str, gb2: Optional[str]) -> Query:
        c1 = self.gb_filt.get_col(gb)
        if gb2 is None:
            return (
                query.group_by(c1)
                # pylint: disable=no-member
                .with_entities(c1.label(gb), db.func.count(SDInvolved._id).label("count"))
            )
        c2 = self.gb_filt.get_col(gb2)
        return (
            query.group_by(c1, c2)
            # pylint: disable=no-member
            .with_entities(c1, c2, db.func.count(SDInvolved._id).label("count"))
        )

    @staticmethod
    def dictify_double_group_by(data: List[Tuple[Any, Any, Any]]) -> List[Dict[str, Any]]:
        r = wd.retro_dictify(data)
        res = []
        for k, v in r.items():
            res.append({"_id": k, "count": [{"grp2": k1, "count": v1} for k1, v1 in v.items()]})
        return res

    def add_params_filter(self, query, params: Dict[str, List[str]]):
        pass_filters = {}
        for k, v in params.items():
            if k == "vcl":
                query = self.add_vcl_filter(query, v)
            elif k == "vcli":
                query = self.add_vcli_filter(query, v)
            else:
                pass_filters[k] = v
        return ParamFilterExp.add_params_filter(query, pass_filters)

    def add_vcl_filter(self, query, values: List[str]):
        expressions = []
        for v in values:
            if v.isdigit():
                val = int(v)
            else:
                raise ValueError(f"{v}:invalid vcl filter value")
            if val == 0:
                expressions.append(SDInvolved.injured_type == 1)
            else:
                expressions.append(SDInvolved.vehicle_type == val)
        query = query.filter(or_(*expressions))
        return query

    VCLI_FILTER_DATA = {
        1: {"val": sum([1 << x for x in [1]]), "name": "מכונית"},
        2: {"val": sum([1 << x for x in [2]]), "name": "טרנזיט"},
        3: {"val": sum([1 << x for x in [3]]), "name": "טנדר"},
        5: {"val": sum([1 << x for x in [4, 5, 6, 7, 24, 25]]), "name": "משאית"},
        8: {"val": sum([1 << x for x in [8, 9, 10, 19]]), "name": "אופנוע"},
        11: {"val": sum([1 << x for x in [11, 18]]), "name": "אוטובוס"},
        12: {"val": sum([1 << x for x in [12]]), "name": "מונית"},
        13: {"val": sum([1 << x for x in [13]]), "name": "רכב עבודה"},
        14: {"val": sum([1 << x for x in [14]]), "name": "טרקטור"},
        15: {"val": sum([1 << x for x in [15]]), "name": "אופניים"},
        16: {"val": sum([1 << x for x in [16]]), "name": "רכבת"},
        17: {"val": sum([1 << x for x in [17]]), "name": "אחר"},
        21: {"val": sum([1 << x for x in [21]]), "name": "קורקינט חשמלי"},
        22: {"val": sum([1 << x for x in [22]]), "name": "קלנועית"},
        23: {"val": sum([1 << x for x in [23]]), "name": "אופניים חשמליים"},
    }

    def add_vcli_filter(self, query, values: List[str]):
        all_valuse = 0
        for v in values:
            if v.isdigit():
                val = int(v)
            else:
                raise ValueError(f"{v}:invalid vcli filter value")
            if val in self.VCLI_FILTER_DATA:
                all_valuse |= self.VCLI_FILTER_DATA[val]["val"]
            else:
                raise ValueError(f"{v}:invalid vcli filter value")
        query = query.filter(SDAccident.vehicles.op("&")(all_valuse) != 0)
        return query


class GBFilt2Col:
    def __init__(self, s1_table):
        self.s1_table = s1_table

    PFE = copy(ParamFilterExp.PFE)
    PFE.update(
        {
            "year": {
                "col": SDAccident.accident_year,
            },
            "sex": {
                "col": Sex.sex_hebrew,
            },
            "ol": {
                "col": OneLane.one_lane_hebrew,
            },
            "ml": {
                "col": MultiLane.multi_lane_hebrew,
            },
            "age": {
                "col": AgeGroup.age_group_hebrew,
            },
            "pt": {
                "col": PopulationType.population_type_hebrew,
            },
            "mn": {
                "col": SDAccident.accident_month,
            },
            "dn": {
                "col": DayNight.day_night_hebrew,
            },
            "wd": {
                "col": SDAccident.day_in_week,
            },
            "rt": {
                "col": RoadType.road_type_hebrew,
            },
            "lca": {
                "col": LocationAccuracy.location_accuracy_hebrew,
            },
            "city": {
                "col": City.heb_name,
            },
            # "cpop": {
            #     "col": City.population, # todo
            # },
            "rd": {
                "col": SDAccident.road1,
            },
            "acc": {
                "col": AccidentType.accident_type_hebrew,
            },
            "selfacc": {
                "col": AccidentType.accident_type_hebrew,
            },
            "vcli": {
                "col": SDAccident.vehicles,
            },
            "sp": {
                "col": SpeedLimit.speed_limit_hebrew,
            },
            "rw": {
                "col": RoadWidth.road_width_hebrew,
            },
            "sev": {
                "col": InjurySeverity.injury_severity_hebrew,
            },
            "injt": {
                "col": InjuredType.injured_type_hebrew,
            },
        }
    )

    def get_col(self, filt: str) -> Column:
        if filt == "st":
            return self.s1_table.street_hebrew
        elif filt not in self.PFE:
            msg = f"filter not recognized as group by: {filt}"
            logging.error(msg)
            raise ValueError(msg)
        return self.PFE[filt]["col"]
