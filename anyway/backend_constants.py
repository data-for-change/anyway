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

    AGE_GROUPS_NUMBER = 18

    ALL_AGE_GROUPS_LIST = list(range(1, AGE_GROUPS_NUMBER + 1)) + [99]

    # This is a type for the 'accident_severity' table field name
    ACCIDENT_SEVERITY_DEADLY = 1

    # This is a type for the 'road_type' table field name
    ROAD_TYPE_NOT_IN_CITY_NOT_IN_INTERSECTION = 4

    # other global constants (python only)
    DEFAULT_NUMBER_OF_YEARS_AGO = 5

    # years ago to store in cache
    INFOGRAPHICS_CACHE_YEARS_AGO = [1, 3, 5, 8]
    SOURCE_MAPPING = {"walla": "וואלה", "twitter": "מד״א", "ynet": "ynet"}

    UNKNOWN = "UNKNOWN"


BE_CONST = BackEndConstants()
