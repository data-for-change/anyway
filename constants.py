class Constants(object):

    # constants that used in javascript and python
    MINIMAL_ZOOM = 16

    MARKER_TYPE_ACCIDENT = 1
    MARKER_TYPE_DISCUSSION = 2
    UNITED_HATZALA_CODE = 2

    HIGHLIGHT_TYPE_USER_SEARCH = 1
    HIGHLIGHT_TYPE_USER_GPS = 2

    # other global constants (python only)

    def __setattr__(self, *_):
        """
        blocking changes in attributes
        """
        pass

    def to_dict(self):
        return {a: getattr(self, a) for a in dir(self) if not a.startswith('__') and not callable(getattr(self,a))}

CONST = Constants()

