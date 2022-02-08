# pylint: disable=no-name-in-module
# pylint: disable=no-self-argument

import datetime
import json
import logging

from typing import List, Optional

from flask import request, Response, make_response, jsonify
from sqlalchemy import and_, not_, or_


from anyway.app_and_db import db
from anyway.backend_constants import BE_CONST
from anyway.models import NewsFlash
from anyway.infographics_utils import is_news_flash_resolution_supported

from pydantic import BaseModel, ValidationError, validator

DEFAULT_OFFSET_REQ_PARAMETER = 0
DEFAULT_LIMIT_REQ_PARAMETER = 100


class NewsFlashQuery(BaseModel):

    id: Optional[int]
    road_number: Optional[int]
    offset: Optional[int] = DEFAULT_OFFSET_REQ_PARAMETER
    limit: Optional[int] = DEFAULT_LIMIT_REQ_PARAMETER
    resolution: Optional[List[str]]
    source: Optional[List[BE_CONST.Source]]
    # Must set default value in order to allow access from "check_missing_date" validator when no value provided
    # from the request
    start_date: Optional[datetime.datetime] = None
    end_date: Optional[datetime.datetime] = None

    @validator("end_date", always=True)
    def check_missing_date(cls, v, values):
        if bool(v) != bool(values["start_date"]):
            raise ValueError("Must provide both start and end date")
        return v

    @validator("resolution")
    def check_supported_resolutions(cls, v):
        supported_resolutions = get_supported_resolutions()
        requested_resolutions = set([resolution.lower() for resolution in v])
        if not requested_resolutions <= supported_resolutions:
            raise ValueError(f"Resolution must be one of: {supported_resolutions}")
        return requested_resolutions


def news_flash():
    news_flash_id = request.values.get("id")

    if news_flash_id is not None:
        query = db.session.query(NewsFlash)
        news_flash_obj = query.filter(NewsFlash.id == news_flash_id).first()
        if news_flash_obj is not None:
            if is_news_flash_resolution_supported(news_flash_obj):
                return Response(
                    json.dumps(news_flash_obj.serialize(), default=str), mimetype="application/json"
                )
            else:
                return Response("News flash location not supported", 406)
        return Response(status=404)

    query = gen_news_flash_query(
        db.session,
        source=request.values.get("source"),
        start_date=request.values.get("start_date"),
        end_date=request.values.get("end_date"),
        interurban_only=request.values.get("interurban_only"),
        road_number=request.values.get("road_number"),
        road_segment=request.values.get("road_segment_only"),
        offset=request.values.get("offset", DEFAULT_OFFSET_REQ_PARAMETER),
        limit=request.values.get("limit", DEFAULT_LIMIT_REQ_PARAMETER),
    )
    news_flashes = query.all()

    news_flashes_jsons = [n.serialize() for n in news_flashes]
    for news_flash in news_flashes_jsons:
        set_display_source(news_flash)
    return Response(json.dumps(news_flashes_jsons, default=str), mimetype="application/json")


def news_flash_v2():
    requested_query_params = normalize_query(request.args)
    try:
        validated_query_params = NewsFlashQuery(**requested_query_params).dict(exclude_none=True)
    except ValidationError as e:
        return make_response(jsonify(e.errors()[0]["msg"]), 404)

    if "id" in validated_query_params:
        return get_news_flash_by_id(validated_query_params["id"])

    query = gen_news_flash_query_v2(db.session, validated_query_params)
    news_flashes = query.all()

    news_flashes_jsons = [n.serialize() for n in news_flashes]
    for news_flash in news_flashes_jsons:
        set_display_source(news_flash)
    return Response(json.dumps(news_flashes_jsons, default=str), mimetype="application/json")


def news_flash_new(args: dict) -> List[dict]:
    news_flash_id = args["id"]

    if news_flash_id is not None:
        return single_news_flash(news_flash_id)

    query = gen_news_flash_query(
        db.session,
        source=args.get("source"),
        start_date=args.get("start_date"),
        end_date=args.get("end_date"),
        interurban_only=args.get("interurban_only"),
        road_number=args.get("road_number"),
        road_segment=args.get("road_segment_only"),
        offset=args.get("offset"),
        limit=args.get("limit"),
    )
    news_flashes = query.all()

    news_flashes_jsons = [n.serialize() for n in news_flashes]
    for news_flash in news_flashes_jsons:
        set_display_source(news_flash)
    return news_flashes_jsons


