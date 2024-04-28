import copy
import logging
import typing
from collections import defaultdict
from typing import Dict, Any, List, Type, Optional, Sequence, Tuple

import pandas as pd

# noinspection PyProtectedMember
from flask_babel import _
from sqlalchemy import func, distinct, between, or_, and_

from anyway.app_and_db import db
from anyway.backend_constants import BE_CONST, LabeledCode, InjurySeverity
from anyway.models import InvolvedMarkerView
from anyway.request_params import LocationInfo
from anyway.vehicle_type import VehicleType
from anyway.parsers.resolution_fields import ResolutionFields as RF
from anyway.models import NewsFlash
from anyway.request_params import RequestParams
from anyway.widgets.segment_junctions import SegmentJunctions

RC = BE_CONST.ResolutionCategories


def get_query(table_obj, filters, start_time, end_time):
    if "road_segment_name" in filters and "road_segment_id" in filters:
        filters = copy.copy(filters)
        filters.pop("road_segment_name")
    query = db.session.query(table_obj)
    if start_time:
        query = query.filter(getattr(table_obj, "accident_timestamp") >= start_time)
    if end_time:
        query = query.filter(getattr(table_obj, "accident_timestamp") <= end_time)
    if not filters:
        return query
    if "road_segment_id" not in filters.keys():
        query = query.filter(get_expression_for_non_road_segment_fields(filters, table_obj, and_))
        return query
    location_fields, other_fields = split_location_fields_and_others(filters)
    if other_fields:
        query = query.filter(
            get_expression_for_non_road_segment_fields(other_fields, table_obj, and_)
        )
    query = query.filter(
        get_expression_for_road_segment_location_fields(location_fields, table_obj)
    )
    return query


def get_expression_for_fields(filters: dict, table_obj):
    op_other, op_segment = None, None
    if "road_segment_id" not in filters.keys():
        return get_expression_for_non_road_segment_fields(filters, table_obj, and_)
    location_fields, other_fields = split_location_fields_and_others(filters)
    if other_fields:
        op_other = get_expression_for_non_road_segment_fields(other_fields, table_obj, and_)
    op_segment = get_expression_for_road_segment_location_fields(location_fields, table_obj)
    return op_segment if op_other is None else and_(op_segment, op_other)


def get_expression_for_non_road_segment_fields(filters, table_obj, op):
    items = list(filters.items())
    if len(items) == 0:
        return True
    field_name, value = items[0]
    ex = get_filter_expression(table_obj, field_name, value)
    for field_name, value in items[1:]:
        ex2 = get_filter_expression(table_obj, field_name, value)
        ex = op(ex, ex2)
    return ex


# todo: remove road_segment_name if road_segment_id exists.
def get_expression_for_road_segment_location_fields(filters, table_obj):
    ex = get_expression_for_non_road_segment_fields(filters, table_obj, and_)
    segment_id = filters["road_segment_id"]
    junctions_ex = get_expression_for_segment_junctions(segment_id, table_obj)
    res = or_(ex, junctions_ex)
    return res


def get_expression_for_segment_junctions(segment_id: int, table_obj):
    sg = SegmentJunctions.get_instance()
    junctions = sg.get_segment_junctions(segment_id)
    return getattr(table_obj, "non_urban_intersection").in_(junctions)


def get_filter_expression(table_obj, field_name, value):
    if field_name == "street1_hebrew" or field_name == "street1":
        return or_(
            get_filter_expression_raw(table_obj, field_name, value),
            get_filter_expression_raw(table_obj, field_name.replace("1", "2"), value),
        )
    else:
        return get_filter_expression_raw(table_obj, field_name, value)


def get_filter_expression_raw(table_obj, field_name, value):
    if isinstance(value, list):
        return (getattr(table_obj, field_name)).in_(value)
    else:
        return (getattr(table_obj, field_name)) == value


def split_location_fields_and_others(filters: dict) -> Tuple[dict, dict]:
    all_location_fields = RF.get_all_location_fields()
    fields = filters.keys()
    location_fields = {x: filters[x] for x in fields if x in all_location_fields}
    other_fields = {x: filters[x] for x in fields if x not in all_location_fields}
    return location_fields, other_fields


def get_accidents_stats(
    table_obj,
    columns=None,
    filters=None,
    group_by=None,
    count=None,
    cnt_distinct=False,
    start_time=None,
    end_time=None,
    resolution: Optional[RC] = None,
):
    filters = filters or {}
    filters = add_resolution_location_accuracy_filter(filters, resolution)
    provider_code_filters = [
        BE_CONST.CBS_ACCIDENT_TYPE_1_CODE,
        BE_CONST.CBS_ACCIDENT_TYPE_3_CODE,
    ]
    filters["provider_code"] = filters.get("provider_code", provider_code_filters)

    # get stats
    query = get_query(table_obj, filters, start_time, end_time)
    if columns:
        query = query.with_entities(*columns)
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
            query = query.with_entities(
                group_by,
                func.count(count) if not cnt_distinct else func.count(distinct(count)),
            )
    df = pd.read_sql_query(query.statement, query.session.bind)
    df.rename(columns={"count_1": "count"}, inplace=True)  # pylint: disable=no-member
    df.columns = [c.replace("_hebrew", "") for c in df.columns]
    return (  # pylint: disable=no-member
        df.to_dict(orient="records") if group_by or count else df.to_dict()
    )


