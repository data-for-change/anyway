from anyway.backend_constants import BE_CONST

driver_type_hebrew_dict = dict(
    professional_driver="נהג מקצועי", private_vehicle_driver="נהג פרטי", other_driver="לא ידוע"
)
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
