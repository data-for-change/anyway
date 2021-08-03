import datetime
import json
import logging
from typing import List, Literal

from flask import request, Response
from sqlalchemy import and_, not_

from anyway.app_and_db import db
from anyway.backend_constants import BE_CONST
from anyway.models import NewsFlash
from anyway.infographics_utils import is_news_flash_resolution_supported

from pydantic import BaseModel, ValidationError, validator

DEFAULT_OFFSET_REQ_PARAMETER = 0
DEFAULT_LIMIT_REQ_PARAMETER = 100

class QueryParams(BaseModel):
    road_number: int
    offset: int
    limit: int
    interurban_only: bool
    road_segment_only: bool
    source: Literal['ynet', 'walla', 'twitter']
    start_date: datetime.datetime
    end_date: datetime.datetime

    @validator('end_date')
    def check_missing_date(cls, end_date, start_date):
        if end_date ^ start_date:
            raise ValidationError('Missing start or end date')
        return end_date

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
