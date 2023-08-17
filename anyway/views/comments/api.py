
# -*- coding: utf-8 -*-
# pylint: disable=no-member

from http import client as http_client
from anyway.models import Comment
import json
import logging
from anyway.views.user_system.user_functions import get_current_user
from flask import request, Response, abort
from anyway.app_and_db import db
from anyway.backend_constants import BE_CONST

from anyway.request_params import get_location_from_request_values

def update_comment():
    current_user = get_current_user()
    params = get_location_from_request_values(request.values)
    location = params["data"]
    resolution = location["resolution"]
    parent = request.get("parent")
    road_segment_id = None
    city = None
    street = None
    if resolution == BE_CONST.ResolutionCategories.SUBURBAN_ROAD:
        road_segment_id = int(location["road_segment_id"])
    elif resolution == BE_CONST.ResolutionCategories.STREET:
        city = location["yishuv_name"]
        street = location["street"]
    else:
        msg = f"Cache unsupported resolution: {resolution}, params:{params}"
        logging.error(msg)
        raise ValueError(msg)

    comment = Comment(author=current_user.id,
                      parent=parent,
                      street=street,
                      city=city,
                      road_segment_id=road_segment_id,
                      resolution=resolution)
    db.session.add(comment)
    db.session.commit()

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
            .filter(Comment.city == location["yishuv_name"])
            .filter(Comment.street == location["street"])
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


