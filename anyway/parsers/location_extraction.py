import logging
import re
import math
import geohash  # python-geohash package
import googlemaps
import numpy as np
from geographiclib.geodesic import Geodesic
from anyway.backend_constants import BE_CONST
from anyway.models import NewsFlash
from anyway.parsers import resolution_dict
from anyway import secrets
from anyway.models import AccidentMarkerView, RoadSegments
from sqlalchemy import not_
import pandas as pd
from sqlalchemy.orm import load_only
from datetime import date


def extract_road_number(location):
    """
    extract road number from location if exist
    :param location: accident's location
    :return: extracted road number
    """
    try:
        road_number_regex = r"כביש (\d{1,4})"
        road_search = re.search(road_number_regex, location)
        if road_search:
            return int(road_search.group(1))
    except Exception as _:
        if location is not None:
            logging.info("bug in extract road number {0}".format(location))
        else:
            logging.info("bug in extract road number")
    return None


def get_road_segment_by_name(road_segment_name: str) -> RoadSegments:
    try:
        from anyway.app_and_db import db
    except ModuleNotFoundError:
        pass  # TODO: maybe throw exception?
    from_name = road_segment_name.split(" - ")[0].strip()
    to_name = road_segment_name.split(" - ")[1].strip()
    query_obj = (
        db.session.query(RoadSegments)
        .filter(RoadSegments.from_name == from_name)
        .filter(RoadSegments.to_name == to_name)
    )
    segment = query_obj.first()
    return segment


def get_road_segment_by_name_and_road(road_segment_name: str, road: int) -> RoadSegments:
    try:
        from anyway.app_and_db import db
    except ModuleNotFoundError:
        pass  # TODO: maybe throw exception?
    segments = db.session.query(RoadSegments).filter(RoadSegments.road == road).all()
    for segment in segments:
        if road_segment_name.startswith(segment.from_name) and road_segment_name.endswith(
            segment.to_name
        ):
            return segment
    err_msg = f"get_road_segment_by_name_and_road:{road_segment_name},{road}: not found"
    logging.error(err_msg)
    raise ValueError(err_msg)


def get_road_segment_name_and_number(road_segment_id) -> (float, str):
    try:
        from anyway.app_and_db import db
    except ModuleNotFoundError:
        pass  # TODO: maybe throw exception?
    query_obj = db.session.query(RoadSegments).filter(RoadSegments.segment_id == road_segment_id)
    segment = query_obj.first()
    from_name = segment.from_name  # pylint: disable=maybe-no-member
    to_name = segment.to_name  # pylint: disable=maybe-no-member
    road_segment_name = " - ".join([from_name, to_name])
    road = segment.road  # pylint: disable=maybe-no-member
    return float(road), road_segment_name


def get_db_matching_location_interurban(latitude, longitude) -> dict:
    """
    extracts location from db by closest geo point to location found, using road number if provided and limits to
    requested resolution
    :param latitude: location latitude
    :param longitude: location longitude
    """

    def get_bounding_box(latitude, longitude, distance_in_km):
        latitude = math.radians(latitude)
        longitude = math.radians(longitude)

        radius = 6371
        # Radius of the parallel at given latitude
        parallel_radius = radius * math.cos(latitude)

        lat_min = latitude - distance_in_km / radius
        lat_max = latitude + distance_in_km / radius
        lon_min = longitude - distance_in_km / parallel_radius
        lon_max = longitude + distance_in_km / parallel_radius
        rad2deg = math.degrees

        return rad2deg(lat_min), rad2deg(lon_min), rad2deg(lat_max), rad2deg(lon_max)

    try:
        from anyway.app_and_db import db
    except ModuleNotFoundError:
        pass  # TODO: maybe throw exception?

    distance_in_km = 1.5
    lat_min, lon_min, lat_max, lon_max = get_bounding_box(latitude, longitude, distance_in_km)
    base_x = lon_min
    base_y = lat_min
    distance_x = lon_max
    distance_y = lat_max
    polygon_str = "POLYGON(({0} {1},{0} {3},{2} {3},{2} {1},{0} {1}))".format(
        base_x, base_y, distance_x, distance_y
    )

    cutoff_year = (date.today()).year - 6
    query_obj = (
        db.session.query(AccidentMarkerView)
        .filter(AccidentMarkerView.geom.intersects(polygon_str))
        .filter(AccidentMarkerView.accident_year >= cutoff_year)
        .filter(AccidentMarkerView.provider_code != BE_CONST.RSA_PROVIDER_CODE)
        .filter(not_(AccidentMarkerView.road_segment_name == None))
        .options(
            load_only(
                "road1",
                "road_segment_id",
                "road_segment_name",
                "latitude",
                "longitude",
                "geom",
                "accident_year",
                "provider_code",
            )
        )
    )
    markers = pd.read_sql_query(query_obj.statement, query_obj.session.bind)

    geod = Geodesic.WGS84
    markers["geohash"] = markers.apply(  # pylint: disable=maybe-no-member
        lambda x: geohash.encode(x["latitude"], x["longitude"], precision=4), axis=1
    )  # pylint: disable=maybe-no-member
    markers_orig = markers.copy()  # pylint: disable=maybe-no-member
    markers = markers.loc[markers["road1"].notnull()]  # pylint: disable=maybe-no-member
    if markers.count()[0] == 0:
        markers = markers_orig

    # FILTER BY GEOHASH
    curr_geohash = geohash.encode(latitude, longitude, precision=4)
    if markers.loc[markers["geohash"] == curr_geohash].count()[0] > 0:
        markers = markers.loc[markers["geohash"] == curr_geohash].copy()

    # CREATE DISTANCE FIELD
    markers["dist_point"] = markers.apply(
        lambda x: geod.Inverse(latitude, longitude, x["latitude"], x["longitude"])["s12"], axis=1
    ).replace({np.nan: None})

    most_fit_loc = (
        markers.loc[markers["dist_point"] == markers["dist_point"].min()].iloc[0].to_dict()
    )

    final_loc = {}
    for field in ["road1", "road_segment_name"]:
        loc = most_fit_loc[field]
        if loc not in [None, "", "nan"]:
            if not (isinstance(loc, np.float64) and np.isnan(loc)):
                final_loc[field] = loc
    return final_loc


