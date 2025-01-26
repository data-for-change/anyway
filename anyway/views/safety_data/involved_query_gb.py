from typing import List, Dict, Optional, Tuple, Any
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
from anyway.widgets import widget_utils as wd
from anyway.views.safety_data.involved_query import InvolvedQuery, ParamFilterExp

GB = "gb"
GB2 = "gb2"


class InvolvedQuery_GB(InvolvedQuery):
    def __init__(self):
        super().__init__()

    def get_data(self) -> List[Dict[str, Optional[str]]]:
        vals = self.get_params()
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
        query = ParamFilterExp.add_params_filter(query, vals)
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
        c1 = GBFilt2Col.get_col(gb)
        if gb2 is None:
            return (query
                    .group_by(c1)
                    # pylint: disable=no-member
                    .with_entities(c1.label(gb), db.func.count(SDInvolved._id).label("count"))
            )
        c2 = GBFilt2Col.get_col(gb2)
        return (query
                .group_by(c1, c2)
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

class GBFilt2Col:
    PFE = {
        "year": {
            "col": SDAccident.accident_year,
        },
        "sex": {
            "col": Sex.sex_hebrew,
        },
    }

    @staticmethod
    def get_col(filt: str) -> Column:
        if filt not in GBFilt2Col.PFE:
            msg = f"filter not recognized as group by: {filt}"
            logging.error(msg)
            raise ValueError(msg)
        return GBFilt2Col.PFE[filt]["col"]