from enum import Enum
from typing import List

from anyway.constants.cross_location import CrossLocation


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
