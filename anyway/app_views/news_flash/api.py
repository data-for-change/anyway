import json
import logging

from flask import request, Response
from sqlalchemy import and_, not_

from anyway.base import user_optional
from anyway.models import db, NewsFlash


@user_optional
def news_flash():
    logging.debug('getting news flash')
    news_flash_id = request.values.get('id')
    if news_flash_id is not None:
        news_flash_obj = db.session.query(NewsFlash).filter(NewsFlash.id == news_flash_id).first()
        if news_flash_obj is not None:
            return Response(json.dumps(news_flash_obj.serialize(), default=str), mimetype="application/json")
        return Response(status=404)

    # Todo - add start and end time for the news flashes
    news_flashes = db.session.query(NewsFlash).filter(
        and_(NewsFlash.accident == True, not_(and_(NewsFlash.lat == 0, NewsFlash.lon == 0)),
             not_(and_(NewsFlash.lat == None, NewsFlash.lon == None)))).with_entities(NewsFlash.id,
                                                                                      NewsFlash.lat,
                                                                                      NewsFlash.lon,
                                                                                      NewsFlash.title, NewsFlash.source,
                                                                                      NewsFlash.date).order_by(
        NewsFlash.date.desc()).all()
    news_flashes = [{"id": x.id, "lat": x.lat, "lon": x.lon, "title": x.title, "source": x.source, "date": x.date} for x
                    in news_flashes]
    return Response(json.dumps(news_flashes, default=str), mimetype="application/json")


@user_optional
def single_news_flash(news_flash_id):
    news_flash_obj = db.session.query(NewsFlash).filter(NewsFlash.id == news_flash_id).first()
    if news_flash_obj is not None:
        return Response(json.dumps(news_flash_obj.serialize(), default=str), mimetype="application/json")
    return Response(status=404)
