from anyway import utilities
from flask_sqlalchemy import SQLAlchemy
import flask_restx
from http import HTTPStatus

from anyway.backend_constants import BE_CONST
from anyway.config import SERVER_ENV


class FlexRootApi(flask_restx.Api):
    def __init__(self, inner_app, **kwargs):
        self.render_root_method = None
        super().__init__(inner_app, **kwargs)

    def render_root(self):
        if self.render_root_method is not None:
            return self.render_root_method()
        else:
            self.abort(HTTPStatus.NOT_FOUND)

    def set_render_root_function(self, func):
        self.render_root_method = func


app = utilities.init_flask()
db = SQLAlchemy(app)
api = FlexRootApi(app, doc="/swagger")


def get_cors_config() -> dict:
    cors_site_list = BE_CONST.ANYWAY_CORS_SITE_LIST_PROD
    if SERVER_ENV == "dev":
        cors_site_list = BE_CONST.ANYWAY_CORS_SITE_LIST_DEV

    return {
        r"/location-subscription": {"origins": "*"},
        r"/report-problem": {"origins": "*"},
        r"/api/infographics-data": {"origins": "*"},
        r"/api/infographics-data-by-location": {"origins": "*"},
        r"/api/gps-to-location": {"origins": "*"},
        r"/api/news-flash": {"origins": "*"},
        r"/api/news-flash-v2": {"origins": "*"},
        r"/api/embedded-reports": {"origins": "*"},
        r"/authorize/*": {"origins": cors_site_list, "supports_credentials": True},
        r"/callback/*": {"origins": cors_site_list, "supports_credentials": True},
        r"/user/*": {"origins": "*"},
        r"/logout": {"origins": cors_site_list, "supports_credentials": True},
    }
