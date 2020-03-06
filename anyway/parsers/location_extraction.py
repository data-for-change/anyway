# coding=utf-8

import re

import geohash  # python-geohash package
import googlemaps
import numpy as np
from geographiclib.geodesic import Geodesic

from anyway.parsers.news_flash_parser import get_markers_for_location_extraction
from . import resolution_dict
import logging

def extract_road_number(location):
    """
    extract road number from location if exist
    :param location: accident's location
    :return: extracted road number
    """
    road_number_regex = r'כביש (\d{1,4})'
    road_search = re.search(road_number_regex, location)
    if road_search:
        return int(road_search.group(1))
    return None


def get_db_matching_location(latitude, longitude, resolution, road_no=None):
    """
    extracts location from db by closest geo point to location found, using road number if provided and limits to
    requested resolution
    :param latitude: location latitude
    :param longitude: location longitude
    :param resolution: wanted resolution
    :param road_no: road number if there is
    :return: a dict containing all the geo fields stated in
    resolution dict, with values filled according to resolution
    """
    geod = Geodesic.WGS84

    relevant_fields = resolution_dict[resolution]
    final_loc = {}
    for field in resolution_dict['אחר']:
        final_loc[field] = None

    # READ MARKERS FROM DB
    markers = get_markers_for_location_extraction()
    markers['geohash'] = markers.apply(lambda x: geohash.encode(x['latitude'], x['longitude'], precision=4), axis=1)
    markers_orig=markers.copy()
    if resolution != 'אחר':
        if road_no is not None and road_no!='' and int(road_no) > 0 and ('road1' in relevant_fields or 'road2' in relevant_fields):
            markers = markers.loc[(markers['road1'] == int(road_no)) | (markers['road2'] == int(road_no))]
        for field in relevant_fields:
            if field == 'road1':
                markers = markers.loc[markers[field].notnull()]
                markers = markers.loc[markers[field] > 0]
            elif field == 'region_hebrew' or field == 'district_hebrew' or \
                    field == 'yishuv_name' or field == 'street1_hebrew':
                markers = markers.loc[markers[field].notnull()]
                markers = markers.loc[markers[field] != '']
    if markers.count()[0]==0:
        markers=markers_orig

    # FILTER BY GEOHASH
    curr_geohash = geohash.encode(latitude, longitude, precision=4)
    if markers.loc[markers['geohash'] == curr_geohash].count()[0] > 0:
        markers = markers.loc[markers['geohash'] == curr_geohash].copy()

    # CREATE DISTANCE FIELD
    markers['dist_point'] = markers.apply(
        lambda x: geod.Inverse(latitude, longitude, x['latitude'], x['longitude'])['s12'], axis=1)
    most_fit_loc = markers.loc[markers['dist_point'] == markers['dist_point'].min()].iloc[0].to_dict()
    for field in relevant_fields:
        if most_fit_loc[field] is not None:
            if (type(most_fit_loc[field])==str and (most_fit_loc[field] == '' or most_fit_loc[field]=='nan'))\
            or (type(most_fit_loc[field])==np.float64 and np.isnan(most_fit_loc[field])):
                final_loc[field]=None
            else:
                final_loc[field] = most_fit_loc[field]
    return final_loc


def set_accident_resolution(accident_row):
    """
    set the resolution of the accident
    :param accident_row: single row of an accident
    :return: resolution option
    """
    logging.info(accident_row['link'])

    if accident_row['intersection'] is not None and str(accident_row['intersection']) != '' and '/' in str(
            accident_row['intersection']):
        return 'צומת עירוני'
    elif accident_row['intersection'] is not None and str(accident_row['intersection']) != '':
        return 'צומת בינעירוני'
    elif accident_row['intersection'] is not None and str(accident_row['road_no']) != '':
        return 'כביש בינעירוני'
    elif accident_row['street'] is not None and str(accident_row['street']) != '':
        return 'רחוב'
    elif accident_row['city'] is not None and str(accident_row['city']) != '':
        return 'עיר'
    elif accident_row['subdistrict'] is not None and str(accident_row['subdistrict']) != '':
        return 'נפה'
    elif accident_row['district'] is not None and str(accident_row['district']) != '':
        return 'מחוז'
    else:
        return 'אחר'


def geocode_extract(location, maps_key):
    """
    this method takes a string representing location and a google maps key and returns a dict of the corresponding
    location found on google maps (by that string), describing details of the location found and the geometry
    :param location: string representing location
    :param maps_key: google maps API key
    :return: a dict containing data about the found location on google maps, with the keys: street,
    road_no [road number], intersection, city, address, district and the geometry of the location.
    """
    gmaps = googlemaps.Client(key=maps_key)
    geocode_result = gmaps.geocode(location, region='il')
    if geocode_result is None or geocode_result == []:
        return None
    response = geocode_result[0]
    geom = response['geometry']['location']
    street = ''
    road_no = ''
    intersection = ''
    subdistrict = ''
    city = ''
    district = ''
    for item in response['address_components']:
        if 'route' in item['types']:
            if item['short_name'].isdigit():
                road_no = item['short_name']
            else:
                street = item['long_name']
        elif 'point_of_interest' in item['types'] or 'intersection' in item['types']:
            intersection = item['long_name']
        elif 'locality' in item['types']:
            city = item['long_name']
        elif 'administrative_area_level_2' in item['types']:
            subdistrict = item['long_name']
        elif 'administrative_area_level_1' in item['types']:
            district = item['long_name']
    address = response['formatted_address']
    if road_no == '' and extract_road_number(location) is not None:
        road_no = extract_road_number(location)
    return {'street': street, 'road_no': road_no, 'intersection': intersection,
            'city': city, 'address': address, 'subdistrict': subdistrict,
            'district': district, 'geom': geom}


