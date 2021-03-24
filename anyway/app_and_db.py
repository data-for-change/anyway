from anyway import utilities
from flask_sqlalchemy import SQLAlchemy

from anyway.backend_constants import BE_CONST
from anyway.config import SERVER_ENV

app = utilities.init_flask()
db = SQLAlchemy(app)


def get_cors_config() -> dict:
    cors_site_list = BE_CONST.ANYWAY_CORS_SITE_LIST_PROD
    if SERVER_ENV == "dev":
        cors_site_list = BE_CONST.ANYWAY_CORS_SITE_LIST_DEV

    return {
        r"/location-subscription": {"origins": "*"},
        r"/report-problem": {"origins": "*"},
        r"/api/infographics-data": {"origins": "*"},
        r"/api/news-flash": {"origins": "*"},
        r"/api/embedded-reports": {"origins": "*"},
        r"/authorize/*": {"origins": cors_site_list, "supports_credentials": True},
        r"/callback/*": {"origins": cors_site_list, "supports_credentials": True},
        r"/user/info": {"origins": cors_site_list, "supports_credentials": True},
        r"/user/update": {"origins": cors_site_list, "supports_credentials": True},
        r"/logout": {"origins": cors_site_list, "supports_credentials": True},
    }
