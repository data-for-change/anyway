class Constants(object):

    # constants that used in javascript and python
    MINIMAL_ZOOM = 17

    MARKER_TYPE_ACCIDENT = 1
    MARKER_TYPE_DISCUSSION = 2

    CBS_ACCIDENT_TYPE_1_CODE = 1
    UNITED_HATZALA_CODE = 2
    CBS_ACCIDENT_TYPE_3_CODE = 3
    RSA_PROVIDER_CODE = 4

    HIGHLIGHT_TYPE_USER_SEARCH = 1
    HIGHLIGHT_TYPE_USER_GPS = 2

    BIKE_ACCIDENTS = 21

    VEHICLE_TYPE_BIKE = 15

    INVOLVED_TYPE_DRIVER_UNHARMED = 1

    AGE_GROUPS_NUMBER = 18

    ALL_AGE_GROUPS_LIST = list(range(1, AGE_GROUPS_NUMBER + 1)) + [99]

    # other global constants (python only)

    def __setattr__(self, *_):
        """
        blocking changes in attributes
        """
        pass

    def to_dict(self):
        return {a: getattr(self, a) for a in dir(self) if not a.startswith('__') and not callable(getattr(self,a))}

CONST = Constants()