def get_db_matching_location(db, latitude, longitude, resolution, road_no=None):
    """
    extracts location from db by closest geo point to location found, using road number if provided and limits to
    requested resolution
    :param db: the DB
    :param latitude: location latitude
    :param longitude: location longitude
    :param resolution: wanted resolution
    :param road_no: road number if there is
    :return: a dict containing all the geo fields stated in
    resolution dict, with values filled according to resolution
    """
    # READ MARKERS FROM DB
    geod = Geodesic.WGS84
    relevant_fields = resolution_dict[resolution]
    markers = db.get_markers_for_location_extraction()
    markers["geohash"] = markers.apply(
        lambda x: geohash.encode(x["latitude"], x["longitude"], precision=4), axis=1
    )
    markers_orig = markers.copy()
    if resolution != "אחר":
        if (
            road_no is not None
            and road_no > 0
            and ("road1" in relevant_fields or "road2" in relevant_fields)
        ):
            markers = markers.loc[(markers["road1"] == road_no) | (markers["road2"] == road_no)]
        for field in relevant_fields:
            if field == "road1":
                markers = markers.loc[markers[field].notnull()]
                markers = markers.loc[markers[field] > 0]
            elif field in ["region_hebrew", "district_hebrew", "yishuv_name", "street1_hebrew"]:
                markers = markers.loc[markers[field].notnull()]
                markers = markers.loc[markers[field] != ""]
    if markers.count()[0] == 0:
        markers = markers_orig

    # FILTER BY GEOHASH
    curr_geohash = geohash.encode(latitude, longitude, precision=4)
    if markers.loc[markers["geohash"] == curr_geohash].count()[0] > 0:
        markers = markers.loc[markers["geohash"] == curr_geohash].copy()

    # CREATE DISTANCE FIELD
    markers["dist_point"] = markers.apply(
        lambda x: geod.Inverse(latitude, longitude, x["latitude"], x["longitude"])["s12"], axis=1
    ).replace({np.nan: None})

    most_fit_loc = (
        markers.loc[markers["dist_point"] == markers["dist_point"].min()].iloc[0].to_dict()
    )

    final_loc = {}
    for field in relevant_fields:
        loc = most_fit_loc[field]
        if loc not in [None, "", "nan"]:
            if not (isinstance(loc, np.float64) and np.isnan(loc)):
                final_loc[field] = loc
    return final_loc


def set_accident_resolution(accident_row):
    """
    set the resolution of the accident
    :param accident_row: single row of an accident
    :return: resolution option
    """
    try:
        if accident_row["intersection"] is not None and "/" in str(accident_row["intersection"]):
            return "צומת עירוני"
        elif accident_row["intersection"] is not None:
            return "צומת בינעירוני"
        elif accident_row["road_no"] is not None:
            return "כביש בינעירוני"
        elif accident_row["street"] is not None:
            return "רחוב"
        elif accident_row["city"] is not None:
            return "עיר"
        elif accident_row["subdistrict"] is not None:
            return "נפה"
        elif accident_row["district"] is not None:
            return "מחוז"
        else:
            return "אחר"
    except Exception as _:
        if accident_row is None:
            logging.info("bug in accident resolution")


