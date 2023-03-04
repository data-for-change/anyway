# pylint: disable=no-name-in-module
# pylint: disable=no-self-argument

import datetime
import json
import logging
import pandas as pd

from typing import List, Optional
from http import HTTPStatus
from collections import OrderedDict

from flask import request, Response, make_response, jsonify
from sqlalchemy import and_, not_, or_
from sqlalchemy.orm.query import Query


from anyway.app_and_db import db
from anyway.backend_constants import (
    BE_CONST,
    NewsflashLocationQualification,
    QUALIFICATION_TO_ENUM_VALUE,
)
from anyway.models import NewsFlash, LocationVerificationHistory
from anyway.infographics_utils import is_news_flash_resolution_supported
from anyway.request_params import get_request_params_from_request_values
from pydantic import BaseModel, ValidationError, validator

from anyway.views.user_system.api import roles_accepted, return_json_error
from anyway.views.user_system.user_functions import get_current_user
from anyway.error_code_and_strings import Errors as Es
from anyway.parsers import fields_to_resolution, resolution_dict
from anyway.models import AccidentMarkerView, InvolvedView
from anyway.widgets.widget_utils import get_accidents_stats
from io import BytesIO

DEFAULT_OFFSET_REQ_PARAMETER = 0
DEFAULT_LIMIT_REQ_PARAMETER = 100
DEFAULT_NUMBER_OF_YEARS_AGO = 5

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
            not_(and_(NewsFlash.lat == None, NewsFlash.lon == None)),
        )
    ).order_by(NewsFlash.date.desc())

    query = query.offset(offset)
    query = query.limit(limit)

    return query

def filter_by_road_number(query: Query, value: float, **kwargs) -> Query:
    return query.filter(NewsFlash.road1 == value)

def filter_by_source(query: Query, value: Optional[List[BE_CONST.Source]], **kwargs) -> Query:
    if value is None:
        return query
    sources = set([source.value for source in value])
    critical = BE_CONST.Source.CRITICAL.value
    if critical in sources:
        query = query.filter(NewsFlash.critical==True)
        sources.remove(critical)
        if len(sources) == 0:
            return query
    return query.filter(NewsFlash.source.in_(list(sources)))

def filter_by_dates(query: Query, value: Optional[datetime.datetime], **kwargs) -> Query:
    start_date, end_date = value, kwargs.get('end_date')
    if start_date:
        if end_date:
            query = query.filter(start_date <= NewsFlash.date <= end_date)
        else:
            query = query.filter(start_date <= NewsFlash.date)
    elif end_date:
        query = query.filter(NewsFlash.date <= end_date)
    return query

def filter_by_resolutions(query, value: List[str], **kwargs):
    ands = []
    if "suburban_road" in value:
        ands.append(
            and_(
                NewsFlash.resolution == BE_CONST.ResolutionCategories.SUBURBAN_ROAD.value,
                NewsFlash.road_segment_name != None,
            )
        )
    if "street" in value:
        ands.append(
            and_(
                NewsFlash.resolution == BE_CONST.ResolutionCategories.STREET.value,
                NewsFlash.street1_hebrew != None,
            )
        )
    if len(ands) > 1:
        return query.filter(or_(*ands))
    return query.filter(ands.pop())

param_to_query_filter = {
    "road_number": filter_by_road_number,
    "source": filter_by_source,
    "start_date": filter_by_dates,
    "resolution": filter_by_resolutions
}

param_to_filter_kwargs = {
    "start_date": lambda valid_params: {
        "end_date": valid_params.get("end_date")
    }
}