def manual_filter_location_of_text(text):
    """
    filters the text so it will be easier to find corresponding geolocation, based on manual chosen filters.
    :param text: text
    :return: filtered text - should catch the correct location most of the time.
    """
    filter_ind = float('inf')
    if text.find('.') != -1:
        text = text[:text.find('.')]
    try:
        forbid_words = ['תושב']
        hospital_words = ['בבית החולים', 'בית חולים', 'בית החולים', 'מרכז רפואי']
        hospital_names = ['שיבא', 'וולפסון', 'תל השומר', 'סוראסקי', 'הלל יפה', 'רמב"ם', 'רמבם', 'בני ציון', 'רוטשילד',
                          'גליל מערבי', 'זיו', 'פוריה', 'ברזילי', 'אסף הרופא', 'סורוקה', 'רבין', 'בלינסון', 'גולדה',
                          'כרמל', 'עמק', 'מאיר', 'קפלן', 'יוספטל', 'הדסה', 'שערי צדק', 'צאנז', 'לניאדו', 'אסותא',
                          'מעיני הישועה', 'מדיקל סנטר', 'איטלקי', 'המשפחה הקדושה']
        forbid_words.extend(hospital_words)
        for forbid_word in forbid_words:
            found_hospital = False
            removed_punc = False
            if forbid_word in text:
                forbid_ind = text.find(forbid_word)
                for punc_to_try in [',', ' - ']:
                    punc_before_ind = text.find(punc_to_try, 0, forbid_ind)
                    punc_after_ind = text.find(punc_to_try, forbid_ind)
                    if punc_before_ind != -1 or punc_after_ind != -1:
                        if punc_before_ind == -1:
                            text = text[(punc_after_ind + 1):]
                        elif punc_after_ind == -1:
                            text = text[:punc_before_ind]
                        else:
                            text = text[:punc_before_ind] + ' ' + text[(punc_after_ind + 1):]
                        removed_punc = True
                        break
                if (not removed_punc) and (forbid_word in hospital_words):
                    for hospital_name in hospital_names:
                        hospital_ind = text.find(hospital_name)
                        if hospital_ind == forbid_ind + len(forbid_word) + 1 or hospital_ind == forbid_ind + len(
                                forbid_word) + 2:
                            text = text[:hospital_ind] + text[hospital_ind + len(hospital_name) + 1:]
                            forbid_ind = text.find(forbid_word)
                            text = text[:forbid_ind] + text[forbid_ind + len(forbid_word) + 1:]
                            found_hospital = True
                if (not found_hospital) and (not removed_punc):
                    text = text[:forbid_ind] + text[text.find(' ', forbid_ind + len(forbid_word) + 2):]

    except Exception as _:
        pass
    if 'כביש' in text:
        filter_ind = min(filter_ind, text.find('כביש'))
    if 'שדרות' in text:
        filter_ind = min(filter_ind, text.find('שדרות'))
    if 'רחוב' in text:
        filter_ind = min(filter_ind, text.find('רחוב'))
    if 'מחלף' in text:
        filter_ind = min(filter_ind, text.find('מחלף'))
    if 'צומת' in text:
        filter_ind = min(filter_ind, text.find('צומת'))
    if 'סמוך ל' in text:
        filter_ind = min(filter_ind, text.find('סמוך ל') + len('סמוך ל'))
    if 'ליד ה' in text:
        filter_ind = min(filter_ind, text.find('ליד ה') + len('ליד ה'))
    if 'יישוב' in text:
        filter_ind = min(filter_ind, text.find('יישוב'))
    if 'מושב' in text:
        filter_ind = min(filter_ind, text.find('מושב'))
    if 'קיבוץ' in text:
        filter_ind = min(filter_ind, text.find('קיבוץ'))
    if 'התנחלות' in text:
        filter_ind = min(filter_ind, text.find('התנחלות'))
    if 'שכונת' in text:
        filter_ind = min(filter_ind, text.find('שכונת'))
    if 'בדרך' in text:
        filter_ind = min(filter_ind, text.find('בדרך'))
    if filter_ind != float('inf'):
        text = text[filter_ind:]
    if 'סמוך ל' in text:
        text = text[(text.find('סמוך ל') + len('סמוך ל')):] + 'סמוך ל' + text[:text.find('סמוך ל')]
    if 'ליד ה' in text:
        text = text[(text.find('ליד ה') + len('ליד ה')):] + 'ליד ה ' + text[:text.find('ליד ה ')]
    return text
