
# -*- coding: utf-8 -*-
# pylint: disable=no-member

from http import client as http_client


from anyway.models import (
    Comment,
)


import json
import logging

from flask import request, Response, abort


from anyway.app_and_db import db
from anyway.backend_constants import (
    BE_CONST,

)

from anyway.request_params import get_location_from_request_values

def get_comments():
    logging.debug("getting comments by resolution")

    params = get_location_from_request_values(request.values)
    comments = get_comments_by_resolution(params)
    
    if not comments:
        log_bad_request(request)
        return abort(http_client.NOT_FOUND)

    json_data = json.dumps(comments, default=str)
    
    return Response(json_data, mimetype="application/json")

def get_comments_by_resolution(params):
    location = params["data"]
    resolution = location["resolution"]
    
    if resolution == BE_CONST.ResolutionCategories.SUBURBAN_ROAD:
        return (
            db.session.query(Comment)
            .filter(
                Comment.road_segment_id
                == int(location["road_segment_id"])
            ))
    elif resolution == BE_CONST.ResolutionCategories.STREET:
        return (
            db.session.query(Comment)
            .filter(Comment.yishuv_symbol == location["yishuv_symbol"])
            .filter(Comment.street == location["street1"])
        )
    else:
        msg = f"Cache unsupported resolution: {resolution}, params:{params}"
        logging.error(msg)
        raise ValueError(msg)


def log_bad_request(request):
    try:
        logging.debug(
            "Bad {0} Request over {1}. Values: {2} {3}".format(
                request.method, request.url, request.form, request.args
            )
        )
    except AttributeError:
        logging.debug("Bad request:{0}".format(str(request)))


