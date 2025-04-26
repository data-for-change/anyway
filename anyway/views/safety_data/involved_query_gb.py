from typing import List, Dict, Optional, Tuple, Any
from copy import copy
from sqlalchemy import case, desc, asc, not_
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
LIMIT = "lim"
SORT = "sort"


class InvolvedQuery_GB(InvolvedQuery):
    def __init__(self):
        super().__init__()
        self.gb_filt = GBFilt2Col(self.S1)

    def get_data(self) -> List[Dict[str, Optional[str]]]:
        vals = sdu.get_params()
        involved_vals, gb_vals = split_dict(vals, [GB, GB2, LIMIT, SORT])
        query = self.get_base_query()
        query, _, _, count = ParamFilterExp.add_params_filter(query, involved_vals)
        if count:
            raise ValueError("count is not supported in group by. params: %s" % vals)
        query, gb, gb2 = self.add_gb_filter(query, gb_vals)
        # pylint: disable=no-member
        dat = query.all()
        data = self.add_gb_text(dat, gb, gb2)
        if gb2 is None:
            res = [{"_id": x[0], "count": x[1]} for x in data]
        else:
            res = self.dictify_double_group_by(data)
        return res

    def add_gb_filter(self, query: Query, vals: dict) -> Query:
        gb, gb2, vals = self.get_gb_vals(vals)
        c1 = self.gb_filt.get_col(gb)
        c1_val = self.gb_filt.get_gb_filt_val(gb)
        if c1_val is not None:
            query = query.filter(not_(c1[-1].in_(c1_val)))
        query = query.filter(c1[-1] != None)
        if gb2 is None:
            query = (
                query.group_by(c1[0])
                # pylint: disable=no-member
                .with_entities(c1[0].label(gb), db.func.count(SDInvolved._id).label("count"))
            )
        else:
            c2 = self.gb_filt.get_col(gb2)
            c2_val = self.gb_filt.get_gb_filt_val(gb2)
            if c2_val is not None:
                query = query.filter(not_(c2[-1].in_(c2_val)))
            query = query.filter(c2[-1] != None)
            query = (
                query.group_by(c1[0], c2[0])
                # pylint: disable=no-member
                .with_entities(c1[0], c2[0], db.func.count(SDInvolved._id).label("count"))
            )
        query, vals = self.add_gb_sort_limit(query, vals)
        return query, gb, gb2

    def add_gb_sort_limit(self, query: Query, vals_orig: dict) -> Tuple[Query, dict]:
        vals = vals_orig.copy()
        limit = vals.pop(LIMIT, ["0"])[0]
        if not limit.isdigit():
            raise ValueError(f"Invalid limit value: {limit}")
        limit = int(limit)
        sort = vals.pop(SORT, [None])
        if len(sort) > 1 or sort[0] not in [None, "a", "d"]:
            raise ValueError(f"Invalid sort value: {sort}")
        sort_f = desc if sort[0] == "d" else (asc if sort[0] == "a" else None)
        if sort_f:
            query = query.order_by(sort_f("count"))
        if limit:
            query = query.limit(limit)
        return query, vals

    def get_gb_vals(self, vals_orig: dict) -> Tuple[str, Optional[str], dict]:
        vals = vals_orig.copy()
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
        return gb, gb2, vals

    def add_gb_text(self, d: List[Tuple], gb: str, gb2: Optional[str]) -> List[Tuple]:
        if gb == "vcl":
            res = [
                (self.vehicle_type_to_str[x[0]].full if x[0] is not None else None, *x[1:])
                for x in d
            ]
        elif gb == "vcli":
            res = [
                (self.vehicle_type_bit_2_heb(x[0]) if x[0] is not None else None, *x[1:]) for x in d
            ]
        elif gb == "cpop":
            res = self.add_cpop_text(d, gb2)
        else:
            res = d
        return res

    def add_gb2_text(self, d: List[Tuple], gb: str, gb2: Optional[str]) -> List[Tuple]:
        if gb == "vcl":
            res = [
                (self.vehicle_type_to_str[x[0]].full if x[0] is not None else None, *x[1:])
                for x in d
            ]
        if gb == "vcli":
            res = [
                (self.vehicle_type_bit_2_heb(x[0]) if x[0] is not None else None, *x[1:]) for x in d
            ]
        elif gb == "cpop":
            res = self.add_cpop_text(d, gb2)
        else:
            res = d
        return res

    @staticmethod
    def add_cpop_text(d: List[Tuple], bg2: str) -> List[Tuple]:
        def get_city(sym: int) -> tuple:
            return (
                db.session.query(City.heb_name, City.population)
                .filter(City.yishuv_symbol == sym)
                .first()
            )

        res = []
        for x in d:
            if x[0] in [None, 0]:
                continue
            c = get_city(x[0])
            if c is None:
                continue
            name, pop = c
            if bg2:
                res.append((name, x[1], (x[2] * 100000) / pop))
            else:
                res.append((name, (x[1] * 100000) / pop))
        return res

    @staticmethod
    def dictify_double_group_by(data: List[Tuple[Any, Any, Any]]) -> List[Dict[str, Any]]:
        r = wd.retro_dictify(data)
        res = []
        for k, v in r.items():
            res.append({"_id": k, "count": [{"grp2": k1, "count": v1} for k1, v1 in v.items()]})
        return res


