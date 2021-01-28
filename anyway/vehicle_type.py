from enum import Enum
from typing import List, Union
import logging
import math
from flask_babel import _


class VehicleType(Enum):
    CAR = 1
    TRUCK_UPTO_4 = 2
    PICKUP_UPTO_4 = 3
    TRUCK_4_TO_10 = 4
    TRUCK_12_TO_16 = 5
    TRUCK_16_TO_34 = 6
    TRUCK_ABOVE_34 = 7
    MOTORCYCLE_UPTO_50 = 8
    MOTORCYCLE_50_TO_250 = 9
    MOTORCYCLE_250_TO_500 = 10
    BUS = 11
    TAXI = 12
    WORK = 13
    TRACTOR = 14
    BIKE = 15
    TRAIN = 16
    OTHER_AND_UNKNOWN = 17
    MINIBUS = 18
    MOTORCYCLE_ABOVE_500 = 19
    ELECTRIC_SCOOTER = 21
    MOBILITY_SCOOTER = 22
    ELECTRIC_BIKE = 23
    TRUCK_3_5_TO_10 = 24
    TRUCK_10_TO_12 = 25

    def get_categories(self) -> List[int]:
        res = []
        for t in list(VehicleCategory):
            if self in t.value:
                res.append(t)
        return res

    def get_english_display_name(self):
        english_vehicle_type_display_names = {
            VT.CAR: _("private car"),
            VT.TRUCK_UPTO_4: _("truck upto 4 tons"),
            VT.PICKUP_UPTO_4: _("pickup upto 4 tons"),
            VT.TRUCK_4_TO_10: _("truck 4 to 10 tons"),
            VT.TRUCK_12_TO_16: _("truck 12 to 16 tons"),
            VT.TRUCK_16_TO_34: _("truck 16 to 34 tons"),
            VT.TRUCK_ABOVE_34: _("truck above 34 tons"),
            VT.MOTORCYCLE_UPTO_50: _("motorcycle upto 50 cc"),
            VT.MOTORCYCLE_50_TO_250: _("motorcycle 50 to 250 cc"),
            VT.MOTORCYCLE_250_TO_500: _("motorcycle 250 to 500 cc"),
            VT.BUS: _("bus"),
            VT.TAXI: _("taxi"),
            VT.WORK: _("work vehicle"),
            VT.TRACTOR: _("tractor"),
            VT.BIKE: _("bike"),
            VT.TRAIN: _("train"),
            VT.OTHER_AND_UNKNOWN: _("other and unknown"),
            VT.MINIBUS: _("minibus"),
            VT.MOTORCYCLE_ABOVE_500: _("motorcycle above 500 cc"),
            VT.ELECTRIC_SCOOTER: _("electric scooter"),
            VT.MOBILITY_SCOOTER: _("mobility scooter"),
            VT.ELECTRIC_BIKE: _("electric bike"),
            VT.TRUCK_3_5_TO_10: _("truck 3.5 to 10 tons"),
            VT.TRUCK_10_TO_12: _("truck 10 to 12 tons"),
        }
        try:
            return english_vehicle_type_display_names[self]
        except (KeyError, TypeError):
            logging.exception(f"VehicleType.get_display_name: {self}: no display string defined")
            return "no display name defined"

    #
    # def get_display_name(self) -> str:
    #     try:
    #         return self.english_vehicle_type_display_names[self.value]
    #     except (KeyError, TypeError):
    #         logging.exception(f"VehicleType.get_display_name: {self.value}: no display string defined")
    #         return "no display name defined"

    @staticmethod
    def to_type_code(db_val: Union[float, int]) -> int:
        """Values read from DB may arrive as float, and empty values come as nan"""
        if isinstance(db_val, float):
            if math.isnan(db_val):
                return VehicleType.OTHER_AND_UNKNOWN.value
            else:
                return int(db_val)
        elif isinstance(db_val, int):
            return db_val
        else:
            logging.error(f"VehicleType.fo_type_code: unknown value: {db_val}({type(db_val)})"
                          '. returning OTHER_AND_UNKNOWN')
            return VehicleType.OTHER_AND_UNKNOWN.value


