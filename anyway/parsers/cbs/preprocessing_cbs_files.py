import os
import logging
import pandas as pd
from anyway.app_and_db import db
from anyway.models import City, CityTemp

CBS_FILES_HEBREW = {
    "sadot": "Fields",
    "zmatim_ironiim": "IntersectUrban",
    "zmatim_lo_ironiim": "IntersectNonUrban",
    "rehev": "VehData",
    "milon": "Dictionary",
    "meoravim": "InvData",
    "klali": "AccData",
    "rechovot": "DicStreets",
}


def update_cbs_files_names(directory):
    files = sorted([path for path in os.listdir(directory)])
    for file in files:
        file_path = os.path.join(directory, file)
        for hebrew_file_name, english_file_name in CBS_FILES_HEBREW.items():
            if hebrew_file_name in file.lower() and english_file_name.lower() not in file.lower():
                os.rename(file_path, file_path.replace(".csv", "_" + english_file_name + ".csv"))


def get_accidents_file_data(directory):
    for file_path in os.listdir(directory):
        if file_path.endswith("{0}{1}".format(CBS_FILES_HEBREW["klali"], ".csv")):
            return os.path.join(directory, file_path)


# noinspection SpellCheckingInspection
def load_cities_data(file_name: str):
    logging.info(f"Loading {file_name} into {City.__tablename__} table.")
    column_names = [
        "heb_name",
        "yishuv_symbol",
        "eng_name",
        "district",
        "napa",
        "natural_zone",
        "municipal_stance",
        "metropolitan",
        "religion",
        "population",
        "other",
        "jews",
        "arab",
        "founded",
        "tzura",
        "irgun",
        "center",
        "altitude",
        "planning",
        "police",
        "year",
        "taatik",
    ]
    col_types = dict.fromkeys(["heb_name", "eng_name", "taatik"], lambda x: str(x) if x else None)
    col_types.update(
        dict.fromkeys(
            [
                "yishuv_symbol",
                "district",
                "napa",
                "natural_zone",
                "municipal_stance",
                "metropolitan",
                "religion",
                "population",
                "founded",
                "tzura",
                "irgun",
                "center",
                "altitude",
                "planning",
                "police",
                "year",
            ],
            lambda x: int(x) if x and x.isdigit() else 1,
        )
    )
    col_types.update(dict.fromkeys(["other", "jews", "arab"], lambda x: float(x) if x else 0.0001))
    cities = pd.read_csv(
        file_name, header=0, names=column_names, converters=col_types, encoding="utf-8"
    )
    cities_list = cities.to_dict(orient="records")
    logging.info(f"Read {len(cities_list)} from {file_name}")
    db.session.commit()
    db.session.execute("DROP table IF EXISTS cbs_cities_temp")
    db.session.execute("CREATE TABLE cbs_cities_temp AS TABLE cbs_cities with NO DATA")
    db.session.execute(CityTemp.__table__.insert(), cities_list)
    db.session.execute("TRUNCATE table cbs_cities")
    db.session.execute("INSERT INTO cbs_cities SELECT * FROM cbs_cities_temp")
    db.session.execute("DROP table cbs_cities_temp")
    db.session.commit()
    num_items = db.session.query(City).count()
    logging.info(f"num items in cities: {num_items}.")


if __name__ == "__main__":
    pass