def split_dict(d: dict, keys: List[str]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    orig = {}
    new = {}
    for k, v in d.items():
        if k in keys:
            new[k] = v
        else:
            orig[k] = v
    return orig, new


class GBFilt2Col:
    def __init__(self, s1_table):
        self.s1_table = s1_table

    PFE_GB = copy(ParamFilterExp.PFE)
    PFE_GB: Dict[str, Tuple] = {
        "year": {
            "col": (SDAccident.accident_year,),
        },
        "sex": {
            "col": (Sex.sex_hebrew, SDInvolved.sex),
        },
        "ol": {
            "col": (OneLane.one_lane_hebrew, SDAccident.one_lane),
        },
        "ml": {
            "col": (MultiLane.multi_lane_hebrew, SDAccident.multi_lane),
        },
        "age": {
            "col": (AgeGroup.age_group_hebrew, SDInvolved.age_group),
        },
        "pt": {
            "col": (PopulationType.population_type_hebrew, SDInvolved.population_type),
        },
        "mn": {
            "col": (SDAccident.accident_month,),
        },
        "dn": {
            "col": (DayNight.day_night_hebrew, SDAccident.day_night),
        },
        "wd": {
            "col": (SDAccident.day_in_week,),
        },
        "rt": {
            "col": (RoadType.road_type_hebrew, SDAccident.road_type),
        },
        "lca": {
            "col": (LocationAccuracy.location_accuracy_hebrew, SDAccident.location_accuracy),
        },
        "city": {
            "col": (City.heb_name, SDAccident.accident_yishuv_symbol),
        },
        "cpop": {
            "col": (City.yishuv_symbol,),
        },
        "rd": {
            "col": (SDAccident.road1,),
        },
        "acc": {
            "col": (AccidentType.accident_type_hebrew, SDAccident.accident_type),
        },
        "selfacc": {
            "col": (AccidentType.accident_type_hebrew, SDAccident.accident_type),
        },
        "vcl": {
            "col": (case([(SDInvolved.injured_type == 1, 0)], else_=SDInvolved.vehicle_type),),
        },
        "vcli": {
            "col": (SDAccident.vehicles,),
        },
        "sp": {
            "col": (SpeedLimit.speed_limit_hebrew, SDAccident.speed_limit),
        },
        "rw": {
            "col": (RoadWidth.road_width_hebrew, SDAccident.road_width),
        },
        "sev": {
            "col": (InjurySeverity.injury_severity_hebrew, SDInvolved.injury_severity),
        },
        "injt": {
            "col": (InjuredType.injured_type_hebrew, SDInvolved.injured_type),
        },
    }

    def get_col(self, filt: str) -> Tuple[Column, ...]:
        if filt == "st":
            return (self.s1_table.street_hebrew, SDAccident.street1)
        elif filt not in self.PFE_GB:
            msg = f"filter not recognized as group by: {filt}"
            logging.error(msg)
            raise ValueError(msg)
        return self.PFE_GB[filt]["col"]

    FILT_TO_EMPTY = {
        "city": [0],
        "age": [99],
        "ol": [0],
        "ml": [0],
        "sev": [0],
        "injt": [0],
        "rw": [0],
    }

    def get_gb_filt_val(self, filt: str) -> Any:
        return self.FILT_TO_EMPTY.get(filt, None)
