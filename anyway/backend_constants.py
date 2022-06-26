from enum import Enum
from typing import List, Iterable

try:
    from flask_babel import _
except ImportError:
    pass
# noinspection PyProtectedMember


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
    TOTAL = "total"
    SERIES = "series"


BE_CONST = BackEndConstants()


class LabeledCode(Enum):
    def get_label(self) -> str:
        return type(self).labels()[self]

    @classmethod
    def codes(cls: Iterable) -> List[int]:
        if isinstance(cls, Iterable):
            return [a.value for a in cls]
        else:
            raise NotImplementedError(f"{cls}: needs to be derived from Enum")

    @classmethod
    def labels(cls):
        return {}


# This is a type for the field 'injury_severity' in the table 'involved_markers_hebrew'
class InjurySeverity(LabeledCode):
    KILLED = 1
    SEVERE_INJURED = 2
    LIGHT_INJURED = 3

    @classmethod
    def labels(cls):
        return {
            InjurySeverity.KILLED: "killed",
            InjurySeverity.SEVERE_INJURED: "severe injured",
            InjurySeverity.LIGHT_INJURED: "light injured",
        }


try:
    _("killed")
    _("severe injured")
    _("light injured")
except NameError:
    pass


# This is a type for the 'accident_severity' table field name
class AccidentSeverity(LabeledCode):
    FATAL = 1
    SEVERE = 2
    LIGHT = 3

    @classmethod
    def labels(cls):
        return {
            AccidentSeverity.FATAL: "fatal",
            AccidentSeverity.SEVERE: "severe",
            AccidentSeverity.LIGHT: "light",
        }


class AccidentType(LabeledCode):
    PEDESTRIAN_INJURY = 1
    COLLISION_OF_FRONT_TO_SIDE = 2
    COLLISION_OF_FRONT_TO_REAR_END = 3
    COLLISION_OF_SIDE_TO_SIDE_LATERAL = 4
    HEAD_ON_FRONTAL_COLLISION = 5
    COLLISION_WITH_A_STOPPED_NON_PARKED_VEHICLE = 6
    COLLISION_WITH_A_PARKED_VEHICLE = 7
    COLLISION_WITH_AN_INANIMATE_OBJECT = 8
    SWERVING_OFF_THE_ROAD_OR_ONTO_THE_PAVEMENT = 9
    OVERTURNED_VEHICLE = 10
    SKID = 11
    INJURY_OF_A_PASSENGER_IN_A_VEHICLE = 12
    A_FALL_FROM_A_MOVING_VEHICLE = 13
    FIRE = 14
    OTHER = 15
    COLLISION_OF_REAR_END_TO_FRONT = 17
    COLLISION_OF_REAR_END_TO_SIDE = 18
    COLLISION_WITH_AN_ANIMAL = 19
    DAMAGE_CAUSED_BY_A_FALLING_LOAD_OFF_A_VEHICLE = 20

    @classmethod
    def labels(cls):
        return {
            AccidentType.PEDESTRIAN_INJURY: "Pedestrian injury",
            AccidentType.COLLISION_OF_FRONT_TO_SIDE: "Collision of front to side",
            AccidentType.COLLISION_OF_FRONT_TO_REAR_END: "Collision of front to rear-end",
            AccidentType.COLLISION_OF_SIDE_TO_SIDE_LATERAL: "Collision of side to side (lateral)",
            AccidentType.HEAD_ON_FRONTAL_COLLISION: "Head-on frontal collision",
            AccidentType.COLLISION_WITH_A_STOPPED_NON_PARKED_VEHICLE: "Collision with a stopped non-parked vehicle",
            AccidentType.COLLISION_WITH_A_PARKED_VEHICLE: "Collision with a parked vehicle",
            AccidentType.COLLISION_WITH_AN_INANIMATE_OBJECT: "Collision with an inanimate object",
            AccidentType.SWERVING_OFF_THE_ROAD_OR_ONTO_THE_PAVEMENT: "Swerving off the road or onto the pavement",
            AccidentType.OVERTURNED_VEHICLE: "Overturned vehicle",
            AccidentType.SKID: "Skid",
            AccidentType.INJURY_OF_A_PASSENGER_IN_A_VEHICLE: "Injury of a passenger in a vehicle",
            AccidentType.A_FALL_FROM_A_MOVING_VEHICLE: "A fall from a moving vehicle",
            AccidentType.FIRE: "Fire",
            AccidentType.OTHER: "Other",
            AccidentType.COLLISION_OF_REAR_END_TO_FRONT: "Collision of rear-end to front",
            AccidentType.COLLISION_OF_REAR_END_TO_SIDE: "Collision of rear-end to side",
            AccidentType.COLLISION_WITH_AN_ANIMAL: "Collision with an animal",
            AccidentType.DAMAGE_CAUSED_BY_A_FALLING_LOAD_OFF_A_VEHICLE: "Damage caused by a falling load off a vehicle",
        }

    def is_collision(self) -> bool:
        return self in [
            self.COLLISION_OF_FRONT_TO_SIDE,
            self.COLLISION_OF_FRONT_TO_REAR_END,
            self.COLLISION_OF_SIDE_TO_SIDE_LATERAL,
            self.HEAD_ON_FRONTAL_COLLISION,
            self.COLLISION_WITH_A_STOPPED_NON_PARKED_VEHICLE,
            self.COLLISION_WITH_A_PARKED_VEHICLE,
            self.COLLISION_WITH_AN_INANIMATE_OBJECT,
            self.COLLISION_OF_REAR_END_TO_FRONT,
            self.COLLISION_OF_REAR_END_TO_SIDE,
            self.COLLISION_WITH_AN_ANIMAL,
        ]


