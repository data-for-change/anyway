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
@click.option('--debug-js', is_flag=True, help="Don't minify the JavaScript files")
def testserver(open_server, debug_js):
    from anyway import app
    from anyway.parsers import united
    from apscheduler.scheduler import Scheduler

    sched = Scheduler()

    @sched.interval_schedule(hours=12)
    def scheduled_import(): # pylint: disable=unused-variable
        united.main()
    sched.start()

    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s')

    if debug_js:
        app.config['ASSETS_DEBUG'] = True

    default_host = '0.0.0.0' if open_server else '127.0.0.1'
    app.run(debug=True, host=os.getenv('IP', default_host),
            port=int(os.getenv('PORT', 5000)))


@cli.group()
def process():
    pass


@process.command()
@click.option('--specific_folder', is_flag=True, default=False)
@click.option('--delete_all', is_flag=True)
@click.option('--path', type=str, default="static/data/cbs")
@click.option('--batch_size', type=int, default=10000)

def cbs(specific_folder, delete_all, path, batch_size):
    from anyway.parsers.cbs import main

    return main(specific_folder=specific_folder, delete_all=delete_all, path=path,
                batch_size=batch_size)

@process.command()
@click.option('--specific_folder', is_flag=True, default=False)
@click.option('--delete_all', is_flag=True)
@click.option('--path', type=str, default="static/data/cbs_vehicles_registered")
def registered_vehicles(specific_folder, delete_all, path):
    from anyway.parsers.registered import main

    return main(specific_folder=specific_folder, delete_all=delete_all, path=path)


@process.command()
@click.option('--light', is_flag=True, help='Import without downloading any new files')
@click.option('--username', default='')
@click.option('--password', default='')
@click.option('--lastmail', is_flag=True)
def united(light, username, password, lastmail):
    from anyway.parsers.united import main

    return main(light=light, username=username, password=password, lastmail=lastmail)


@process.command()
@click.argument("filename")
def rsa(filename):
    from anyway.parsers.rsa import parse

    return parse(filename)


@cli.command()
@click.argument('identifiers', nargs=-1)
def load_discussions(identifiers):
    from anyway.models import DiscussionMarker
    from flask.ext.sqlalchemy import SQLAlchemy
    from anyway.utilities import init_flask

    app = init_flask()
    db = SQLAlchemy(app)

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
            db.session.add(marker)
            db.session.commit()
            logging.info("Added:  " + identifier)
        except Exception as e:
            db.session.rollback()
            logging.warn("Failed: " + identifier + ": " + e)


if __name__ == '__main__':
    cli(sys.argv[1:]) # pylint: disable=too-many-function-args
