from typing import Union, List, Set, Container
from anyway.backend_constants import BE_CONST


class ResolutionFields:
    RC = BE_CONST.ResolutionCategories
    __required_fields = {
        "מחוז": ["region_hebrew"],
        "נפה": ["district_hebrew"],
        "עיר": ["yishuv_name"],
        "רחוב": ["yishuv_name", "street1_hebrew"],
        "צומת עירוני": ["yishuv_name", "street1_hebrew", "street2_hebrew"],
        "כביש בינעירוני": ["road1", "road_segment_id"],
        "צומת בינעירוני": [
            "non_urban_intersection",
            "non_urban_intersection_hebrew",
            "road1",
            "road2",
        ],
        "אחר": [
            "region_hebrew",
            "district_hebrew",
            "yishuv_name",
            "street1_hebrew",
            "street2_hebrew",
            "non_urban_intersection_hebrew",
            "road1",
            "road2",
            "road_segment_name",
            "road_segment_id",
        ],
    }
    __possible_fields = {
        "מחוז": __required_fields[RC.REGION.value],
        "נפה": __required_fields[RC.DISTRICT.value],
        "עיר": __required_fields[RC.CITY.value],
        "רחוב": __required_fields[RC.STREET.value],
        "צומת עירוני": __required_fields[RC.URBAN_JUNCTION.value],
        "כביש בינעירוני": ["road1", "road_segment_id", "road_segment_name"],
        "צומת בינעירוני": __required_fields[RC.SUBURBAN_JUNCTION.value],
        "אחר": __required_fields[RC.OTHER.value],
    }
    __all_fields = set()

    @classmethod
    def get_fields(cls, d: dict, res: Union[BE_CONST.ResolutionCategories, str]) -> List[str]:
        if isinstance(res, BE_CONST.ResolutionCategories):
            res = res.value
        if res in d:
            return d[res]
        else:
            raise ValueError(f"ResolutionFields:{res}: not a resolution")

    @classmethod
    def get_possible_fields(cls, res: Union[BE_CONST.ResolutionCategories, str]) -> List[str]:
        return cls.get_fields(cls.__possible_fields, res)

    @classmethod
    def get_required_fields(cls, res: Union[BE_CONST.ResolutionCategories, str]) -> List[str]:
        return cls.get_fields(cls.__required_fields, res)

    @classmethod
    def get_all_location_fields(cls) -> Set[str]:
        if not cls.__all_fields:
            for fields in cls.__possible_fields.values():
                cls.__all_fields.update(fields)
        return cls.__all_fields

    @classmethod
    def is_resolution_valid(cls, res: str) -> bool:
        return res in cls.__possible_fields

    @classmethod
    def get_supported_resolution_of_fields(cls, fields: Container[str]) -> List[str]:
        fields = set(fields)
        res = list(
            filter(
                lambda r: set(cls.get_required_fields(r)) <= fields, BE_CONST.SUPPORTED_RESOLUTIONS
            )
        )
        return res
