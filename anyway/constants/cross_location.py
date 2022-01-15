from enum import Enum


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