def reverse_geocode_extract(latitude, longitude):
    """
    this method takes a latitude, longitude and returns a dict of the corresponding
    location found on google maps (by that string), describing details of the location found and the geometry
    :param latitude: latitude
    :param longitude: longitude
    :return: a dict containing data about the found location on google maps, with the keys: street,
    road_no [road number], intersection, city, address, district and the geometry of the location.
    """
    street = None
    road_no = None
    intersection = None
    subdistrict = None
    city = None
    district = None
    try:
        gmaps = googlemaps.Client(key=secrets.get("GOOGLE_MAPS_KEY"))
        geocode_result = gmaps.reverse_geocode((latitude, longitude))

        # if we got no results, move to next iteration of location string
        if not geocode_result:
            return None
    except Exception as _:
        logging.info("exception in gmaps")
        return None
    # logging.info(geocode_result)
    response = geocode_result[0]
    geom = response["geometry"]["location"]
    for item in response["address_components"]:
        if "route" in item["types"]:
            if item["short_name"].isdigit():
                road_no = int(item["short_name"])
            else:
                street = item["long_name"]
        elif "point_of_interest" in item["types"] or "intersection" in item["types"]:
            intersection = item["long_name"]
        elif "locality" in item["types"]:
            city = item["long_name"]
        elif "administrative_area_level_2" in item["types"]:
            subdistrict = item["long_name"]
        elif "administrative_area_level_1" in item["types"]:
            district = item["long_name"]
    address = response["formatted_address"]
    return {
        "street": street,
        "road_no": road_no,
        "intersection": intersection,
        "city": city,
        "address": address,
        "subdistrict": subdistrict,
        "district": district,
        "geom": geom,
    }


def geocode_extract(location):
    """
    this method takes a string representing location and a google maps key and returns a dict of the corresponding
    location found on google maps (by that string), describing details of the location found and the geometry
    :param location: string representing location
    :return: a dict containing data about the found location on google maps, with the keys: street,
    road_no [road number], intersection, city, address, district and the geometry of the location.
    """
    street = None
    road_no = None
    intersection = None
    subdistrict = None
    city = None
    district = None
    address = None
    geom = {"lat": None, "lng": None}
    for candidate_location_string in get_candidate_location_strings(location):
        try:
            logging.debug(f'using location string: "{candidate_location_string}"')
            gmaps = googlemaps.Client(key=secrets.get("GOOGLE_MAPS_KEY"))
            geocode_result = gmaps.geocode(candidate_location_string, region="il")

            # if we got no results, move to next iteration of location string
            if not geocode_result:
                logging.warning(
                    f'location string: "{candidate_location_string}" returned no results from gmaps'
                )
                continue

            response = geocode_result[0]
            geom = response["geometry"]["location"]
            for item in response["address_components"]:
                if "route" in item["types"]:
                    if item["short_name"].isdigit():
                        road_no = int(item["short_name"])
                    else:
                        street = item["long_name"]
                elif "point_of_interest" in item["types"] or "intersection" in item["types"]:
                    intersection = item["long_name"]
                elif "locality" in item["types"]:
                    city = item["long_name"]
                elif "administrative_area_level_2" in item["types"]:
                    subdistrict = item["long_name"]
                elif "administrative_area_level_1" in item["types"]:
                    district = item["long_name"]
            address = response["formatted_address"]
            if road_no is None and extract_road_number(candidate_location_string) is not None:
                road_no = extract_road_number(candidate_location_string)
        except Exception as _:
            logging.exception(
                f'exception caught while extracting geocode location for: "{candidate_location_string}"'
            )

        return {
            "street": street,
            "road_no": road_no,
            "intersection": intersection,
            "city": city,
            "address": address,
            "subdistrict": subdistrict,
            "district": district,
            "geom": geom,
        }

    # we can no longer rectify the location string, log and return None
    logging.exception(f"Failed to extract location for {location}")
    return None