VT = VehicleType


class VehicleCategory(Enum):
    PROFESSIONAL_DRIVER = 1
    PRIVATE_DRIVER = 2
    LIGHT_ELECTRIC = 3
    CAR = 4
    LARGE = 5
    MOTORCYCLE = 6
    BICYCLE_AND_SMALL_MOTOR = 7
    OTHER = 8

    def get_codes(self) -> List[int]:
        """returns VehicleType codes of category"""
        category_vehicle_types = {
            VehicleCategory.PROFESSIONAL_DRIVER: [
                VT.TRUCK_UPTO_4,
                VT.PICKUP_UPTO_4,
                VT.TRUCK_4_TO_10,
                VT.TRUCK_12_TO_16,
                VT.TRUCK_16_TO_34,
                VT.TRUCK_ABOVE_34,
                VT.BUS,
                VT.TAXI,
                VT.WORK,
                VT.TRACTOR,
                VT.MINIBUS,
                VT.TRUCK_3_5_TO_10,
                VT.TRUCK_10_TO_12,
            ],
            VehicleCategory.PRIVATE_DRIVER: [
                VT.CAR,
                VT.MOTORCYCLE_UPTO_50,
                VT.MOTORCYCLE_50_TO_250,
                VT.MOTORCYCLE_250_TO_500,
                VT.MOTORCYCLE_ABOVE_500,
            ],
            VehicleCategory.LIGHT_ELECTRIC: [
                VT.ELECTRIC_SCOOTER,
                VT.MOBILITY_SCOOTER,
                VT.ELECTRIC_BIKE
            ],
            VehicleCategory.CAR: [VT.CAR, VT.TAXI],
            VehicleCategory.LARGE: [
                VT.TRUCK_UPTO_4,
                VT.PICKUP_UPTO_4,
                VT.TRUCK_4_TO_10,
                VT.TRUCK_12_TO_16,
                VT.TRUCK_16_TO_34,
                VT.TRUCK_ABOVE_34,
                VT.BUS,
                VT.WORK,
                VT.TRACTOR,
                VT.MINIBUS,
                VT.TRUCK_3_5_TO_10,
                VT.TRUCK_10_TO_12,
            ],
            VehicleCategory.MOTORCYCLE: [
                VT.MOTORCYCLE_UPTO_50,
                VT.MOTORCYCLE_50_TO_250,
                VT.MOTORCYCLE_250_TO_500,
                VT.MOTORCYCLE_ABOVE_500,
            ],
            VehicleCategory.BICYCLE_AND_SMALL_MOTOR: [VT.BIKE, VT.ELECTRIC_SCOOTER, VT.ELECTRIC_BIKE],
            VehicleCategory.OTHER: [VT.BIKE, VT.TRAIN, VT.OTHER_AND_UNKNOWN]
        }
        return list(map(lambda x: x.value, category_vehicle_types[self]))

    def contains(self, vt_code: int) -> bool:
        # noinspection PyTypeChecker
        if not isinstance(int, vt_code):
            logging.warning(f"VehicleCategory.contains: {vt_code}:{type(vt_code)}: not int")
            return False
        return vt_code in self.get_codes()

    def get_english_display_name(self):
        english_vehicle_type_display_names = {
            VC.PROFESSIONAL_DRIVER: _("professional driver"),
            VC.PRIVATE_DRIVER: _("private driver"),
            VC.LIGHT_ELECTRIC: _("light electric vehicles"),
            VC.CAR: _("private car"),
            VC.LARGE: _("large vehicle"),
            VC.MOTORCYCLE: _("motorcycle"),
            VC.BICYCLE_AND_SMALL_MOTOR: _("bicycle and small motor vehicles"),
            VC.OTHER: _("other"),
        }
        try:
            return english_vehicle_type_display_names[self]
        except (KeyError, TypeError):
            logging.exception(f"VehicleType.get_display_name: {self}: no display string defined")
            return "no display name defined"


VC = VehicleCategory