def gen_news_flash_query(
    session,
    source=None,
    start_date=None,
    end_date=None,
    interurban_only=None,
    road_number=None,
    road_segment=None,
    offset=None,
    limit=None,
):
    query = session.query(NewsFlash)
    # get all possible sources
    sources = [
        str(source_name[0]) for source_name in db.session.query(NewsFlash.source).distinct().all()
    ]
    if source:
        if source not in sources:
            return Response(
                '{"message": "Requested source does not exist"}',
                status=404,
                mimetype="application/json",
            )
        else:
            query = query.filter(NewsFlash.source == source)

    if start_date and end_date:
        query = filter_by_timeframe(end_date, query, start_date)
    # when only one of the dates is sent
    elif start_date or end_date:
        return Response(
            '{"message": "Must send both start_date and end_date"}',
            status=404,
            mimetype="application/json",
        )
    supported_resolutions = set([x.value for x in BE_CONST.SUPPORTED_RESOLUTIONS])
    query = query.filter(NewsFlash.resolution.in_(supported_resolutions))
    if interurban_only == "true" or interurban_only == "True":
        query = query.filter(NewsFlash.resolution.in_(["כביש בינעירוני"]))
    if road_number:
        query = query.filter(NewsFlash.road1 == road_number)
    if road_segment == "true":
        query = query.filter(not_(NewsFlash.road_segment_name == None))
    query = query.filter(
        and_(
            NewsFlash.accident == True,
            not_(and_(NewsFlash.lat == 0, NewsFlash.lon == 0)),
            not_(and_(NewsFlash.lat is None, NewsFlash.lon is None)),
        )
    ).order_by(NewsFlash.date.desc())

    query = query.offset(offset)
    query = query.limit(limit)

    return query


def gen_news_flash_query_v2(session, valid_params: dict):
    query = session.query(NewsFlash)
    for param, value in valid_params.items():
        if param == "road_number":
            query = query.filter(NewsFlash.road1 == value)
        if param == "source":
            sources = [source.value for source in value]
            query = query.filter(NewsFlash.source.in_(sources))
        if param == "start_date":
            query = query.filter(value <= NewsFlash.date <= valid_params["end_date"])
        if param == "resolution":
            query = filter_by_resolutions(query, value)
    query = query.filter(
        and_(
            NewsFlash.accident == True,
            not_(and_(NewsFlash.lat == 0, NewsFlash.lon == 0)),
            not_(and_(NewsFlash.lat is None, NewsFlash.lon is None)),
        )
    ).order_by(NewsFlash.date.desc())
    query = query.offset(valid_params["offset"])
    query = query.limit(valid_params["limit"])
    return query


def set_display_source(news_flash):
    news_flash["display_source"] = BE_CONST.SOURCE_MAPPING.get(
        news_flash["source"], BE_CONST.UNKNOWN
    )
    if news_flash["display_source"] == BE_CONST.UNKNOWN:
        logging.warning(f"Unknown source of news-flash with id")


def filter_by_timeframe(end_date, news_flash_obj, start_date):
    s = datetime.datetime.fromtimestamp(int(start_date))
    e = datetime.datetime.fromtimestamp(int(end_date))
    news_flash_obj = news_flash_obj.filter(and_(NewsFlash.date <= e, NewsFlash.date >= s))
    return news_flash_obj


def single_news_flash(news_flash_id: int):
    news_flash_obj = db.session.query(NewsFlash).filter(NewsFlash.id == news_flash_id).first()
    if news_flash_obj is not None:
        return Response(
            json.dumps(news_flash_obj.serialize(), default=str), mimetype="application/json"
        )
    return Response(status=404)


def get_supported_resolutions() -> set:
    return set([x.name.lower() for x in BE_CONST.SUPPORTED_RESOLUTIONS])


def get_news_flash_by_id(id: int):
    query = db.session.query(NewsFlash)
    news_flash_with_id = query.filter(NewsFlash.id == id).first()
    if news_flash_with_id is None:
        return Response(status=404)
    if not is_news_flash_resolution_supported(news_flash_with_id):
        return Response("News flash location not supported", 406)
    return Response(
        json.dumps(news_flash_with_id.serialize(), default=str), mimetype="application/json"
    )


def filter_by_resolutions(query, resolutions: List[str]):
    ands = []
    if "suburban_road" in resolutions:
        ands.append(
            and_(
                NewsFlash.resolution == BE_CONST.ResolutionCategories.SUBURBAN_ROAD.value,
                NewsFlash.road_segment_name is not None,
            )
        )
    if "street" in resolutions:
        ands.append(
            and_(
                NewsFlash.resolution == BE_CONST.ResolutionCategories.STREET.value,
                NewsFlash.street1_hebrew is not None,
            )
        )
    if len(ands) > 1:
        return query.filter(or_(*ands))
    return query.filter(ands.pop())


# Params that can take more than 1 value are kept as lists regardless of number of values supplied
# in order to simplify dependent code.
# Single valued params are converted to their value.
def normalize_query_param(key, value: list):
    multi_value_params = ["source", "resolution"]
    return value if key in multi_value_params else value.pop()


def normalize_query(params: dict):
    params_non_flat = params.to_dict(flat=False)
    return {k: normalize_query_param(k, v) for k, v in params_non_flat.items()}
