from anyway.constants.label_code import LabeledCode


class DriverType(LabeledCode):
    PROFESSIONAL_DRIVER = 1
    PRIVATE_VEHICLE_DRIVER = 2
    OTHER_DRIVER = 3

    @classmethod
    def labels(cls):
        return {
            DriverType.PROFESSIONAL_DRIVER: "professional_driver",
            DriverType.PRIVATE_VEHICLE_DRIVER: "private_vehicle_driver",
            DriverType.OTHER_DRIVER: "other_driver",
        }