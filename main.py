#!/usr/bin/env python
import argparse
import logging
import os
import re
import sys

import click

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.DEBUG,
    datefmt="%Y-%m-%d %H:%M:%S",
)

def valid_date(date_string):
    date_input_format = "%d-%m-%Y"
    date_input_format_alt = "%Y-%m-%dT%H:%M"
    from datetime import datetime

    try:
        return datetime.strptime(date_string, date_input_format)
    except ValueError:
        try:
            return datetime.strptime(date_string, date_input_format_alt)
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
    from anyway.app_and_db import app

    logging.basicConfig(
        format="%(asctime)s %(levelname)-8s %(message)s",
        level=logging.DEBUG,
        datefmt="%Y-%m-%d %H:%M:%S",
    )

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
    from anyway.parsers import news_flash

    if not source:
        source = None
    if not news_flash_id:
        news_flash_id = None
    return news_flash.update_all_in_db(source, news_flash_id)


@update_news_flash.command()
def remove_duplicate_news_flash_rows():
    from anyway.parsers import news_flash_db_adapter

    news_flash_db_adapter.init_db().remove_duplicate_rows()


@cli.group()
def process():
    pass


@process.command()
@click.option("--batch_size", type=int, default=5000)
@click.option("--load_start_year", type=str, default=None)
@click.option("--source", type=str, default="s3")
def cbs(batch_size, load_start_year, source):
    from anyway.parsers.cbs.executor import main

    return main(batch_size=batch_size, load_start_year=load_start_year, source=source)


@process.command()
def news_flash():
    from anyway.parsers.news_flash import scrape_all

    return scrape_all()


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
@click.argument(
    "schools_description_filepath",
    type=str,
    default="static/data/schools/schools_description_2020.xlsx",
)
@click.argument(
    "schools_coordinates_filepath",
    type=str,
    default="static/data/schools/schools_coordinates_2020.xlsx",
)
@click.option("--batch_size", type=int, default=5000)
def schools_with_description_2020(
    schools_description_filepath, schools_coordinates_filepath, batch_size
):
    from anyway.parsers.schools_with_description_2020 import parse

    return parse(
        schools_description_filepath=schools_description_filepath,
        schools_coordinates_filepath=schools_coordinates_filepath,
        batch_size=batch_size,
    )


@process.command()
@click.option(
    "--start_date", default="01-07-2017", type=valid_date, help="The Start Date - format DD-MM-YYYY"
)
@click.option(
    "--end_date", default="30-06-2022", type=valid_date, help="The End Date - format DD-MM-YYYY"
)
@click.option("--distance", default=0.5, help="float In KM. Default is 0.5 (500m)", type=float)
@click.option("--batch_size", type=int, default=5000)
def injured_around_schools_2022(start_date, end_date, distance, batch_size):
    from anyway.parsers.injured_around_schools_2022 import parse
    return parse(start_date=start_date, end_date=end_date, distance=distance, batch_size=batch_size)


@process.command()
@click.option(
    "--from_s3",
    "-f",
    is_flag=True,
    help="get the data from files, instead of waze api",
)
@click.option(
    "--start_date", default="01-01-2019", type=valid_date, help="The Start Date - format DD-MM-YYYY"
)
@click.option(
    "--end_date", default="01-01-2020", type=valid_date, help="The End Date - format DD-MM-YYYY"
)
def waze_data(from_s3, start_date, end_date):
    """
    Get waze data from existing files or from waze api.
    Examples for running the script:

     - For getting data from waze RTS HTTP API, run:
       python -m main process waze-data

     - For getting data from the S3 stored json files, run (change the start and end date as you need):
       python -m main process waze-data --from_s3 --start_date=01-01-2020 --end_date=01-01-2020
    """

    from anyway.parsers.waze.waze_data_parser import ingest_waze_from_files, ingest_waze_from_api

    if from_s3:
        return ingest_waze_from_files(
            bucket_name="anyway-hasadna.appspot.com", start_date=start_date, end_date=end_date
        )
    else:
        return ingest_waze_from_api()


@process.command()
@click.argument("filename", type=str, default="static/data/embedded_reports/embedded_reports.csv")
def embedded_reports(filename):
    from anyway.parsers.embedded_reports import parse

    return parse(filename)


@process.command()
@click.option(
    "--update",
    "update",
    is_flag=True,
    help="Recalculates the cache (default is False)",
    default=False,
)
@click.option(
    "--no_info", "info", is_flag=True, help="Prints info on cache (default is True)", default=True
)
def infographics_data_cache(info, update):
    """Will refresh the infographics data cache"""
    from anyway.parsers.infographics_data_cache_updater import main

    return main(update=update, info=info)


@process.command()
def infographics_data_cache_for_road_segments():
    """Will refresh the infographics data cache"""
    from anyway.parsers.infographics_data_cache_updater import main_for_road_segments

    return main_for_road_segments()


@process.group()
def cache():
    pass


@cache.command()
def update_street():
    """Update street cache"""
    from anyway.parsers.infographics_data_cache_updater import main_for_street

    main_for_street()


@cache.command()
def update_road_segments():
    """Update road segments cache"""
    from anyway.parsers.infographics_data_cache_updater import main_for_road_segments

    return main_for_road_segments()


@process.command()
@click.argument("filename", type=str, default="static/data/casualties/casualties_costs.csv")
def update_casualties_costs(filename):
    from anyway.parsers.casualties_costs import parse

    return parse(filename)


@cli.group()
def preprocess():
    pass


@preprocess.command()
@click.option("--path", type=str)
def preprocess_cbs(path):
    from anyway.parsers.cbs.preprocessing_cbs_files import update_cbs_files_names

    return update_cbs_files_names(path)


@cli.group()
def create_tables():
    pass


@create_tables.command()
def create_cbs_tables():
    from anyway.parsers.cbs.executor import create_tables

    return create_tables()


@create_tables.command()
@click.option(
    "--file-name",
    type=str,
    help="csv file to load from. Default is static/data/cities.csv",
    default="%s/static/data/cities.csv" % os.path.abspath(os.path.dirname(__file__)),
)
def update_cities_table(file_name):
    from anyway.parsers.cbs.preprocessing_cbs_files import load_cities_data

    return load_cities_data(file_name=file_name)


@cli.group()
def update_dictionary_tables():
    pass


@update_dictionary_tables.command()
@click.option("--path", type=str, default="static/data/cbs")
def update_cbs(path):
    from anyway.parsers.cbs.executor import update_dictionary_tables

    return update_dictionary_tables(path)


@cli.group()
def truncate_dictionary_tables():
    pass


@truncate_dictionary_tables.command()
@click.option("--path", type=str)
def truncate_cbs(path):
    from anyway.parsers.cbs.executor import truncate_dictionary_tables

    return truncate_dictionary_tables(path)


@cli.command()
@click.argument("identifiers", nargs=-1)
def load_discussions(identifiers):
    from anyway.models import DiscussionMarker
    from anyway.app_and_db import db

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
            logging.info(f"Added: {identifier}")
        except Exception as e:
            db.session.rollback()
            logging.warning(f"Failed: {identifier} {e}")


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


@scripts.command()
def test_airflow():
    print('my print')
    logging.info('info log')
    logging.warning('warning log')
    logging.debug('debug log')


@scripts.command()
def importemail():
    from anyway.parsers.cbs.importmail_cbs import main

    return main()


if __name__ == "__main__":
    cli(sys.argv[1:])  # pylint: disable=too-many-function-args
