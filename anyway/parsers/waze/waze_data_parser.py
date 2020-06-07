from google.cloud import storage
import pandas as pd
from pandas.io.json import json_normalize
import json
from .waze_db_functions import insert_waze_alerts, insert_waze_traffic_jams


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
            "location.x": "latitude",
            "location.y": "lontitude",
            "nThumbsUp": "number_thumbs_up",
            "reportRating": "report_rating",
            "type": "alert_type",
            "subtype": "alert_subtype",
            "roadType": "road_type",
        },
        axis=1,
        inplace=True,
    )
    waze_df["geom"] = waze_df.apply(
        lambda row: "POINT({} {})".format(row["lontitude"], row["latitude"]), axis=1
    )
    waze_df["road_type"] = waze_df["road_type"].fillna(-1)
    waze_df.drop(["country", "pubMillis", "reportDescription"], axis=1, inplace=True)

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

    return waze_df.to_dict("records")


def waze_parser(bucket_name, start_date, end_date):
    """
    iterate over waze files in google cloud bucket, parse them and insert them to db
    param bucket_name: google cloud bucket name
    param start_date: date to start fetch waze files
    param end_date: date to end fetch waze files
    return: parsed Dataframe
    """
    waze_alerts = []
    waze_traffic_jams = []
    blobs = []

    dates_range = pd.date_range(start=start_date, end=end_date, freq="D")
    prefixs = ["waze-api-dumps-TGeoRSS/{}/".format(d.strftime("%Y/%-m/%-d")) for d in dates_range]

    storage_client = storage.Client()

    for prefix in prefixs:
        blobs.extend(storage_client.list_blobs(bucket_name, prefix=prefix, delimiter="/"))

    for waze_file in blobs:
        waze_data = waze_file.download_as_string()
        waze_json = json.loads(waze_data)
        waze_alerts.extend(parse_waze_alerts_data(waze_json["alerts"]))
        waze_traffic_jams.extend(parse_waze_traffic_jams_data(waze_json["jams"]))

    insert_waze_alerts(waze_alerts)
    insert_waze_traffic_jams(waze_traffic_jams)
