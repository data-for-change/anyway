import json
import logging

from flask import Response, request, make_response
from sqlalchemy import and_

from anyway.base import user_optional, db
from anyway.constants import CONST
from anyway.parsers.cbs import global_cbs_dictionary as cbs_dictionary
from anyway.helpers import get_kwargs, generate_csv, generate_json, get_involved_dict, get_vehicle_dict
from anyway.models import AccidentMarker, DiscussionMarker, Involved, Vehicle


@user_optional
def markers():
    logging.debug('getting markers')
    kwargs = get_kwargs()
    logging.debug('querying markers in bounding box: %s' % kwargs)
    is_thin = (kwargs['zoom'] < CONST.MINIMAL_ZOOM)
    result = AccidentMarker.bounding_box_query(is_thin, yield_per=50, involved_and_vehicles=False, **kwargs)
    accident_markers = result.accident_markers
    rsa_markers = result.rsa_markers

    discussion_args = ('ne_lat', 'ne_lng', 'sw_lat', 'sw_lng', 'show_discussions')
    discussions = DiscussionMarker.bounding_box_query(**{arg: kwargs[arg] for arg in discussion_args})

    if request.values.get('format') == 'csv':
        date_format = '%Y-%m-%d'
        return Response(generate_csv(accident_markers), headers={
            "Content-Type": "text/csv",
            "Content-Disposition": 'attachment; '
                                   'filename="Anyway-accidents-from-{0}-to-{1}.csv"'
                        .format(kwargs["start_date"].strftime(date_format), kwargs["end_date"].strftime(date_format))
        })

    else:  # defaults to json
        return generate_json(accident_markers, rsa_markers, discussions, is_thin, total_records=result.total_records)


def marker(marker_id):
    involved = db.session.query(Involved).filter(Involved.accident_id == marker_id)

    vehicles = db.session.query(Vehicle).filter(Vehicle.accident_id == marker_id)

    list_to_return = list()
    for inv in involved:
        obj = inv.serialize()
        obj["age_group"] = cbs_dictionary.get((92, obj["age_group"]))
        obj["population_type"] = cbs_dictionary.get((66, obj["population_type"]))
        obj["home_region"] = cbs_dictionary.get((77, obj["home_region"]))
        obj["home_district"] = cbs_dictionary.get((79, obj["home_district"]))
        obj["home_natural_area"] = cbs_dictionary.get((80, obj["home_natural_area"]))
        obj["home_municipal_status"] = cbs_dictionary.get((78, obj["home_municipal_status"]))
        obj["home_yishuv_shape"] = cbs_dictionary.get((81, obj["home_yishuv_shape"]))
        list_to_return.append(obj)

    for veh in vehicles:
        obj = veh.serialize()
        obj["engine_volume"] = cbs_dictionary.get((111, obj["engine_volume"]))
        obj["total_weight"] = cbs_dictionary.get((112, obj["total_weight"]))
        obj["driving_directions"] = cbs_dictionary.get((28, obj["driving_directions"]))
        list_to_return.append(obj)
    return make_response(json.dumps(list_to_return, ensure_ascii=False))


def marker_all():
    marker_id = request.args.get('marker_id', None)
    provider_code = request.args.get('provider_code', None)
    accident_year = request.args.get('accident_year', None)

    involved = db.session.query(Involved).filter(and_(Involved.accident_id == marker_id,
                                                      Involved.provider_code == provider_code,
                                                      Involved.accident_year == accident_year))

    vehicles = db.session.query(Vehicle).filter(and_(Vehicle.accident_id == marker_id,
                                                     Vehicle.provider_code == provider_code,
                                                     Vehicle.accident_year == accident_year))

    list_to_return = list()
    for inv in involved:
        obj = inv.serialize()
        new_inv = get_involved_dict(provider_code, accident_year)
        obj["age_group"] = new_inv["age_group"]
        obj["population_type"] = new_inv["population_type"]
        obj["home_region"] = new_inv["home_region"]
        obj["home_district"] = new_inv["home_district"]
        obj["home_natural_area"] = new_inv["home_natural_area"]
        obj["home_municipal_status"] = new_inv["home_municipal_status"]
        obj["home_yishuv_shape"] = new_inv["home_yishuv_shape"]

        list_to_return.append(obj)

    for veh in vehicles:
        obj = veh.serialize()
        new_veh = get_vehicle_dict(provider_code, accident_year)
        obj["engine_volume"] = new_veh["engine_volume"]
        obj["total_weight"] = new_veh["total_weight"]
        obj["driving_directions"] = new_veh["driving_directions"]

        list_to_return.append(obj)
    return make_response(json.dumps(list_to_return, ensure_ascii=False))
