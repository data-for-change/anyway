import requests
import json
from typing import Iterable, Dict, Any, List
from anyway.models import Streets
from anyway.app_and_db import db
import logging

CBS_STREETS_RESOURCES_URL = "https://data.gov.il/api/3/action/package_show?id=321"
RESOURCE_NAME = "רשימת רחובות בישראל - מתעדכן"
BASE_GET_DATA_GOV = "https://data.gov.il/dataset/321"
RESOURCE_DOWNLOAD_TEMPLATE = (
    "https://data.gov.il/api/3/action/datastore_search?resource_id={id}&limit=1000000"
)
STREETS_FILE_YISHUV_NAME = "שם_ישוב"
STREETS_FILE_YISHUV_SYMBOL = "סמל_ישוב"
STREETS_FILE_STREET_NAME = "שם_רחוב"
STREETS_FILE_STREET_SYMBOL = "סמל_רחוב"
CHUNK_SIZE = 1000


class UpdateStreetsFromCSB:
    def __init__(self):
        self.s = requests.Session()

    def get_cbs_streets_download_url(self):
        response = self.s.get(CBS_STREETS_RESOURCES_URL)
        if not response.ok:
            raise Exception(
                f"Could not get streets url. reason:{response.reason}:{response.status_code}"
            )
        data = json.loads(response.text)
        if (
            not data.get("success")
            and not data.get("result")
            and not data["result"].get("resources")
        ):
            raise Exception(f"Could not get streets url. received bad data:{data.get('success')}")
        it = filter(
            lambda x: x["name"] == RESOURCE_NAME and x["format"] == "CSV",
            data["result"].get("resources"),
        )
        item = list(it)[0]
        url = RESOURCE_DOWNLOAD_TEMPLATE.format(id=item["id"])
        logging.info(f"Streets data last updated: {item['last_modified']}")
        # url_part = item["url"][take_from + 1:]
        return url
        # return f"{BASE_GET_DATA_GOV}/{url_part}"

    def get_streets_data_chunks(self, url: str, chunk_size: int) -> Iterable[List[Dict[str, Any]]]:
        # r = requests.get(url, stream=True, allow_redirects=True)
        r = self.s.get(url)
        if not r.ok:
            raise Exception(f"Could not get streets url. reason:{r.reason}:{r.status_code}")
        data = json.loads(r.text)
        chunk = []
        logging.debug(f"read {len(data['result']['records'])} records from {url}.")
        for item in data["result"]["records"]:
            street_name = item[STREETS_FILE_STREET_NAME]
            street_name_len = len(street_name)
            street_entry = {
                "yishuv_symbol": item[STREETS_FILE_YISHUV_SYMBOL],
                "street": item[STREETS_FILE_STREET_SYMBOL],
                "street_hebrew": street_name[: min(street_name_len, Streets.MAX_NAME_LEN)],
            }
            chunk.append(street_entry)
            if len(chunk) == chunk_size:
                yield chunk
                chunk = []
        if chunk:
            logging.debug(f"last chunk: {len(chunk)}.")
            yield chunk

    def import_street_file_into_db(self, url: str, chunk_size: int):
        num = 0
        db.session.query(Streets).delete()
        for chunk in self.get_streets_data_chunks(url=url, chunk_size=chunk_size):
            db.session.bulk_insert_mappings(Streets, chunk)
            num += len(chunk)
        db.session.commit()
        logging.info(f"{num} records written to Streets table.")


def parse(chunk_size=CHUNK_SIZE):
    instance = UpdateStreetsFromCSB()
    res = instance.get_cbs_streets_download_url()
    instance.import_street_file_into_db(res, chunk_size)


if __name__ == "__main__":
    parse()
