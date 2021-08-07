import datetime
import json
import logging
from typing import List, Literal, Optional

from flask import request, Response, make_response, jsonify
from sqlalchemy import and_, not_

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
    interurban_only: Optional[bool]
    road_segment_only: Optional[bool]
    source: Optional[str]
    # Must set default value in order to be accessed from "check_missing_date" validator when no value provided
    # from the request
    start_date: Optional[datetime.datetime] = None
    end_date: Optional[datetime.datetime] = None

    @validator("end_date", always=True)
    def check_missing_date(cls, v, values):
        if bool(v) != bool(values["start_date"]):
            raise ValueError("Must provide both start and end date")
        return v

    @validator("source")
    def check_source_exist(cls, v):
        valid_sources = [
            str(source_name[0])
            for source_name in db.session.query(NewsFlash.source).distinct().all()
        ]
        if not v in valid_sources:
            raise ValueError(f"Source must be one of: {valid_sources}")
        return v


def news_flash():
    news_flash_id = request.values.get("id")
    requested_query_params = request.args

    try:
        validated_query_params = NewsFlashQuery(**requested_query_params).dict(exclude_none=True)
    except ValidationError as e:
        return make_response(jsonify(e.errors()[0]["msg"]), 404)

    query = db.session.query(NewsFlash)
    if "id" in validated_query_params:
        return get_news_flash_by_id(validated_query_params["id"], query)

    query = gen_news_flash_query_new(query, validated_query_params)
    news_flashes = query.all()

    news_flashes_jsons = [n.serialize() for n in news_flashes]
    for news_flash in news_flashes_jsons:
        set_display_source(news_flash, news_flash_id)
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
        set_display_source(news_flash, news_flash_id)
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
            not_(and_(NewsFlash.lat == None, NewsFlash.lon == None)),
        )
    ).order_by(NewsFlash.date.desc())

    query = query.offset(offset)
    query = query.limit(limit)

    return query

def gen_news_flash_query_new(query, valid_params: dict):
    filters = {
        "source": filter_news_flash_by_source,
        "start_date": filter_news_flash_by_start_date,
        "end_date": filter_news_flash_by_end_date,
        "interurban_only": filter_news_flash_by_interurban_only,
        "road_segment_only": filter_news_flash_by_road_segment,
        "road_number": filter_news_flash_by_road_number,
    }

    for param in valid_params:
        if param is not "offset" and param is not "limit":
            query = filters[param](query, valid_params[param])

    query = query.filter(
        and_(
            NewsFlash.accident == True,
            not_(and_(NewsFlash.lat == 0, NewsFlash.lon == 0)),
            not_(and_(NewsFlash.lat == None, NewsFlash.lon == None)),
        )
    ).order_by(NewsFlash.date.desc())

    query = filter_news_flash_by_offset(query, valid_params["offset"])
    query = filter_news_flash_by_limit(query, valid_params["limit"])
    return query


def set_display_source(news_flash, news_flash_id):
    news_flash["display_source"] = BE_CONST.SOURCE_MAPPING.get(
        news_flash["source"], BE_CONST.UNKNOWN
    )
    if news_flash["display_source"] == BE_CONST.UNKNOWN:
        logging.warning(f"Unknown source of news-flash with id {str(news_flash_id)}")


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
    return set([x.value for x in BE_CONST.SUPPORTED_RESOLUTIONS])


def get_news_flash_by_id(id: int, query):
    news_flash_with_id = query.filter(NewsFlash.id == id).first()
    if news_flash_with_id is None:
        return Response(status=404)
    if not is_news_flash_resolution_supported(news_flash_with_id):
        return Response("News flash location not supported", 406)
    return Response(
    json.dumps(news_flash_with_id.serialize(), default=str), mimetype="application/json")


def filter_news_flash_by_interurban_only(query, interurban_only: bool):
    return query.filter(NewsFlash.resolution.in_(["כביש בינעירוני"]))


def filter_news_flash_by_road_number(query, road_number):
    return query.filter(NewsFlash.road1 == road_number)


def filter_news_flash_by_road_segment(query, road_segment_required: bool):
    return query.filter(not_(NewsFlash.road_segment_name == None))


def filter_news_flash_by_start_date(query, start_date: datetime.datetime):
    return query.filter(NewsFlash.date >= start_date)


def filter_news_flash_by_end_date(query, end_date: datetime.datetime):
    return query.filter(NewsFlash.date <= end_date)


def filter_news_flash_by_supported_resolutions(query, supported_resolutions):
    return query.filter(NewsFlash.resolution.in_(supported_resolutions))


def filter_news_flash_by_source(query, source):
    return query.filter(NewsFlash.source == source)


def filter_news_flash_by_offset(query, offset):
    return query.offset(offset)


def filter_news_flash_by_limit(query, limit):
    return query.limit(limit)
