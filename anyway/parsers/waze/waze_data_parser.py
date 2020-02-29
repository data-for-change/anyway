from google.cloud import storage
import pandas as pd
from pandas.io.json import json_normalize
import json
import cloudstorage as gcs

def list_blobs(bucket_name):
    """Lists all the blobs in the bucket."""
    storage_client = storage.Client()

    blobs = storage_client.list_blobs(bucket_name)

    return blobs


# def get_waze_json(bucket_name, file_name):
#     gcs_file = gcs.open('{}/{}'.format(bucket_name, file_name))
#     contents = gcs_file.read()
#     gcs_file.close()


def parse_waze_data(waze_json, created_at):
    """
    parse waze json into a Dataframe.
    param waze_json: waze raw json data
    return: parsed Dataframe
    """

    waze_json = json.loads(waze_json)

    waze_df = json_normalize(waze_json['alerts'])
    waze_df['created_at'] = pd.to_datetime(created_at)
    return waze_df

def parser(bucket_name):
    waze_list = []
    for i, file in enumerate(list_blobs(bucket_name)):
        if i < 4:
            waze_created_at = file.time_created
            waze_data = file.download_as_string()
            waze_list.append(parse_waze_data(waze_data, waze_created_at))

    waze_df = pd.concat(waze_list, ignore_index=True)
    return waze_df

BUCKET_NAME = 'anyway-hasadna.appspot.com'
results = parser(BUCKET_NAME)
print(results.columns)