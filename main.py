#!/usr/bin/env python
import argparse
import logging
import os
import re
import sys

import click


def valid_date(date_string):
    DATE_INPUT_FORMAT = "%d-%m-%Y"
    from datetime import datetime

    try:
        return datetime.strptime(date_string, DATE_INPUT_FORMAT)
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(date_string)
        raise argparse.ArgumentTypeError(msg)


@click.group()
def cli():
    pass


@cli.command()
@click.option(
    "--open",
    "open_server",
    is_flag=True,
    help="Open the server for communication from outside",
    default=False,
)
@click.option("--debug-js", is_flag=True, help="Don't minify the JavaScript files")
def testserver(open_server, debug_js):
    from anyway import app

    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(message)s")

    if debug_js:
        app.config["ASSETS_DEBUG"] = True

    default_host = "0.0.0.0" if open_server else "127.0.0.1"
    app.run(debug=True, host=os.getenv("IP", default_host), port=int(os.getenv("PORT", 5000)))


@cli.group()
def update_news_flash():
    pass


@update_news_flash.command()
@click.option("--source", default="", type=str)
@click.option("--news_flash_id", default="", type=str)
def update(source, news_flash_id):
    from anyway.parsers.news_flash_updater import main

    if not source:
        source = None
    if not news_flash_id:
        news_flash_id = None
    return main(source, news_flash_id)


@update_news_flash.command()
def remove_duplicate_news_flash_rows():
    from anyway.parsers import news_flash_db_adapter

    news_flash_db_adapter.init_db().remove_duplicate_rows()


@cli.group()
def process():
    pass


@process.command()
@click.option("--specific_folder", is_flag=True, default=False)
@click.option("--delete_all", is_flag=True)
@click.option("--path", type=str, default="static/data/cbs")
@click.option("--batch_size", type=int, default=5000)
@click.option("--delete_start_date", type=str, default=None)
@click.option("--load_start_year", type=str, default="2005")
@click.option("--from_email", is_flag=True, default=False)
@click.option("--username", default="")
@click.option("--password", default="")
@click.option("--email_search_start_date", type=str, default="")  # format - DD.MM.YYYY
def cbs(
    specific_folder,
    delete_all,
    path,
    batch_size,
    delete_start_date,
    load_start_year,
    from_email,
    username,
    password,
    email_search_start_date,
):
    from anyway.parsers.cbs import main

    return main(
        specific_folder=specific_folder,
        delete_all=delete_all,
        path=path,
        batch_size=batch_size,
        delete_start_date=delete_start_date,
        load_start_year=load_start_year,
        from_email=from_email,
        username=username,
        password=password,
        email_search_start_date=email_search_start_date,
    )


@process.command()
def news_flash():
    from anyway.parsers.scrape_flash_news import main
    return main()


@process.command()
@click.option("--specific_folder", is_flag=True, default=False)
@click.option("--delete_all", is_flag=True)
@click.option("--path", type=str, default="static/data/cbs_vehicles_registered")
def registered_vehicles(specific_folder, delete_all, path):
    from anyway.parsers.registered import main

    return main(specific_folder=specific_folder, delete_all=delete_all, path=path)


@process.command()
@click.option("--path", type=str, default="static/data/traffic_volume")
def traffic_volume(path):
    from anyway.parsers.traffic_volume import main

    return main(path)


@process.command()
@click.argument("filename")
def rsa(filename):
    from anyway.parsers.rsa import parse

    return parse(filename)


@process.command()
@click.argument("filename", type=str, default="static/data/segments/road_segments.xlsx")
def road_segments(filename):
    from anyway.parsers.road_segments import parse

    return parse(filename)


@process.command()
@click.argument("filepath", type=str, default="static/data/schools/schools.csv")
@click.option("--batch_size", type=int, default=5000)
def schools(filepath, batch_size):
    from anyway.parsers.schools import parse

    return parse(filepath=filepath, batch_size=batch_size)


@process.command()
@click.argument(
    "schools_description_filepath", type=str, default="static/data/schools/schools_description.xlsx"
)
@click.argument(
    "schools_coordinates_filepath", type=str, default="static/data/schools/schools_coordinates.xlsx"
)
@click.option("--batch_size", type=int, default=5000)
def schools_with_description(
    schools_description_filepath, schools_coordinates_filepath, batch_size
):
    from anyway.parsers.schools_with_description import parse

    return parse(
        schools_description_filepath=schools_description_filepath,
        schools_coordinates_filepath=schools_coordinates_filepath,
        batch_size=batch_size,
    )


