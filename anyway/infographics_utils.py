# -*- coding: utf-8 -*-
import logging
import datetime
import json
import pandas as pd
from collections import defaultdict
from sqlalchemy import func
from sqlalchemy import cast, Numeric
from sqlalchemy import desc
from flask import Response
from .constants import CONST
from .models import (NewsFlash, AccidentMarkerView, InvolvedMarkerView, RoadSegments)
from .parsers import resolution_dict
from .app_and_db import db

'''
    Widget structure:
    {
        'name': str,
        'rank': int (Integer),
        'data': {'items': list (Array) | dictionary (Object),
                 'text': list (Array) - optional,
                 'title': str (String) - optional,
                 'additional': dictionary (Object) - optional,
                 'meta': dictionary (Object) - can be empty
    }
'''
class Widget():
    def __init__(self, name, rank, items, text=None, title=None, additional=None, meta=None):
        self.name = name
        self.rank = rank
        self.items = items
        self.text = text
        self.title = title
        self.additional = additional
        self.meta = meta

    def serialize(self):
        output = {}
        output['name'] = self.name
        output['rank'] = self.rank
        output['data'] = {}
        output['data']['items'] = self.items
        if self.text:
            output['data']['text'] = self.text
        if self.title:
            output['data']['title'] = self.title
        if self.additional:
            output['data']['additional'] = self.additional
        if self.meta:
            output['data']['meta'] = self.meta
        return output


def extract_news_flash_location(news_flash_id):
    news_flash_obj = db.session.query(NewsFlash).filter(
        NewsFlash.id == news_flash_id).first()
    if not news_flash_obj:
        logging.warn('could not find news flash id {}'.format(news_flash_id))
        return None
    resolution = news_flash_obj.resolution if news_flash_obj.resolution else None
    if not news_flash_obj or not resolution or resolution not in resolution_dict:
        logging.warn(
            'could not find valid resolution for news flash id {}'.format(news_flash_id))
        return {'name': 'location', 'data': {'resolution': None}}
    data = {'resolution': resolution}
    for field in resolution_dict[resolution]:
        curr_field = getattr(news_flash_obj, field)
        if curr_field is not None:
            data[field] = curr_field
    gps = {}
    for field in ['lon', 'lat']:
        gps[field] = getattr(news_flash_obj, field)
    return {'name': 'location', 'data': data, 'gps': gps}


def get_query(table_obj, filters, start_time, end_time):
    query = db.session.query(table_obj)
    if start_time:
        query = query.filter(
            getattr(table_obj, 'accident_timestamp') >= start_time)
    if end_time:
        query = query.filter(
            getattr(table_obj, 'accident_timestamp') <= end_time)
    if filters:
        for field_name, value in filters.items():
            if isinstance(value, list):
                values = value
            else:
                values = [value]
            query = query.filter((getattr(table_obj, field_name)).in_(values))
    return query

def get_accident_count_by_accident_type(location_info, start_time, end_time):
    all_accident_type_count = get_accidents_stats(table_obj=AccidentMarkerView,
                                                  filters=location_info,
                                                  group_by='accident_type_hebrew',
                                                  count='accident_type_hebrew',
                                                  start_time=start_time,
                                                  end_time=end_time)
    merged_accident_type_count = [{'accident_type': 'התנגשות', 'count': 0}]
    for item in all_accident_type_count:
        if 'התנגשות' in item['accident_type']:
            merged_accident_type_count[0]['count'] += item['count']
        else:
            merged_accident_type_count.append('item')
    return merged_accident_type_count

def get_top_road_segments_accidents_per_km(resolution, location_info, start_time=None, end_time=None, limit=5):
    if resolution != 'כביש בינעירוני':  # relevent for non urban roads only
        return {}

    query = get_query(table_obj=AccidentMarkerView, filters=None,
                      start_time=start_time, end_time=end_time)

    query = query.with_entities(
        AccidentMarkerView.road_segment_name,
        func.count(AccidentMarkerView.road_segment_name).label(
            'total_accidents'),
        (RoadSegments.to_km - RoadSegments.from_km).label('segment_length'),
        cast((func.count(AccidentMarkerView.road_segment_name) / (RoadSegments.to_km - RoadSegments.from_km)),
             Numeric(10, 4)).label(
            'accidents_per_km')) \
        .filter(AccidentMarkerView.road1 == RoadSegments.road) \
        .filter(AccidentMarkerView.road_segment_number == RoadSegments.segment) \
        .filter(AccidentMarkerView.road1 == location_info['road1']) \
        .filter(AccidentMarkerView.road_segment_name is not None) \
        .group_by(AccidentMarkerView.road_segment_name, RoadSegments.from_km, RoadSegments.to_km) \
        .order_by(desc('accidents_per_km')) \
        .limit(limit)

    result = pd.read_sql_query(query.statement, query.session.bind)
    return result.to_dict(orient='records')  # pylint: disable=no-member


