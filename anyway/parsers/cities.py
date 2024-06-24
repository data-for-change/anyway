import requests
import json
from typing import Iterable, Dict, Any, List
from anyway.models import City
from anyway.app_and_db import db
import logging

CBS_CITIES_RESOURCES_URL = "https://data.gov.il/dataset/citiesandsettelments"
CBS_CITIES_RESOURCES_ID = "8f714b6f-c35c-4b40-a0e7-547b675eee0e"
RESOURCE_NAME = "רשימת רחובות בישראל - מתעדכן"
BASE_GET_DATA_GOV = "https://data.gov.il/dataset/321"
RESOURCE_DOWNLOAD_TEMPLATE = (
    "https://data.gov.il/api/3/action/datastore_search?resource_id={id}&limit=100000"
)
FIELD_NAMES = {
    "yishuv_symbol": "city_code",
    "heb_name": "city_name_he",
    "eng_name": "city_name_en",
    "district": "region_code",
    "napa": "region_code",
    "municipal_stance": "Regional_Council_name",
}
CITY_CODE = "city_code"
CITY_NAME = "city_name_he"
CITY_NAME_EN = "city_name_en"
YISHUV_SYMBOL = "city_code"
MUNICIPAL_STANCE = "PIBA_bureau_code"
NAPA = "Regional_Council_code"
CHUNK_SIZE = 1000


class UpdateCitiesFromCSB:
    def __init__(self):
        self.s = requests.Session()

    def get_cbs_streets_download_url(self):
        url = RESOURCE_DOWNLOAD_TEMPLATE.format(id=CBS_CITIES_RESOURCES_ID)
        return url

    def get_city_data_chunks(self, url: str, chunk_size: int) -> Iterable[List[Dict[str, Any]]]:
        r = self.s.get(url)
        if not r.ok:
            raise Exception(f"Could not get streets url. reason:{r.reason}:{r.status_code}")
        r.encoding = "utf-8"
        data = json.loads(r.text)
        chunk = []
        logging.debug(f"read {len(data['result']['records'])} records from {url}.")
        for item in data["result"]["records"]:
            city_entry = {
                "heb_name": item[CITY_NAME],
                "yishuv_symbol": item[YISHUV_SYMBOL],
                "eng_name": item[CITY_NAME_EN],
                # "napa": item[NAPA],
                # "municipal_stance": item[MUNICIPAL_STANCE],
            }
            chunk.append(city_entry)
            if len(chunk) == chunk_size:
                yield chunk
                chunk = []
        if chunk:
            logging.debug(f"last chunk: {len(chunk)}.")
            yield chunk

    def import_citis_into_db(self, url: str, chunk_size: int):
        num = 0
        db.session.query(City).delete()
        for chunk in self.get_city_data_chunks(url=url, chunk_size=chunk_size):
            db.session.bulk_insert_mappings(City, chunk)
            num += len(chunk)
        db.session.commit()
        logging.info(f"{num} records written to City table.")


def parse(chunk_size=CHUNK_SIZE):
    instance = UpdateCitiesFromCSB()
    res = instance.get_cbs_streets_download_url()
    instance.import_citis_into_db(res, chunk_size)


if __name__ == "__main__":
    parse()