def extract_location_text(text):
    """
    filters the text so it will be easier to find corresponding geolocation, based on manual chosen filters.
    :param text: text
    :return: filtered text - should catch the correct location most of the time.
    """
    if text is None:
        return None
    filter_ind = float("inf")
    if text.find(".") != -1:
        text = text[: text.find(".")]
    try:
        if text.find(".") != -1:
            text = text[: text.find(".")]
        forbid_words = ["תושב"]
        hospital_words = ["בבית החולים", "בית חולים", "בית החולים", "מרכז רפואי"]
        hospital_names = [
            "שיבא",
            "וולפסון",
            "תל השומר",
            "סוראסקי",
            "הלל יפה",
            'רמב"ם',
            "רמבם",
            "בני ציון",
            "רוטשילד",
            "גליל מערבי",
            "זיו",
            "פוריה",
            "ברזילי",
            "אסף הרופא",
            "סורוקה",
            "רבין",
            "בלינסון",
            "גולדה",
            "כרמל",
            "עמק",
            "מאיר",
            "קפלן",
            "יוספטל",
            "הדסה",
            "שערי צדק",
            "צאנז",
            "לניאדו",
            "אסותא",
            "מעיני הישועה",
            "מדיקל סנטר",
            "איטלקי",
            "המשפחה הקדושה",
        ]
        forbid_words.extend(hospital_words)
        for forbid_word in forbid_words:
            found_hospital = False
            removed_punc = False
            if forbid_word in text:
                forbid_ind = text.find(forbid_word)
                for punc_to_try in [",", " - "]:
                    punc_before_ind = text.find(punc_to_try, 0, forbid_ind)
                    punc_after_ind = text.find(punc_to_try, forbid_ind)
                    if punc_before_ind != -1 or punc_after_ind != -1:
                        if punc_before_ind == -1:
                            text = text[(punc_after_ind + 1) :]
                        elif punc_after_ind == -1:
                            text = text[:punc_before_ind]
                        else:
                            text = text[:punc_before_ind] + " " + text[(punc_after_ind + 1) :]
                        removed_punc = True
                        break
                if (not removed_punc) and (forbid_word in hospital_words):
                    for hospital_name in hospital_names:
                        hospital_ind = text.find(hospital_name)
                        if (
                            hospital_ind == forbid_ind + len(forbid_word) + 1
                            or hospital_ind == forbid_ind + len(forbid_word) + 2
                        ):
                            text = (
                                text[:hospital_ind] + text[hospital_ind + len(hospital_name) + 1 :]
                            )
                            forbid_ind = text.find(forbid_word)
                            text = text[:forbid_ind] + text[forbid_ind + len(forbid_word) + 1 :]
                            found_hospital = True
                if (not found_hospital) and (not removed_punc):
                    text = (
                        text[:forbid_ind]
                        + text[text.find(" ", forbid_ind + len(forbid_word) + 2) :]
                    )

    except Exception as _:
        logging.exception("could not filter text {0}".format(text))

    loc_tokens = [
        "כביש",
        "שדרות",
        "רחוב",
        "מחלף",
        "צומת",
        "יישוב",
        "מושב",
        "קיבוץ",
        "התנחלות",
        "שכונת",
        "בדרך",
    ]
    for token in loc_tokens:
        i = text.find(token)
        if i >= 0:
            filter_ind = min(filter_ind, i)

    near_tokens = ["סמוך ל", "ליד ה"]  # maybe add: "ליד "
    for token in near_tokens:
        i = text.find(token)
        if i >= 0:
            filter_ind = min(filter_ind, i + len(token))

    if filter_ind != float("inf"):
        text = text[filter_ind:]

    for token in near_tokens:
        i = text.find(token)
        if i >= 0:
            text = text[:i] + token + text[i + len(token) :]
    return text


def extract_geo_features(db, newsflash: NewsFlash) -> None:
    newsflash.location = extract_location_text(newsflash.description) or extract_location_text(
        newsflash.title
    )
    geo_location = geocode_extract(newsflash.location)
    if geo_location is not None:
        newsflash.lat = geo_location["geom"]["lat"]
        newsflash.lon = geo_location["geom"]["lng"]
        newsflash.resolution = set_accident_resolution(geo_location)
        location_from_db = get_db_matching_location(
            db, newsflash.lat, newsflash.lon, newsflash.resolution, geo_location["road_no"]
        )
        for k, v in location_from_db.items():
            setattr(newsflash, k, v)
        all_resolutions = []
        for _, v in resolution_dict.items():
            all_resolutions += v
        for resolution in all_resolutions:
            if resolution not in location_from_db:
                setattr(newsflash, resolution, None)


def get_candidate_location_strings(location_string):
    """
    Here, we iteratively try to make basic modifications on the original location string
    in case gmaps.geocode() can't make sense of it
    """
    yield location_string
    trimmed_location_string = first_location_preposition(location_string)
    yield trimmed_location_string


def first_location_preposition(location_string):
    """
    In some cases google can't extract a response from the original
    sentence but will be able to do so from a sub-sentence starting at the first location indicator
    e.g.
    "גבר נהרג בתאונת דרכים בגליל התחתון"
    ->no results
    "בתאונת דרכים בגליל התחתון"
    ->results
    """

    # iterate over sentences, find first location preposition (very crudely) and trim the prefix of that sentence
    for sentence in location_string.split("."):
        trimmed_location_tokens = []
        found = False
        for token in sentence.split():
            if token.startswith("ב"):
                found = True
            if found:
                trimmed_location_tokens.append(token)

        if found:
            return " ".join(trimmed_location_tokens)

    return ""