def get_accidents_stats(table_obj, filters=None, group_by=None, count=None, start_time=None, end_time=None):
    filters = filters or {}
    filters['provider_code'] = [
        CONST.CBS_ACCIDENT_TYPE_1_CODE, CONST.CBS_ACCIDENT_TYPE_3_CODE]
    # get stats
    query = get_query(table_obj, filters, start_time, end_time)
    if group_by:
        query = query.group_by(group_by)
        query = query.with_entities(group_by, func.count(count))
    df = pd.read_sql_query(query.statement, query.session.bind)
    df.rename(columns={'count_1': 'count'}, inplace=True)  # pylint: disable=no-member
    df.columns = [c.replace('_hebrew', '') for c in df.columns]
    return df.to_dict(orient='records') if group_by or count else df.to_dict()  # pylint: disable=no-member


def get_injured_filters(location_info):
    new_filters = {}
    for curr_filter, curr_values in location_info.items():
        if curr_filter in ['region_hebrew', 'district_hebrew', 'district_hebrew', 'yishuv_name']:
            new_filter_name = 'accident_' + curr_filter
            new_filters[new_filter_name] = curr_values
        else:
            new_filters[curr_filter] = curr_values
    new_filters['injury_severity'] = [1, 2, 3, 4, 5]
    return new_filters


def get_most_severe_accidents_with_entities(table_obj, filters, entities, start_time, end_time, limit=10):
    filters = filters or {}
    filters['provider_code'] = [
        CONST.CBS_ACCIDENT_TYPE_1_CODE, CONST.CBS_ACCIDENT_TYPE_3_CODE]
    query = get_query(table_obj, filters, start_time, end_time)
    query = query.with_entities(*entities)
    query = query.order_by(getattr(table_obj, "accident_severity"), getattr(
        table_obj, "accident_timestamp").desc())
    query = query.limit(limit)
    df = pd.read_sql_query(query.statement, query.session.bind)
    df.columns = [c.replace('_hebrew', '') for c in df.columns]
    return df.to_dict(orient='records')  # pylint: disable=no-member


def get_most_severe_accidents(table_obj, filters, start_time, end_time, limit=10):
    entities = 'longitude', 'latitude', 'accident_severity_hebrew', 'accident_timestamp', 'accident_type_hebrew'
    return get_most_severe_accidents_with_entities(table_obj, filters, entities, start_time, end_time, limit)


def get_accidents_heat_map(table_obj, filters, start_time, end_time):
    filters = filters or {}
    filters['provider_code'] = [
        CONST.CBS_ACCIDENT_TYPE_1_CODE, CONST.CBS_ACCIDENT_TYPE_3_CODE]
    query = get_query(table_obj, filters, start_time, end_time)
    query = query.with_entities('longitude', 'latitude')
    df = pd.read_sql_query(query.statement, query.session.bind)
    return df.to_dict(orient='records')  # pylint: disable=no-member


