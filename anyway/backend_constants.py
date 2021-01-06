class BackEndConstants(object):

    MARKER_TYPE_ACCIDENT = 1
    MARKER_TYPE_DISCUSSION = 2

    CBS_ACCIDENT_TYPE_1_CODE = 1
    UNITED_HATZALA_CODE = 2
    CBS_ACCIDENT_TYPE_3_CODE = 3
    RSA_PROVIDER_CODE = 4

    BIKE_ACCIDENTS = 21

    VEHICLE_TYPE_BIKE = 15

    PROFESSIONAL_DRIVER_VEHICLE_TYPES = [2, 3, 4, 5, 6, 7, 11, 12, 13, 14, 18, 24, 25]
    PRIVATE_DRIVER_VEHICLE_TYPES = [1, 8, 9, 10, 19]
    LIGHT_ELECTRIC_VEHICLE_TYPES = [21, 22, 23]
    OTHER_VEHICLES_TYPES = [15, 16, 17]

    # For percentage_accidents_by_car_type function
    CAR_VEHICLE_TYPES = [1, 12]
    LARGE_VEHICLE_TYPES = [25, 11, 4, 18, 6, 2, 3, 5, 13, 7, 24, 14]
    MOTORCYCLE_VEHICLE_TYPES = [8, 10, 19, 9]
    BICYCLE_AND_SMALL_MOTOR_VEHICLE_TYPES = [15, 21, 23]
    OTHER_VEHICLE_TYPES = [14, 17, 22, 16]

    AGE_GROUPS_NUMBER = 18

    ALL_AGE_GROUPS_LIST = list(range(1, AGE_GROUPS_NUMBER + 1)) + [99]

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


BE_CONST = BackEndConstants()