# noinspection Mypy
def retro_dictify(iterable) -> Dict[Any, Dict[Any, Any]]:
    d = defaultdict(dict)
    for row in iterable:
        here = d
        for elem in row[:-2]:
            if elem not in here:
                here[elem] = defaultdict(lambda: 0)
            here = here[elem]
        here[row[-2]] = row[-1]
    return d


def add_empty_keys_to_gen_two_level_dict(
    d,
    level_1_values: List[Any],
    level_2_values: List[Any],
    default_level_3_value: int = 0,
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


def get_involved_marker_view_location_filters(
    resolution: BE_CONST.ResolutionCategories, location_info: LocationInfo
):
    filters = {}
    if resolution == BE_CONST.ResolutionCategories.STREET:
        filters["involve_yishuv_name"] = location_info.get("yishuv_name")
        filters["street1_hebrew"] = location_info.get("street1_hebrew")
    elif resolution == BE_CONST.ResolutionCategories.SUBURBAN_ROAD:
        filters["road1"] = location_info.get("road1")
        filters["road_segment_id"] = location_info.get("road_segment_id")
    return filters


def get_injured_filters(request_params: RequestParams):
    new_filters = get_involved_marker_view_location_filters(
        request_params.resolution, request_params.location_info
    )
    for curr_filter, curr_values in request_params.location_info.items():
        if curr_filter in ["region_hebrew", "district_hebrew", "yishuv_name"]:
            new_filter_name = "accident_" + curr_filter
            new_filters[new_filter_name] = curr_values

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


# noinspection PyUnresolvedReferences
def get_involved_counts(
    start_year: int,
    end_year: int,
    severities: Sequence[InjurySeverity],
    vehicle_types: Sequence[VehicleType],
    location_info: LocationInfo,
) -> Dict[str, int]:
    table = InvolvedMarkerView

    selected_columns = (
        table.accident_year.label("label_key"),
        func.count(distinct(table.involve_id)).label("value"),
    )

    query = (
        db.session.query()
        .select_from(table)
        .with_entities(*selected_columns)
        .filter(between(table.accident_year, start_year, end_year))
        .order_by(table.accident_year)
    )
    filters = add_resolution_location_accuracy_filter(location_info, table)
    if "yishuv_symbol" in location_info:
        filters["accident_yishuv_symbol"] = filters["yishuv_symbol"]
        filters.pop("yishuv_symbol")
        filters.pop("yishuv_name", None)
    ex = get_expression_for_fields(filters, table)
    query = query.filter(ex).group_by(table.accident_year)

    if severities:
        query = query.filter(table.injury_severity.in_([severity.value for severity in severities]))

    if vehicle_types:
        query = query.filter(
            table.involve_vehicle_type.in_([v_type.value for v_type in vehicle_types])
        )
    # todo: check for suburban junction resolution
    df = pd.read_sql_query(query.statement, query.session.bind)
    return df.to_dict(orient="records")  # pylint: disable=no-member


def join_strings(strings, sep_a=" ,", sep_b=" ו-"):
    if len(strings) < 2:
        return "".join(strings)
    elif len(strings) == 2:
        return sep_b.join(strings)
    else:
        return sep_a.join(strings[:-1]) + sep_b + strings[-1]


def newsflash_has_location(newsflash: NewsFlash):
    resolution = newsflash.resolution
    return (
        resolution == BE_CONST.ResolutionCategories.SUBURBAN_ROAD.value
        and newsflash.road_segment_name
    ) or (resolution == BE_CONST.ResolutionCategories.STREET.value and newsflash.street1_hebrew)


def get_location_text(request_params: RequestParams) -> str:
    in_str = _("in")
    if request_params.resolution == BE_CONST.ResolutionCategories.SUBURBAN_ROAD:
        return f'{_("in segment")} {_(request_params.location_info["road_segment_name"])}'
    elif request_params.resolution == BE_CONST.ResolutionCategories.STREET:
        return f'{_("in street")} {request_params.location_info["street1_hebrew"]} {in_str}{request_params.location_info["yishuv_name"]}'


__RESOLUTION_ACCURACY_VALUES: dict = {
    RC.SUBURBAN_JUNCTION: [1, 4],
    RC.SUBURBAN_ROAD: [1, 4],
    RC.URBAN_JUNCTION: [1, 3],
    RC.STREET: [1, 3],
}


def get_resolution_location_accuracy_filter(rc: RC) -> Optional[dict]:
    vals = __RESOLUTION_ACCURACY_VALUES.get(rc)
    return {"location_accuracy": vals} if vals else None


def add_resolution_location_accuracy_filter(
    filters: Optional[dict], resolution: RC
) -> Optional[dict]:
    la = get_resolution_location_accuracy_filter(resolution)
    if la is None:
        return filters
    elif filters is None:
        return la
    else:
        res = copy.copy(filters)
        res.update(la)
        return res