def filter_and_group_injured_count_per_age_group(data_of_ages):
    import re
    range_dict = {0: 14, 15: 24, 25: 64, 65: 200}
    return_dict_by_required_age_group = defaultdict(int)

    for age_range_and_count in data_of_ages:
        age_range = age_range_and_count['age_group']
        count = age_range_and_count['count']

        # Parse the db age range
        match_parsing = re.match("([0-9]{2})\\-([0-9]{2})", age_range)
        if match_parsing:
            regex_age_matches = match_parsing.groups()
            if len(regex_age_matches) != 2:
                return_dict_by_required_age_group["unknown"] += count
                continue
            min_age_raw, max_age_raw = regex_age_matches
        else:
            match_parsing = re.match("([0-9]{2})\\+", age_range)  # e.g  85+
            if match_parsing:
                # We assume that no body live beyond age 200
                min_age_raw, max_age_raw = match_parsing.group(1), 200
            else:
                return_dict_by_required_age_group["unknown"] += count
                continue

        # Find to what "bucket" to aggregate the data
        min_age = int(min_age_raw)
        max_age = int(max_age_raw)
        for item in range_dict.items():
            item_min_range, item_max_range = item
            if item_min_range <= min_age <= item_max_range and item_min_range <= max_age <= item_max_range:
                string_age_range = f'{item_min_range:02}-{item_max_range:02}'
                return_dict_by_required_age_group[string_age_range] += count
                break

    # Rename the last key
    return_dict_by_required_age_group["65+"] = return_dict_by_required_age_group["65-200"]
    del return_dict_by_required_age_group["65-200"]

    return return_dict_by_required_age_group


def get_most_severe_accidents_table_title(location_text):
    return 'תאונות חמורות ב' + location_text


def get_accident_count_by_severity(location_info, location_text, start_time, end_time):
    count_by_severity = get_accidents_stats(table_obj=AccidentMarkerView,
                                            filters=location_info,
                                            group_by='accident_severity_hebrew',
                                            count='accident_severity_hebrew',
                                            start_time=start_time,
                                            end_time=end_time)
    severity_dict = {'קטלנית': 1,
                     'קשה': 2,
                     'קלה': 3}
    items = {}
    text = []
    severity_texts = ['','','']
    total_accidents_count = 0
    start_year = start_time.year
    end_year = end_time.year
    for severity_and_count in count_by_severity:
        if severity_and_count['count'] > 0:
            accident_severity_hebrew = severity_and_count['accident_severity']
            severity_num = severity_dict[accident_severity_hebrew]
            severity_count_var = 'severity_{}_count'.format(severity_num)
            idx = severity_num-1
            severity_texts[idx] = ('{' + severity_count_var + '}' + \
                                                   ' בחומרה ' + accident_severity_hebrew)
            items[severity_count_var] = severity_and_count['count']
            total_accidents_count += severity_and_count['count']
    years_text = 'בין השנים {start_year}-{end_year},'
    text.append(years_text)
    items['start_year'] = start_year
    items['end_year'] = end_year
    location_and_total_text = 'ב' + location_text + ' התרחשו {total_accidents_count}' + ' תאונות.'
    text.append(location_and_total_text)
    items['total_accidents_count'] = total_accidents_count
    text += severity_texts
    return text, items


def get_most_severe_accidents_table(location_info, start_time, end_time):
    entities = 'id', 'provider_code', 'accident_timestamp', 'accident_type_hebrew', 'accident_year'
    accidents = get_most_severe_accidents_with_entities(
        table_obj=AccidentMarkerView,
        filters=location_info,
        entities=entities,
        start_time=start_time,
        end_time=end_time)
    logging.debug('accidents:{}'.format(accidents))
    # Add casualties
    for accident in accidents:
        accident['type'] = accident['accident_type']
        dt = accident['accident_timestamp'].to_pydatetime()
        accident['date'] = dt.strftime("%d/%m/%y")
        accident['hour'] = dt.strftime("%H:%M")
        num = get_casualties_count_in_accident(
            accident['id'], accident['provider_code'], 1, accident['accident_year'])
        accident['killed_count'] = num
        num = get_casualties_count_in_accident(
            accident['id'], accident['provider_code'], [2, 3], accident['accident_year'])
        accident['injured_count'] = num
        del accident['accident_timestamp'], accident['accident_type'], accident['id'], accident['provider_code']
    return accidents


# count of dead and severely injured
def get_casualties_count_in_accident(accident_id, provider_code, injury_severity, accident_year):
    filters = {'accident_id': accident_id,
               'provider_code': provider_code,
               'injury_severity': injury_severity,
               'accident_year': accident_year}
    casualties = get_accidents_stats(table_obj=InvolvedMarkerView, filters=filters,
                                     group_by='injury_severity', count='injury_severity')
    res = 0
    for ca in casualties:
        res += ca['count']
    return res


