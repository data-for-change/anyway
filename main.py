#!/usr/bin/env python
import click
import logging
import os
import re
import sys


@click.group()
def cli():
    pass


@cli.command()
@click.option('--open', 'open_server', is_flag=True,
              help='Open the server for communication from outside', default=False)
def testserver(open_server):
    from anyway import app, united
    from apscheduler.scheduler import Scheduler

    sched = Scheduler()

    @sched.interval_schedule(hours=12)
    def scheduled_import():
        united.main()
    sched.start()

    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s')

    default_host = '0.0.0.0' if open_server else '127.0.0.1'
    app.run(debug=True, host=os.getenv('IP', default_host),
            port=int(os.getenv('PORT', 5000)))


@cli.command()
def init_db():
    from anyway.models import init_db
    init_db()


@cli.command()
@click.option('--specific_folder', is_flag=True, default=False)
@click.option('--delete_all', is_flag=True)
@click.option('--path', type=str, default="static/data/lms")
@click.option('--batch_size', type=int, default=100)
@click.option('--provider_code', type=int)
def process_data(specific_folder, delete_all, path, batch_size, provider_code):
    from anyway.process import main

    return main(specific_folder=specific_folder, delete_all=delete_all, path=path,
                batch_size=batch_size, provider_code=provider_code)


@cli.command()
@click.option('--light', is_flag=True, help='Import without downloading any new files')
@click.option('--username', default='')
@click.option('--password', default='')
@click.option('--lastmail', is_flag=True)
def import_united_data(light, username, password, lastmail):
    from anyway.united import main

    return main(light=light, username=username, password=password, lastmail=lastmail)


@cli.command()
@click.argument('identifiers', nargs=-1)
def load_discussions(identifiers):
    from anyway.database import db_session
    from anyway.models import DiscussionMarker

    identifiers = identifiers or sys.stdin

    for identifier in identifiers:
        identifier = identifier.strip()
        m = re.match(r'\((\d+\.\d+),\s*(\d+\.\d+)\)', identifier)
        if not m:
            logging.error("Failed processing: " + identifier)
            continue
        (latitude, longitude) = m.group(1, 2)
        marker = DiscussionMarker.parse({
            'latitude': latitude,
            'longitude': longitude,
            'title': identifier,
            'identifier': identifier
        })
        try:
            db_session.add(marker)
            db_session.commit()
            logging.info("Added:  " + identifier)
        except Exception as e:
            db_session.rollback()
            logging.warn("Failed: " + identifier + ": " + e.message)


if __name__ == '__main__':
    cli(sys.argv[1:])
