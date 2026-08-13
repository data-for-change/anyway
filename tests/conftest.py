from threading import Thread
from time import sleep

import pytest
import requests
from urlobject import URLObject
from werkzeug.serving import make_server

from anyway.app_and_db import app, db
from anyway.models import City

# Minimal cbs_cities rows for tests that join City (name / cpop).
DEFAULT_TEST_CITIES = [
    {
        "yishuv_symbol": 5000,
        "heb_name": "תל אביב - יפו",
        "eng_name": "Tel Aviv - Yafo",
        "population": 500000,
    },
]


class ServerThread(Thread):
    def __init__(self):
        super(ServerThread, self).__init__()
        self.srv = make_server("127.0.0.1", 5000, app)
        self.ctx = app.app_context()
        self.ctx.push()

    def run(self):
        self.srv.serve_forever()

    def shutdown(self):
        self.srv.shutdown()


@pytest.fixture(scope="session")
def anyway_server():
    server_thread = ServerThread()
    server_thread.start()
    sleep(0.1)

    url = URLObject("http://127.0.0.1:5000")
    response = requests.get(url)
    response.raise_for_status()

    yield url

    server_thread.shutdown()


@pytest.fixture
def cbs_cities():
    """Ensure default cbs_cities rows exist; only remove rows this fixture inserted."""
    inserted_symbols = []
    with app.app_context():
        for city_data in DEFAULT_TEST_CITIES:
            symbol = city_data["yishuv_symbol"]
            exists = (
                db.session.query(City.yishuv_symbol)
                .filter(City.yishuv_symbol == symbol)
                .first()
            )
            if exists:
                continue
            db.session.add(City(**city_data))
            inserted_symbols.append(symbol)
        db.session.commit()
    yield DEFAULT_TEST_CITIES
    if not inserted_symbols:
        return
    with app.app_context():
        db.session.query(City).filter(City.yishuv_symbol.in_(inserted_symbols)).delete(
            synchronize_session=False
        )
        db.session.commit()