@process.command()
@click.option(
    "--start_date", default="01-01-2014", type=valid_date, help="The Start Date - format DD-MM-YYYY"
)
@click.option(
    "--end_date", default="31-12-2018", type=valid_date, help="The End Date - format DD-MM-YYYY"
)
@click.option("--distance", default=0.5, help="float In KM. Default is 0.5 (500m)", type=float)
@click.option("--batch_size", type=int, default=5000)
def injured_around_schools(start_date, end_date, distance, batch_size):
    from anyway.parsers.injured_around_schools import parse

    return parse(start_date=start_date, end_date=end_date, distance=distance, batch_size=batch_size)


@process.command()
@click.option(
    "--start_date", default="01-01-2019", type=valid_date, help="The Start Date - format DD-MM-YYYY"
)
@click.option(
    "--end_date", default="01-01-2020", type=valid_date, help="The End Date - format DD-MM-YYYY"
)
def waze_data(start_date, end_date):
    from anyway.parsers.waze.waze_data_parser import waze_parser

    return waze_parser(
        bucket_name="anyway-hasadna.appspot.com", start_date=start_date, end_date=end_date
    )


@process.command()
@click.argument("filename", type=str, default="static/data/embedded_reports/embedded_reports.csv")
def embedded_reports(filename):
    from anyway.parsers.embedded_reports import parse

    return parse(filename)


@cli.group()
def preprocess():
    pass


@preprocess.command()
@click.option("--path", type=str)
def preprocess_cbs(path):
    from anyway.parsers.preprocessing_cbs_files import update_cbs_files_names

    return update_cbs_files_names(path)


@cli.group()
def create_views():
    pass


@create_views.command()
def cbs_views():
    from anyway.parsers.cbs import create_views

    return create_views()


@cli.group()
def update_dictionary_tables():
    pass


@update_dictionary_tables.command()
@click.option("--path", type=str, default="static/data/cbs")
def update_cbs(path):
    from anyway.parsers.cbs import update_dictionary_tables

    return update_dictionary_tables(path)


@cli.group()
def truncate_dictionary_tables():
    pass


@truncate_dictionary_tables.command()
@click.option("--path", type=str)
def truncate_cbs(path):
    from anyway.parsers.cbs import truncate_dictionary_tables

    return truncate_dictionary_tables(path)


@cli.command()
@click.argument("identifiers", nargs=-1)
def load_discussions(identifiers):
    from anyway.models import DiscussionMarker
    from flask_sqlalchemy import SQLAlchemy
    from anyway.utilities import init_flask

    app = init_flask()
    db = SQLAlchemy(app)

    identifiers = identifiers or sys.stdin

    for identifier in identifiers:
        identifier = identifier.strip()
        m = re.match(r"\((\d+\.\d+),\s*(\d+\.\d+)\)", identifier)
        if not m:
            logging.error("Failed processing: " + identifier)
            continue
        (latitude, longitude) = m.group(1, 2)
        marker = DiscussionMarker.parse(
            {
                "latitude": latitude,
                "longitude": longitude,
                "title": identifier,
                "identifier": identifier,
            }
        )
        try:
            db.session.add(marker)
            db.session.commit()
            logging.info("Added:  " + identifier)
        except Exception as e:
            db.session.rollback()
            logging.warn("Failed: " + identifier + ": " + e)


@cli.group()
def scripts():
    pass


@scripts.command()
@click.option(
    "--start_date", default="01-01-2013", type=valid_date, help="The Start Date - format DD-MM-YYYY"
)
@click.option(
    "--end_date", default="31-12-2017", type=valid_date, help="The End Date - format DD-MM-YYYY"
)
@click.option("--distance", default=0.5, help="float In KM. Default is 0.5 (500m)", type=float)
@click.option(
    "--output_path", default="output", help="output file of the results. Default is output.csv"
)
def accidents_around_schools(start_date, end_date, distance, output_path):
    from anyway.accidents_around_schools import main

    return main(
        start_date=start_date, end_date=end_date, distance=distance, output_path=output_path
    )


if __name__ == "__main__":
    cli(sys.argv[1:])  # pylint: disable=too-many-function-args