def gen_news_flash_query_v2(session, valid_params: dict):
    query = session.query(NewsFlash)
    for param, value in valid_params.items():
        query_filter = param_to_query_filter.get(param)
        if query_filter is not None:
            kwargs = {}
            kwargs_retriever = param_to_filter_kwargs.get(param)
            if kwargs_retriever is not None:
                kwargs = kwargs_retriever(valid_params)
            query = query_filter(query, value, **kwargs)
    query = query.filter(
        and_(
            NewsFlash.accident == True,
            not_(and_(NewsFlash.lat == 0, NewsFlash.lon == 0)),
            not_(and_(NewsFlash.lat == None, NewsFlash.lon == None)),
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


# Params that can take more than 1 value are kept as lists regardless of number of values supplied
# in order to simplify dependent code.
# Single valued params are converted to their value.
def normalize_query_param(key, value: list):
    multi_value_params = ["source", "resolution"]
    return value if key in multi_value_params else value.pop()


def normalize_query(params: dict):
    params_non_flat = params.to_dict(flat=False)
    return {k: normalize_query_param(k, v) for k, v in params_non_flat.items()}


def update_location_verification_history(
    user_id: int,
    news_flash_id: int,
    prev_location: str,
    prev_qualification: int,
    new_location: str,
    new_qualification: int,
):
    new_location_qualifiction_history = LocationVerificationHistory(
        user_id=user_id,
        news_flash_id=news_flash_id,
        location_verification_before_change=prev_qualification,
        location_before_change=prev_location,
        location_verification_after_change=new_qualification,
        location_after_change=new_location,
    )
    db.session.add(new_location_qualifiction_history)
    db.session.commit()


def extracted_location_and_qualification(news_flash_obj: NewsFlash):
    news_flash_resolution = {}
    resolution = resolution_dict[news_flash_obj.resolution]
    for field in resolution:
        value = getattr(news_flash_obj, field)
        news_flash_resolution[field] = value
    location = json.dumps(news_flash_resolution)
    return location, news_flash_obj.newsflash_location_qualification


@roles_accepted(
    BE_CONST.Roles2Names.Authenticated.value,
    BE_CONST.Roles2Names.Location_verification.value,
    need_all_permission=True,
)
def update_news_flash_qualifying(id):
    current_user = get_current_user()
    manual_update = False
    use_road_segment = True

    newsflash_location_qualification = request.values.get("newsflash_location_qualification")
    road_segment_name = request.values.get("road_segment_name")
    yishuv_name = request.values.get("yishuv_name")
    street1_hebrew = request.values.get("street1_hebrew")
    newsflash_location_qualification = QUALIFICATION_TO_ENUM_VALUE[newsflash_location_qualification]
    if newsflash_location_qualification == NewsflashLocationQualification.MANUAL.value:
        manual_update = True
        if road_segment_name is None:
            if (yishuv_name is None) or (street1_hebrew is None):
                logging.error("manual update must include location detalis.")
                return return_json_error(Es.BR_FIELD_MISSING)
            else:
                use_road_segment = False
    else:
        if road_segment_name is not None or street1_hebrew is not None or yishuv_name is not None:
            logging.error("only manual update should contain location details.")
            return return_json_error(Es.BR_BAD_FIELD)
    news_flash_obj = db.session.query(NewsFlash).filter(NewsFlash.id == id).first()
    old_location, old_location_qualifiction = extracted_location_and_qualification(news_flash_obj)
    if news_flash_obj is not None:
        if manual_update:
            if use_road_segment:
                news_flash_obj.road_segment_name = road_segment_name
                news_flash_obj.resolution = fields_to_resolution.get("road_segment_name")
            else:
                news_flash_obj.yishuv_name = yishuv_name
                news_flash_obj.street1_hebrew = street1_hebrew
                news_flash_obj.resolution = fields_to_resolution.get(
                    ("yishuv_name", "street1_hebrew")
                )
        else:
            if (news_flash_obj.road_segment_name is None) and (
                (news_flash_obj.yishuv_name is None) or (news_flash_obj.street1_hebrew is None)
            ):
                logging.error("try to set qualification on empty location.")
                return return_json_error(Es.BR_BAD_FIELD)

        news_flash_obj.newsflash_location_qualification = newsflash_location_qualification
        news_flash_obj.location_qualifying_user = current_user.id
        db.session.commit()
        new_location, new_location_qualifiction = extracted_location_and_qualification(
            news_flash_obj
        )
        update_location_verification_history(
            user_id=current_user.id,
            news_flash_id=id,
            prev_location=old_location,
            prev_qualification=old_location_qualifiction,
            new_location=new_location,
            new_qualification=new_location_qualifiction,
        )
        return Response(status=HTTPStatus.OK)


def get_downloaded_data(format, years_ago):
    request_params = get_request_params_from_request_values(request.values)
    end_time = datetime.datetime.now()
    start_time = end_time - datetime.timedelta(days=years_ago*365)
    columns = OrderedDict()

    columns[AccidentMarkerView.id] = 'מס תאונה'
    columns[AccidentMarkerView.provider_code_hebrew] = 'סוג תיק'
    columns[AccidentMarkerView.accident_type_hebrew] = 'סוג תאונה'
    columns[AccidentMarkerView.accident_severity_hebrew] = 'חומרת תאונה'
    columns[AccidentMarkerView.speed_limit_hebrew] = 'מהירות מותרת'
    columns[AccidentMarkerView.location_accuracy_hebrew] = 'איכות עיגון'

    columns[AccidentMarkerView.accident_year] = 'שנה'
    columns[AccidentMarkerView.accident_month] = 'חודש'
    columns[AccidentMarkerView.accident_day] = 'יום'
    columns[AccidentMarkerView.accident_timestamp] = 'חתימת זמן'
    columns[AccidentMarkerView.day_in_week_hebrew] = 'יום בשבוע'
    columns[AccidentMarkerView.day_type_hebrew] = 'סוג יום'

    columns[AccidentMarkerView.road1] = 'מספר דרך- מקום אירוע התאונה'
    columns[AccidentMarkerView.road2] = 'מספר דרך 2'
    columns[AccidentMarkerView.km] = 'מספר הק"מ- מקום אירוע התאונה'
    columns[AccidentMarkerView.region_hebrew] = 'מחוז-מקום התאונה'
    columns[AccidentMarkerView.yishuv_name] = 'שם היישוב בו אירעה התאונה'
    columns[AccidentMarkerView.street1_hebrew] = 'רחוב- מקום אירוע התאונה'
    columns[AccidentMarkerView.street2_hebrew] = 'רחוב 2'
    columns[AccidentMarkerView.house_number] = 'מספר בית- מקום אירוע התאונה'

    columns[AccidentMarkerView.road_type_hebrew] = 'סוג דרך'
    columns[AccidentMarkerView.non_urban_intersection_hebrew] = 'צומת בינעירוני'
    columns[AccidentMarkerView.road_shape_hebrew] = 'צורת הדרך'
    columns[AccidentMarkerView.road_surface_hebrew] = 'מצב פני הכביש'
    columns[AccidentMarkerView.road_intactness_hebrew] = 'תקינות הכביש'
    columns[AccidentMarkerView.road_width_hebrew] = 'רוחב הכביש'
    columns[AccidentMarkerView.one_lane_hebrew] = 'דרך חד מסלולית'
    columns[AccidentMarkerView.multi_lane_hebrew] = 'דרך רב מסלולית'

    columns[AccidentMarkerView.road_sign_hebrew] = 'סימון/תמרור'
    columns[AccidentMarkerView.road_light_hebrew] = 'תאורה'
    columns[AccidentMarkerView.road_control_hebrew] = 'בקרה בצומת'
    columns[AccidentMarkerView.traffic_light_hebrew] = 'מרומזר/לא מרומזר'
    columns[AccidentMarkerView.weather_hebrew] = 'מזג אוויר'
    columns[AccidentMarkerView.day_night_hebrew] = 'יום/לילה'
    columns[AccidentMarkerView.road_object_hebrew] = 'עצם-סוג'

    columns[AccidentMarkerView.didnt_cross_hebrew] = 'חצייה-לא חצה'
    columns[AccidentMarkerView.cross_mode_hebrew] = 'חצייה-אופן'
    columns[AccidentMarkerView.cross_location_hebrew] = 'חצייה-מקום'
    columns[AccidentMarkerView.cross_direction_hebrew] = 'חצייה-כיוון'

    columns[AccidentMarkerView.longitude] = 'קו אורך'
    columns[AccidentMarkerView.latitude] = 'קו רוחב'
    columns[AccidentMarkerView.x] = 'X קואורדינטה'
    columns[AccidentMarkerView.y] = 'Y קואורדינטה'


    related_accidents = get_accidents_stats(
            table_obj=AccidentMarkerView,
            columns=columns.keys(),
            filters=request_params.location_info,
            start_time=start_time,
            end_time=end_time
        )
    accident_ids = list(related_accidents['id'].values())
    accident_severities = get_accidents_stats(
            table_obj=InvolvedView,
            group_by=("accident_id", "injury_severity_hebrew"),
            count="injury_severity_hebrew",
            filters={"accident_id": accident_ids}
        )

    severities_hebrew = set()
    for i, accident_id in enumerate(accident_ids):
        for severity_hebrew, severity_count in accident_severities[accident_id].items():
            if severity_hebrew is None:
                continue
            severities_hebrew.add(severity_hebrew)
            if severity_hebrew not in related_accidents:
                related_accidents[severity_hebrew] = {}
            related_accidents[severity_hebrew][i] = severity_count

    json_data = json.dumps(related_accidents, default=str)
    buffer = BytesIO()
    df = pd.read_json(json_data)
    df.rename(columns={key.name.replace('_hebrew', ''): value for key, value in columns.items()}, inplace=True)

    index_to_insert_severities = list(columns.values()).index('מהירות מותרת')
    output_column_names = list(columns.values())[:index_to_insert_severities] + list(severities_hebrew) + list(columns.values())[index_to_insert_severities:]
    df = df[output_column_names]
    df.rename(columns={'פצוע קל': 'פצוע/ה קל', 'פצוע בינוני': 'פצוע/ה בינוני', 'פצוע קשה': 'פצוע/ה קשה', 'הרוג': 'הרוג/ה'}, inplace=True)

    if format == 'csv':
        df.to_csv(buffer, encoding="utf-8")
        mimetype ='text/csv'
        file_type = 'csv'
    elif format == 'xlsx':
        df.to_excel(buffer, encoding="utf-8")
        mimetype='application/vnd.ms-excel'
        file_type = 'xlsx'
    else:
        raise Exception(f'File format not supported for downloading : {format}')

    headers = { 'Content-Disposition': f'attachment; filename=anyway_download_{datetime.datetime.now().strftime("%d_%m_%Y_%H_%M_%S")}.{file_type}' }
    return Response(buffer.getvalue(), mimetype=mimetype, headers=headers)
