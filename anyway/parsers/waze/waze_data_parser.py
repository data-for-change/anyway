import logging
import json
import requests
from pandas import json_normalize
import pandas as pd
from google.cloud import storage

from anyway.parsers.waze.waze_db_functions import insert_waze_alerts, insert_waze_traffic_jams
from anyway.models import WazeAlert, WazeTrafficJams


ISRAEL_POLYGON = [
    ("33.717000", "32.547000"),
    ("34.722000", "33.004000"),
    ("35.793000", "33.331000"),
    ("35.914000", "32.953000"),
    ("35.750000", "32.723000"),
    ("35.395000", "31.084000"),
    ("34.931000", "29.473000"),
    ("33.717000", "32.547000"),
    ("33.717000", "32.547000"),
]
WAZE_ALERTS_API_PARAMS = {
    "format": "JSON",
    "tk": "ccp_partner",
    "ccp_partner_name": "The Public Knowledge Workshop",
    "types": "traffic,alerts,irregularities",
    "polygon": ";".join([",".join(point) for point in ISRAEL_POLYGON]),
}
WAZE_ALERTS_API_URL = "https://il-georss.waze.com/rtserver/web/TGeoRSS"


logger = logging.getLogger("waze_data")


def list_blobs(bucket_name):
    """
    Lists all the blobs in the bucket.
    """
    storage_client = storage.Client()
    blobs = storage_client.list_blobs(bucket_name)

    return blobs


def parse_waze_alerts_data(waze_alerts):
    """
    parse waze alert json into a Dataframe.
    param waze_alerts: waze raw alert json data
    return: parsed Dataframe
    """

    waze_df = json_normalize(waze_alerts)
    waze_df["created_at"] = pd.to_datetime(waze_df["pubMillis"], unit="ms")
    waze_df.rename(
        {
            "location.x": "longitude",
            "location.y": "latitude",
            "nThumbsUp": "number_thumbs_up",
            "reportRating": "report_rating",
            "reportDescription": "report_description",
            "reportByMunicipalityUser": "report_by_municipality_user",
            "jamUuid": "jam_uuid",
            "type": "alert_type",
            "subtype": "alert_subtype",
            "roadType": "road_type",
        },
        axis=1,
        inplace=True,
    )
    waze_df["geom"] = waze_df.apply(
        lambda row: "POINT({} {})".format(row["longitude"], row["latitude"]), axis=1
    )
    waze_df["road_type"] = int(waze_df["road_type"].fillna(-1)[0])
    waze_df["number_thumbs_up"] = int(waze_df.get("number_thumbs_up").fillna(0)[0])
    waze_df["report_by_municipality_user"] = _convert_to_bool(waze_df.get("report_by_municipality_user", False))

    waze_df.drop(["country", "pubMillis"], axis=1, inplace=True, errors='ignore')
    for key in waze_df.keys():
        if waze_df[key] is None or key not in [field.name for field in WazeAlert.__table__.columns]:
            waze_df.drop([key], axis=1, inplace=True)

    return waze_df.to_dict("records")


def parse_waze_traffic_jams_data(waze_jams):
    """
    parse waze traffic jams json into a Dataframe.
    param waze_jams: waze raw traffic jams json data
    return: parsed Dataframe
    """

    waze_df = json_normalize(waze_jams)
    waze_df["created_at"] = pd.to_datetime(waze_df["pubMillis"], unit="ms")
    waze_df["geom"] = waze_df["line"].apply(
        lambda l: "LINESTRING({})".format(",".join(["{} {}".format(nz["x"], nz["y"]) for nz in l]))
    )
    waze_df["line"] = waze_df["line"].apply(str)
    waze_df["segments"] = waze_df["segments"].apply(str)
    waze_df["turnType"] = waze_df["roadType"].fillna(-1)
    waze_df.drop(["country", "pubMillis"], axis=1, inplace=True)
    waze_df.rename(
        {
            "speedKMH": "speed_kmh",
            "turnType": "turn_type",
            "roadType": "road_type",
            "endNode": "end_node",
            "blockingAlertUuid": "blocking_alert_uuid",
            "startNode": "start_node",
        },
        axis=1,
        inplace=True,
    )
    for key in waze_df.keys():
        if waze_df[key] is None or key not in [field.name for field in WazeTrafficJams.__table__.columns]:
            waze_df.drop([key], axis=1, inplace=True)

    return waze_df.to_dict("records")


def ingest_waze_from_files(bucket_name, start_date, end_date):
    """
    iterate over waze files in google cloud bucket, parse them and insert them to db
    param bucket_name: google cloud bucket name
    param start_date: date to start fetch waze files
    param end_date: date to end fetch waze files
    return: parsed Dataframe
    """
    blobs = []
    total_ingested_alerts = 0
    total_ingested_traffic = 0

    dates_range = pd.date_range(start=start_date, end=end_date, freq="D")
    prefixs = ["waze-api-dumps-TGeoRSS/{}/".format(d.strftime("%Y/%-m/%-d")) for d in dates_range]

    storage_client = storage.Client()

    for prefix in prefixs:
        blobs.extend(storage_client.list_blobs(bucket_name, prefix=prefix, delimiter="/"))

    bulk_size = 50
    bulk_jsons = []
    for waze_file in blobs:
        waze_data = waze_file.download_as_string()
        waze_json = json.loads(waze_data)
        bulk_jsons.append(waze_json)
        if len(bulk_jsons) % bulk_size == 0:
            alerts_count, jams_count = _ingest_waze_jsons(bulk_jsons)
            total_ingested_alerts += alerts_count
            total_ingested_traffic += jams_count
            bulk_jsons = []

    # ingest remaining
    alerts_count, jams_count = _ingest_waze_jsons(bulk_jsons)
    total_ingested_alerts += alerts_count
    total_ingested_traffic += jams_count
    logger.info(f"Ingested {total_ingested_alerts} alerts, {jams_count} jams")


def ingest_waze_from_api():
    """
    iterate over waze files in google cloud bucket, parse them and insert them to db
    param bucket_name: google cloud bucket name
    param start_date: date to start fetch waze files
    param end_date: date to end fetch waze files
    return: parsed Dataframe
    """
    response = requests.get(WAZE_ALERTS_API_URL, params=WAZE_ALERTS_API_PARAMS)
    response.raise_for_status()
    waze_data = json.loads(response.content)

    alerts_count, jams_count = _ingest_waze_jsons([waze_data])
    logger.info(f"Ingested {alerts_count} alerts, {jams_count} jams")


def _ingest_waze_jsons(waze_jsons):
    waze_alerts = []
    waze_traffic_jams = []

    for waze_data in waze_jsons:
        waze_alerts.extend(parse_waze_alerts_data(waze_data["alerts"]))
        waze_traffic_jams.extend(parse_waze_traffic_jams_data(waze_data.get("jams")))

    logger.debug(f"Ingesting #{len(waze_alerts)} waze_alert records in bulk")
    insert_waze_alerts(waze_alerts)
    logger.debug(f"Ingesting #{len(waze_traffic_jams)} waze_traffic_jams records in bulk")
    insert_waze_traffic_jams(waze_traffic_jams)

    return len(waze_alerts), len(waze_traffic_jams)


def _convert_to_bool(value):
    if isinstance(value, bool):
        return value
    else:
        return str(value).lower() in ("yes", "true", "t", "1")
