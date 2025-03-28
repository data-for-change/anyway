from typing import List, Dict, Optional
from anyway.models import City
from anyway.app_and_db import db
from anyway.views.safety_data import sd_utils as sdu

GB = "gb"
GB2 = "gb2"


class CityQuery:
    def get_data(self) -> List[Dict[str, Optional[str]]]:
        vals = sdu.get_params()
        if len(vals) == 0:
            query = db.session.query(
                City.yishuv_symbol,
                City.heb_name,
                City.eng_name
                )
            data = query.all()
            res = [{"_id": x.yishuv_symbol, "name_he": x.heb_name, "name_en": x.eng_name} for x in data]
            return res
        if "yishuv_symbol" in vals:
            val = vals["yishuv_symbol"][0]
            query = db.session.query(City).filter(City.yishuv_symbol == val)
        elif "name_he" in vals:
            val = vals["name_he"][0]
            query = db.session.query(City).filter(City.heb_name == val)
        else:
            raise ValueError(f"Missing 'yishuv_symbol' or 'name_he' in params:{vals}")
        data = query.first()
        if data is None:
            raise ValueError(f"City not found for {vals}", 404)
        res = {
            "_id": data.yishuv_symbol,
            "name": data.heb_name,
            "name_he": data.heb_name,
            "name_en": data.eng_name,
            "population": data.population,
            "id_osm": data.id_osm,
            "lat": data.lat,
            "lon": data.lon,
        }
        return [res]
