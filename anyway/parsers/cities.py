import requests
import json
from typing import Iterable, Dict, Any, List
from anyway.models import City
from anyway.app_and_db import db
import logging

DATA_GOV_CITIES_RESOURCES_URL = "https://data.gov.il/dataset/citiesandsettelments"
DATA_GOV_CITIES_RESOURCES_ID = "8f714b6f-c35c-4b40-a0e7-547b675eee0e"
DATA_GOV_CITY_POP_RESOURCES_ID = "64edd0ee-3d5d-43ce-8562-c336c24dbc1f"
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
POP_CITY_CODE = "סמל_ישוב"
POP_CITY_POP = "סהכ"
OVERPASS_OSP_API_URL = "https://overpass-api.de/api/interpreter?data=%5Bout%3Ajson%5D%5Btimeout%3A100%5D%3B%0Aarea%28id%3A3601473946%29-%3E.searchArea%3B%0A%0A%2F%2F%20Fetch%20all%20relevant%20places%0A%28%0A%20%20node%5B%22place%22~%22village%7Ctown%7Ccity%7CRegional%20Council%7CLocal%20Council%22%5D%28area.searchArea%29%3B%0A%29%3B%0A%0A%2F%2F%20Output%20the%20results%20with%20specified%20fields%0Aout%20body%3B%0A%3E%3B%0Aout%20skel%20qt%3B%0A"
CBS_OSM_FIELD_NAME_MAPPING = {
    "heb_name": ["name:he", "alt_name:he", "name:he1", "name:he2"],
    "eng_name": [
        "name:en",
        "alt_name:en",
    ],
}
CBS_OSM_FIELD_NAME_MAPPING["eng_name"].extend([f"name:en{i}" for i in range(1, 20)]),
TRANS = str.maketrans("", "", " '\"״-\\()")


def prep_for_comp(s: str) -> str:
    return s.translate(TRANS).lower()


class UpdateCitiesFromDataGov:
    def __init__(self):
        self.s = requests.Session()
        self.len_cities = 0
        self.len_city_pop = 0
        self.len_cities_osm = 0
        self.num_osm_mismatch = 0

    def get_cities_download_url(self):
        url = RESOURCE_DOWNLOAD_TEMPLATE.format(id=DATA_GOV_CITIES_RESOURCES_ID)
        return url

    def get_city_data(self, url: str) -> Iterable[List[Dict[str, Any]]]:
        heb_name_dict = {}
        eng_name_dict = {}
        city_pop_data = self.get_city_pop_data()
        self.len_city_pop = len(city_pop_data)
        r = self.s.get(url)
        if not r.ok:
            raise Exception(f"Could not get streets url. reason:{r.reason}:{r.status_code}")
        r.encoding = "utf-8"
        data = json.loads(r.text)
        logging.debug(f"read {len(data['result']['records'])} records from {url}.")
        for item in data["result"]["records"]:
            pop = city_pop_data.get(item[YISHUV_SYMBOL])
            city_entry = {
                "heb_name": item[CITY_NAME].lstrip().rstrip(),
                "yishuv_symbol": item[YISHUV_SYMBOL],
                "eng_name": item[CITY_NAME_EN].lstrip().rstrip(),
                "population": pop,
                # "napa": item[NAPA],
                # "municipal_stance": item[MUNICIPAL_STANCE],
            }
            if pop is None:
                logging.info(f"Population not found for city {item}")
            heb_name_dict[prep_for_comp(city_entry["heb_name"])] = city_entry
            eng_name_dict[prep_for_comp(city_entry["eng_name"])] = city_entry
            if city_entry["yishuv_symbol"] == 0:
                city_entry["heb_name"] = None
                city_entry["eng_name"] = None
        self.len_cities = len(heb_name_dict)
        self.add_osm_data(heb_name_dict, eng_name_dict)
        return heb_name_dict.values()

    def import_citis_into_db(self, url: str, chunk_size: int):
        db.session.query(City).delete()
        data = self.get_city_data(url)
        db.session.bulk_insert_mappings(City, data)
        db.session.commit()
        logging.info(
            f"{len(data)} records written to City table. {self.len_city_pop} population, "
            f"{self.len_cities_osm} OSM entries, {self.num_osm_mismatch} OSM mismatch."
        )

    def get_city_pop_data(self) -> Dict[int, int]:
        url = RESOURCE_DOWNLOAD_TEMPLATE.format(id=DATA_GOV_CITY_POP_RESOURCES_ID)
        r = self.s.get(url)
        if not r.ok:
            raise Exception(f"Could not get city population url. reason:{r.reason}:{r.status_code}")
        r.encoding = "utf-8"
        data = json.loads(r.text)
        records = data["result"]["records"]
        res = {x[POP_CITY_CODE]: x[POP_CITY_POP] for x in records}
        logging.debug(f"read {len(records)} records from {url}.")
        return res

    def add_osm_data(self, heb_name_dict: Dict[str, Any], eng_name_dict: Dict[str, Any]) -> None:
        max_retries = 10
        for attempt in range(max_retries):
            try:
                r = self.s.get(OVERPASS_OSP_API_URL)
                if not r.ok:
                    raise Exception(f"Could not get OSM data. reason:{r.reason}:{r.status_code}.")
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                logging.warning(f"Attempt {attempt + 1} failed: {e}. Retrying...")

        r.encoding = "utf-8"
        data = json.loads(r.text)
        records = data["elements"]
        self.len_cities_osm = len(records)
        for r in records:
            found = list(
                filter(
                    lambda x: x, [heb_name_dict.get(prep_for_comp(x)) for x in r["tags"].values()]
                )
            ) or list(
                filter(
                    lambda x: x, [eng_name_dict.get(prep_for_comp(x)) for x in r["tags"].values()]
                )
            )
            cbs_record = found[0] if found else None
            if cbs_record is not None:
                cbs_record["id_osm"] = r["id"]
                cbs_record["lat"] = r["lat"]
                cbs_record["lon"] = r["lon"]
            else:
                self.num_osm_mismatch += 1
                logging.debug(f"Not found CBS record for OSM: {r['id']},{r['tags']}")


def parse(chunk_size=CHUNK_SIZE):
    instance = UpdateCitiesFromDataGov()
    res = instance.get_cities_download_url()
    instance.import_citis_into_db(res, chunk_size)


if __name__ == "__main__":
    parse()
