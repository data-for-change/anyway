from enum import Enum
from typing import List
from flask_babel import _


class BackEndConstants(object):
    MARKER_TYPE_ACCIDENT = 1
    MARKER_TYPE_DISCUSSION = 2

    CBS_ACCIDENT_TYPE_1_CODE = 1
    UNITED_HATZALA_CODE = 2
    CBS_ACCIDENT_TYPE_3_CODE = 3
    RSA_PROVIDER_CODE = 4

    BIKE_ACCIDENTS = 21

    AGE_GROUPS_NUMBER = 18

    ALL_AGE_GROUPS_LIST = list(range(1, AGE_GROUPS_NUMBER + 1)) + [99]

    # This class should be correlated with the Roles table
    class Roles2Names(Enum):
        Admins = "admins"
        Or_yarok = "or_yarok"
        Authenticated = "authenticated"

    # This is a type for the 'road_type' table field name
    ROAD_TYPE_NOT_IN_CITY_IN_INTERSECTION = 3
    ROAD_TYPE_NOT_IN_CITY_NOT_IN_INTERSECTION = 4
    NON_CITY_ROAD_TYPES = [
        ROAD_TYPE_NOT_IN_CITY_IN_INTERSECTION,
        ROAD_TYPE_NOT_IN_CITY_NOT_IN_INTERSECTION,
    ]

    # other global constants (python only)
    DEFAULT_NUMBER_OF_YEARS_AGO = 5

    # years ago to store in cache
    INFOGRAPHICS_CACHE_YEARS_AGO = [1, 3, 5, 8]
    SOURCE_MAPPING = {"walla": "וואלה", "twitter": "מד״א", "ynet": "ynet"}

    UNKNOWN = "UNKNOWN"
    DEFAULT_REDIRECT_URL = "https://anyway-infographics.web.app/"
    ANYWAY_CORS_SITE_LIST_PROD = [
        "https://anyway-infographics-staging.web.app",
        "https://anyway-infographics.web.app",
        "https://www.anyway.co.il",
        "https://anyway-infographics-demo.web.app",
        "https://media.anyway.co.il",
        "https://dev.anyway.co.il",
    ]

    ANYWAY_CORS_SITE_LIST_DEV = ANYWAY_CORS_SITE_LIST_PROD + [
        "https://dev.anyway.co.il",
        "http://localhost:3000",
        "https://localhost:3000",
        "http://127.0.0.1:3000",
        "https://127.0.0.1:3000",
    ]

    class ResolutionCategories(Enum):
        REGION = "מחוז"
        DISTRICT = "נפה"
        CITY = "עיר"
        STREET = "רחוב"
        URBAN_JUNCTION = "צומת עירוני"
        SUBURBAN_ROAD = "כביש בינעירוני"
        SUBURBAN_JUNCTION = "צומת בינעירוני"
        OTHER = "אחר"

    SUPPORTED_RESOLUTIONS: List[ResolutionCategories] = [
        ResolutionCategories.STREET,
        ResolutionCategories.SUBURBAN_ROAD,
    ]

    class Source(Enum):
        @classmethod
        def _missing_(cls, value):
            for member in cls:
                if member.value == value.lower():
                    return member

        YNET = "ynet"
        WALLA = "walla"
        TWITTER = "twitter"

    SUPPORTED_SOURCES: List[Source] = [Source.YNET, Source.WALLA, Source.TWITTER]

    # If in the future there will be a number of organizations or a need for a dynamic setting change, move this
    # data to a table in the DB.
    OR_YAROK_WIDGETS = [
        "accident_count_by_severity",
        "most_severe_accidents_table",
        "most_severe_accidents",
        "vision_zero_2_plus_1",
        "head_on_collisions_comparison",
    ]

    LKEY = "label_key"
    VAL = "value"
    SERIES = "series"


try:
    _("killed")
    _("severe injured")
    _("light injured")
except NameError:
    pass
