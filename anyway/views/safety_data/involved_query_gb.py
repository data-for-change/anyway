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
        if gb is None:
            msg = f"'gb' missing: params: {vals}"
            logging.error(msg)
            raise ValueError(msg)
        gb2 = vals.pop(GB2, None)
        query = self.get_base_query()
        query = ParamFilterExp.add_params_filter(query, vals)
        query = self.add_gb_filter(query, gb)
        # pylint: disable=no-member
        data = query.all()
        if gb2 is not None:
            data = wd.retro_dictify(data)
        # [self.add_text(d) for d in data]
        return data

    def add_gb_filter(self, query: Query, gb: str) -> Query:
        return (query
                .group_by(SDAccident.accident_year, Sex.sex_hebrew)
                .with_entities(SDAccident.accident_year, Sex.sex_hebrew, db.func.count(SDInvolved._id).label("count"))
        )