# generate text describing location or road segment of news flash
# to be used by most severe accidents additional info widget
def get_news_flash_location_text(news_flash_id):
    news_flash_item = db.session.query(NewsFlash).filter(
        NewsFlash.id == news_flash_id).first()
    logging.debug('news_flash_item:{}'.format(news_flash_item))
    nf = news_flash_item.serialize()
    logging.debug('news flash serialized:{}'.format(nf))
    logging.debug('news_flash_id:{}({})'.format(news_flash_id, type(nf)))
    resolution = nf['resolution'] if nf['resolution'] else ''
    yishuv_name = nf['yishuv_name'] if nf['yishuv_name'] else ''
    road1 = str(int(nf['road1'])) if nf['road1'] else ''
    road2 = str(int(nf['road2'])) if nf['road2'] else ''
    street1_hebrew = nf['street1_hebrew'] if nf['street1_hebrew'] else ''
    road_segment_name = nf['road_segment_name'] if nf['road_segment_name'] else ''
    if resolution == 'כביש בינעירוני' and road1 and road_segment_name:
        res = 'כביש ' + road1 + ' במקטע ' + road_segment_name
    elif resolution == 'עיר' and not yishuv_name:
        res = nf['location']
    elif resolution == 'עיר' and yishuv_name:
        res = nf['yishuv_name']
    elif resolution == 'צומת בינעירוני' and road1 and road2:
        res = 'צומת כביש ' + road1 + ' עם כביש ' + road2
    elif resolution == 'צומת בינעירוני' and road1 and road_segment_name:
        res = 'כביש ' + road1 + ' במקטע ' + road_segment_name
    elif resolution == 'רחוב' and yishuv_name and street1_hebrew:
        res = ' רחוב ' + street1_hebrew + ' ב' + yishuv_name
    else:
        logging.warning(
            "Did not found quality resolution. Using location field. News Flash id:{}".format(nf['id']))
        res = nf['location']
    logging.debug('{}'.format(res))
    return res

