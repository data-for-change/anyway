from anyway.constants.label_code import LabeledCode


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
