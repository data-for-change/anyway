from anyway.backend_constants import BE_CONST

# noinspection PyProtectedMember
from flask_babel import _

english_driver_type_dict = {
    BE_CONST.DriverType.PROFESSIONAL_DRIVER: "professional_driver",
    BE_CONST.DriverType.PRIVATE_VEHICLE_DRIVER: "private_vehicle_driver",
    BE_CONST.DriverType.OTHER_DRIVER: "other_driver",
}

head_on_collisions_comparison_dict = dict(
    head_to_head_collision="התנגשות חזית בחזית", others="אחרות", head_to_head="חזיתיות"
)
english_accident_severity_dict = {
    BE_CONST.AccidentSeverity.FATAL: "fatal",
    BE_CONST.AccidentSeverity.SEVERE: "severe",
    BE_CONST.AccidentSeverity.LIGHT: "light",
}

english_accident_type_dict = {
    BE_CONST.AccidentType.PEDESTRIAN_INJURY: "Pedestrian injury",
    BE_CONST.AccidentType.COLLISION_OF_FRONT_TO_SIDE: "Collision of front to side",
    BE_CONST.AccidentType.COLLISION_OF_FRONT_TO_REAR_END: "Collision of front to rear-end",
    BE_CONST.AccidentType.COLLISION_OF_SIDE_TO_SIDE_LATERAL: "Collision of side to side (lateral)",
    BE_CONST.AccidentType.HEAD_ON_FRONTAL_COLLISION: "Head-on frontal collision",
    BE_CONST.AccidentType.COLLISION_WITH_A_STOPPED_NON_PARKED_VEHICLE: "Collision with a stopped non-parked vehicle",
    BE_CONST.AccidentType.COLLISION_WITH_A_PARKED_VEHICLE: "Collision with a parked vehicle",
    BE_CONST.AccidentType.COLLISION_WITH_AN_INANIMATE_OBJECT: "Collision with an inanimate object",
    BE_CONST.AccidentType.SWERVING_OFF_THE_ROAD_OR_ONTO_THE_PAVEMENT: "Swerving off the road or onto the pavement",
    BE_CONST.AccidentType.OVERTURNED_VEHICLE: "Overturned vehicle",
    BE_CONST.AccidentType.SKID: "Skid",
    BE_CONST.AccidentType.INJURY_OF_A_PASSENGER_IN_A_VEHICLE: "Injury of a passenger in a vehicle",
    BE_CONST.AccidentType.A_FALL_FROM_A_MOVING_VEHICLE: "A fall from a moving vehicle",
    BE_CONST.AccidentType.FIRE: "Fire",
    BE_CONST.AccidentType.OTHER: "Other",
    BE_CONST.AccidentType.COLLISION_OF_REAR_END_TO_FRONT: "Collision of rear-end to front",
    BE_CONST.AccidentType.COLLISION_OF_REAR_END_TO_SIDE: "Collision of rear-end to side",
    BE_CONST.AccidentType.COLLISION_WITH_AN_ANIMAL: "Collision with an animal",
    BE_CONST.AccidentType.DAMAGE_CAUSED_BY_A_FALLING_LOAD_OFF_A_VEHICLE: "Damage caused by a falling load off a vehicle",
}

english_injury_severity_dict = {
    BE_CONST.InjurySeverity.DEAD: "fatal",
    BE_CONST.InjurySeverity.SEVERE: "severe",
    BE_CONST.InjurySeverity.LIGHT: "light",
}

# temporary until we'll create translations
class smart_dict(dict):
    def __missing__(self, key):
        return key


segment_dictionary = smart_dict()

# bogus calls to gettext to get pybabel extract to recofnize the strings
_("fatal")
_("severe")
_("light")

_("Pedestrian injury")
_("Collision of front to side")
_("Collision of front to rear-end")
_("Collision of side to side (lateral)")
_("Head-on frontal collision")
_("Collision with a stopped non-parked vehicle")
_("Collision with a parked vehicle")
_("Collision with an inanimate object")
_("Swerving off the road or onto the pavement")
_("Overturned vehicle")
_("Skid")
_("Injury of a passenger in a vehicle")
_("A fall from a moving vehicle")
_("Fire")
_("Other")
_("Collision of rear-end to front")
_("Collision of rear-end to side")
_("Collision with an animal")
_("Damage caused by a falling load off a vehicle")

_("professional_driver")  # "נהג מקצועי")
_("private_vehicle_driver")  #  "נהג פרטי")
_("other_driver")  # "לא ידוע")
