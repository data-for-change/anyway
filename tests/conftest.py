import pytest
import requests
from anyway import app
from threading import Thread
from time import sleep
from urlobject import URLObject
from werkzeug.serving import make_server


class ServerThread(Thread):
    def __init__(self):
        super(ServerThread, self).__init__()
        self.srv = make_server('127.0.0.1', 5000, app)
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
