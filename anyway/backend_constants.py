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

    # This is a type for the field 'injury_severity' in the table 'involved_markers_hebrew'
    class InjurySeverity:
        DEAD = 1
        SEVERE = 2
        LIGHT = 3

    # This is a type for the 'accident_severity' table field name
    class AccidentSeverity:
        FATAL = 1
        SEVERE = 2
        LIGHT = 3

    class AccidentType:
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

    class DriverType:
        PROFESSIONAL_DRIVER = 1
        PRIVATE_VEHICLE_DRIVER = 2
        OTHER_DRIVER = 3

    # This class should be correlated with the Roles table
    class Roles2Names:
        Admins = "admins"

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
        "https://anyway-infographics-staging.web.app/*",
        "https://anyway-infographics.web.app/*",
        "https://www.anyway.co.il/*",
        "https://anyway-infographics-demo.web.app/*",
    ]

    ANYWAY_CORS_SITE_LIST_DEV = ANYWAY_CORS_SITE_LIST_PROD + [
        "https://dev.anyway.co.il/*",
        "http://localhost:3000/*",
        "https://localhost:3000/*",
        "http://127.0.0.1:3000/*",
        "https://127.0.0.1:3000/*",
    ]


BE_CONST = BackEndConstants()