def create_infographics_data(news_flash_id, number_of_years_ago):
    output = {}
    try:
        number_of_years_ago = int(number_of_years_ago)
    except ValueError:
        return Response({})
    if number_of_years_ago < 0 or number_of_years_ago > 100:
        return Response({})
    location_info = extract_news_flash_location(news_flash_id)
    logging.debug('location_info:{}'.format(location_info))
    if location_info is None:
        return Response({})
    location_text = get_news_flash_location_text(news_flash_id)
    logging.debug('location_text:{}'.format(location_text))
    gps = location_info['gps']
    location_info = location_info['data']
    output['meta'] = {"location_info": location_info.copy()}
    output['widgets'] = []
    resolution = location_info.pop('resolution')
    if resolution is None:
        return Response({})

    if all(value is None for value in location_info.values()):
        return Response({})

    end_time = datetime.date.today()
    start_time = datetime.date(
        end_time.year - number_of_years_ago, 1, 1)

    # accident_severity count
    text, items = get_accident_count_by_severity(location_info=location_info,
                                                 location_text=location_text,
                                                 start_time=start_time,
                                                 end_time=end_time)

    accident_count_by_severity = Widget(name='accident_count_by_severity',
                                        rank=1,
                                        items=items,
                                        text=text)
    output['widgets'].append(accident_count_by_severity.serialize())

    # most severe accidents table
    most_severe_accidents_table = Widget(name='most_severe_accidents_table',
                                        rank=2,
                                        items=get_most_severe_accidents_table(location_info, start_time, end_time),
                                        title=get_most_severe_accidents_table_title(location_text))
    output['widgets'].append(most_severe_accidents_table.serialize())

    # most severe accidents
    most_severe_accidents = Widget(name='most_severe_accidents',
                                   rank=3,
                                   items=get_most_severe_accidents(table_obj=AccidentMarkerView,
                                                                   filters=location_info,
                                                                   start_time=start_time,
                                                                   end_time=end_time))
    output['widgets'].append(most_severe_accidents.serialize())

    # street view
    street_view = Widget(name='street_view',
                         rank=4,
                         items={'longitude': gps['lon'],
                                'latitude': gps['lat']})
    output['widgets'].append(street_view.serialize())


    # vision zero
    vision_zero = Widget(name='vision_zero',
                         rank=5,
                         items=['vision_zero_2_plus_1'])
    output['widgets'].append(vision_zero.serialize())

    # accident_type count
    accident_count_by_accident_type = Widget(name='accident_count_by_accident_type',
                                             rank=6,
                                             items=get_accident_count_by_accident_type(location_info=location_info,
                                                                                       start_time=start_time,
                                                                                       end_time=end_time))
    output['widgets'].append(accident_count_by_accident_type.serialize())

    # accidents heat map
    accidents_heat_map = Widget(name='accidents_heat_map',
                         rank=7,
                         items=get_accidents_heat_map(table_obj=AccidentMarkerView,
                                                      filters=location_info,
                                                      start_time=start_time,
                                                      end_time=end_time))
    output['widgets'].append(accidents_heat_map.serialize())

    # accident count by accident year
    accident_count_by_accident_year = Widget(name='accident_count_by_accident_year',
                                            rank=8,
                                            items=get_accidents_stats(table_obj=AccidentMarkerView,
                                                                      filters=location_info,
                                                                      group_by='accident_year',
                                                                      count='accident_year',
                                                                      start_time=start_time,
                                                                      end_time=end_time),
                                            title='כמות תאונות')
    output['widgets'].append(accident_count_by_accident_year.serialize())

    # injured count by accident year
    injured_count_by_accident_year = Widget(name='injured_count_by_accident_year',
                                            rank=9,
                                            items=get_accidents_stats(table_obj=InvolvedMarkerView,
                                                                      filters=get_injured_filters(location_info),
                                                                      group_by='accident_year',
                                                                      count='accident_year',
                                                                      start_time=start_time,
                                                                      end_time=end_time),
                                            title='כמות פצועים')
    output['widgets'].append(injured_count_by_accident_year.serialize())

    # accident count on day light
    accident_count_by_day_night = Widget(name='accident_count_by_day_night',
                                         rank=10,
                                         items=get_accidents_stats(table_obj=AccidentMarkerView,
                                                                   filters=location_info,
                                                                   group_by='day_night_hebrew',
                                                                   count='day_night_hebrew',
                                                                   start_time=start_time,
                                                                   end_time=end_time),
                                         title='כמות תאונות ביום ובלילה')
    output['widgets'].append(accident_count_by_day_night.serialize())

    # accidents distribution count by hour
    accidents_count_by_hour = Widget(name='accidents_count_by_hour',
                                         rank=11,
                                         items=get_accidents_stats(table_obj=AccidentMarkerView,
                                                                   filters=location_info,
                                                                   group_by='accident_hour',
                                                                   count='accident_hour',
                                                                   start_time=start_time,
                                                                   end_time=end_time),
                                         title='כמות תאונות לפי שעה')
    output['widgets'].append(accidents_count_by_hour.serialize())

    # accident count by road_light
    accident_count_by_road_light = Widget(name='accident_count_by_road_light',
                                         rank=12,
                                         items=get_accidents_stats(table_obj=AccidentMarkerView,
                                                                   filters=location_info,
                                                                   group_by='road_light_hebrew',
                                                                   count='road_light_hebrew',
                                                                   start_time=start_time,
                                                                   end_time=end_time),
                                         title='כמות תאונות לפי תאורה')
    output['widgets'].append(accident_count_by_road_light.serialize())

    # accident count by road_segment
    top_road_segments_accidents_per_km = Widget(name='top_road_segments_accidents_per_km',
                                         rank=13,
                                         items=get_top_road_segments_accidents_per_km(resolution=resolution,
                                                                                     location_info=location_info,
                                                                                     start_time=start_time,
                                                                                     end_time=end_time))
    output['widgets'].append(top_road_segments_accidents_per_km.serialize())

    # injured count per age group
    data_of_injured_count_per_age_group_raw = get_accidents_stats(table_obj=InvolvedMarkerView,
                                                                  filters=get_injured_filters(location_info),
                                                                  group_by='age_group_hebrew',
                                                                  count='age_group_hebrew',
                                                                  start_time=start_time,
                                                                  end_time=end_time)
    data_of_injured_count_per_age_group = filter_and_group_injured_count_per_age_group(data_of_injured_count_per_age_group_raw)

    injured_count_per_age_group = Widget(name='injured_count_per_age_group',
                                         rank=14,
                                         items=data_of_injured_count_per_age_group)
    output['widgets'].append(injured_count_per_age_group.serialize())

    return Response(json.dumps(output, default=str), mimetype="application/json")
