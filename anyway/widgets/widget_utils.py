import copy
import logging
import typing
from collections import defaultdict
from typing import Dict, Any, List, Type, Optional

import pandas as pd
from flask_babel import _
from sqlalchemy import func

from anyway.app_and_db import db
from anyway.backend_constants import BE_CONST, LabeledCode


def get_query(table_obj, filters, start_time, end_time):
    query = db.session.query(table_obj)
    if start_time:
        query = query.filter(getattr(table_obj, "accident_timestamp") >= start_time)
    if end_time:
        query = query.filter(getattr(table_obj, "accident_timestamp") <= end_time)
    if filters:
        for field_name, value in filters.items():
            if isinstance(value, list):
                values = value
            else:
                values = [value]
            query = query.filter((getattr(table_obj, field_name)).in_(values))
    return query


def get_accidents_stats(
    table_obj, filters=None, group_by=None, count=None, start_time=None, end_time=None
):
    filters = filters or {}
    provider_code_filters = [BE_CONST.CBS_ACCIDENT_TYPE_1_CODE, BE_CONST.CBS_ACCIDENT_TYPE_3_CODE]
    filters["provider_code"] = filters.get("provider_code", provider_code_filters)

    # get stats
    query = get_query(table_obj, filters, start_time, end_time)
    if group_by:
        if isinstance(group_by, tuple):
            if len(group_by) == 2:
                query = query.group_by(*group_by)
                query = query.with_entities(*group_by, func.count(count))
                dd = query.all()
                res = retro_dictify(dd)
                return res
            else:
                err_msg = f"get_accidents_stats: {group_by}: Only a string or a tuple of two are valid for group_by"
                logging.error(err_msg)
                raise Exception(err_msg)
        else:
            query = query.group_by(group_by)
            query = query.with_entities(group_by, func.count(count))
    df = pd.read_sql_query(query.statement, query.session.bind)
    df.rename(columns={"count_1": "count"}, inplace=True)  # pylint: disable=no-member
    df.columns = [c.replace("_hebrew", "") for c in df.columns]
    return (  # pylint: disable=no-member
        df.to_dict(orient="records") if group_by or count else df.to_dict()
    )


# noinspection Mypy
def retro_dictify(indexable) -> Dict[Any, Dict[Any, Any]]:
    d = defaultdict(dict)
    for row in indexable:
        here = d
        for elem in row[:-2]:
            if elem not in here:
                here[elem] = defaultdict(lambda: 0)
            here = here[elem]
        here[row[-2]] = row[-1]
    return d


def add_empty_keys_to_gen_two_level_dict(
    d, level_1_values: List[Any], level_2_values: List[Any], default_level_3_value: int = 0
) -> Dict[Any, Dict[Any, int]]:
    for v1 in level_1_values:
        if v1 not in d:
            d[v1] = {}
        for v2 in level_2_values:
            if v2 not in d[v1]:
                d[v1][v2] = default_level_3_value
    return d


def gen_entity_labels(entity: Type[LabeledCode]) -> dict:
    res = {}
    for code in entity:
        label = code.get_label()
        res[label] = _(label)
    return res


def get_injured_filters(location_info):
    new_filters = {}
    for curr_filter, curr_values in location_info.items():
        if curr_filter in ["region_hebrew", "district_hebrew", "yishuv_name"]:
            new_filter_name = "accident_" + curr_filter
            new_filters[new_filter_name] = curr_values
        else:
            new_filters[curr_filter] = curr_values
    new_filters["injury_severity"] = [1, 2, 3, 4, 5]
    return new_filters


def run_query(query: db.session.query) -> Dict:
    # pylint: disable=no-member
    return pd.read_sql_query(query.statement, query.session.bind).to_dict(orient="records")


# TODO: Find a better way to deal with typing.Union[int, str]
def format_2_level_items(
    items: Dict[typing.Union[int, str], dict],
    level1_vals: Optional[Type[LabeledCode]],
    level2_vals: Optional[Type[LabeledCode]],
):
    res: List[Dict[str, Any]] = []
    for l1_code, year_res in items.items():
        l1 = level1_vals.labels()[level1_vals(l1_code)] if level1_vals else l1_code
        series_data = []
        for l2_code, num in year_res.items():
            l2 = level2_vals.labels()[level2_vals(l2_code)] if level2_vals else l2_code
            series_data.append({BE_CONST.LKEY: l2, BE_CONST.VAL: num})
        res.append({BE_CONST.LKEY: l1, BE_CONST.SERIES: series_data})
    return res


def second_level_fill_and_sort(data: dict, default_order: dict) -> dict:
    for num, value in data.items():
        new_value = copy.deepcopy(default_order)
        for key, value_in in value.items():
            new_value[key] += value_in
        data[num] = new_value

    return data


def fill_and_sort_by_numeric_range(
    data: defaultdict, numeric_range: typing.Iterable, default_order: dict
) -> Dict[int, dict]:
    for item in numeric_range:
        if item not in data:
            data[item] = default_order
    return dict(sorted(data.items()))


def sort_and_fill_gaps_for_stacked_bar(
    data: defaultdict, numeric_range: typing.Iterable, default_order: dict
) -> Dict[int, dict]:
    res = fill_and_sort_by_numeric_range(data, numeric_range, default_order)
    res2 = second_level_fill_and_sort(res, default_order)
    return res2