class DriverType(LabeledCode):
    PROFESSIONAL_DRIVER = 1
    PRIVATE_VEHICLE_DRIVER = 2
    OTHER_DRIVER = 3

    @classmethod
    def labels(cls):
        return {
            DriverType.PROFESSIONAL_DRIVER: "professional_driver",
            DriverType.PRIVATE_VEHICLE_DRIVER: "private_vehicle_driver",
            DriverType.OTHER_DRIVER: "other_driver",
        }


class InjuredType(LabeledCode):
    PEDESTRIAN = 1
    DRIVER_FOUR_WHEELS_AND_ABOVE = 2
    PASSENGER_FOUR_WHEELS_AND_ABOVE = 3
    DRIVER_MOTORCYCLE = 4
    PASSENGER_MOTORCYCLE = 5
    DRIVER_BICYCLE = 6
    PASSENGER_BICYCLE = 7
    DRIVER_UNKNOWN_VEHICLE = 8
    PASSENGER_UNKNOWN_VEHICLE = 9

    @classmethod
    def labels(cls):
        return {
            InjuredType.PEDESTRIAN: "Pedestrian",
            InjuredType.DRIVER_FOUR_WHEELS_AND_ABOVE: "Driver of a vehicle with 4 wheel or more",
            InjuredType.PASSENGER_FOUR_WHEELS_AND_ABOVE: "Passenger of a vehicle with 4 wheel or more",
            InjuredType.DRIVER_MOTORCYCLE: "Motorcycle driver",
            InjuredType.PASSENGER_MOTORCYCLE: "Motorcycle passenger",
            InjuredType.DRIVER_BICYCLE: "Bicycle driver",
            InjuredType.PASSENGER_BICYCLE: "Bicycle passenger",
            InjuredType.DRIVER_UNKNOWN_VEHICLE: "Driver of an unknown vehicle",
            InjuredType.PASSENGER_UNKNOWN_VEHICLE: "Passenger of an unknown vehicle",
        }


class CrossLocation(Enum):
    UNKNOWN = 9
    OUTNEAR = 1
    OUTFAR = 2
    YESNONE = 3
    YESLIGHT = 4

    @classmethod
    def labels(cls):
        return {
            CrossLocation.UNKNOWN: "Location unknown",
            CrossLocation.OUTNEAR: "Near the intersection, outside the crosswalk",
            CrossLocation.OUTFAR: "Away from the intersection, outside the crosswalk",
            CrossLocation.YESNONE: "In the crosswalk, without a crossing light",
            CrossLocation.YESLIGHT: "In the crosswalk, with a crossing light",
        }


class CrossCategory(Enum):
    UNKNOWN = 0
    NONE = 1
    CROSSWALK = 2

    def get_codes(self) -> List[int]:
        """returns CrossLocation codes of category"""
        category_cross_locations = {
            CrossCategory.UNKNOWN: [CrossLocation.UNKNOWN],
            CrossCategory.NONE: [CrossLocation.OUTFAR, CrossLocation.OUTNEAR],
            CrossCategory.CROSSWALK: [CrossLocation.YESLIGHT, CrossLocation.YESNONE],
        }
        return list(map(lambda x: x.value, category_cross_locations[self]))


class InvolvedType(Enum):
    # this is defined based on https://docs.google.com/spreadsheets/d/1qaVV7NKXVYNmnxKZ4he2MKZDAjWPHiHfq-U5dcNZM5k/edit#gid=266079360
    DRIVER = 1
    INJURED_DRIVER = 2
    INJURED = 3