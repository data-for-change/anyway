from anyway.constants.label_code import LabeledCode


class AccidentType(LabeledCode):
    PEDESTRIAN_INJURY = 1
    COLLISION_OF_FRONT_TO_SIDE = 2
    COLLISION_OF_FRONT_TO_REAR_END = 3
    COLLISION_OF_SIDE_TO_SIDE_LATERAL = 4
    HEAD_ON_FRONTAL_COLLISION = 5
    COLLISION_WITH_A_STOPPED_NON_PARKED_VEHICLE = 6
    COLLISION_WITH_A_PARKED_VEHICLE = 7
    COLLISION_WITH_AN_INANIMATE_OBJECT = 8
    SWERVING_OFF_THE_ROAD_OR_ONTO_THE_PAVEMENT = 9
    OVERTURNED_VEHICLE = 10
    SKID = 11
    INJURY_OF_A_PASSENGER_IN_A_VEHICLE = 12
    A_FALL_FROM_A_MOVING_VEHICLE = 13
    FIRE = 14
    OTHER = 15
    COLLISION_OF_REAR_END_TO_FRONT = 17
    COLLISION_OF_REAR_END_TO_SIDE = 18
    COLLISION_WITH_AN_ANIMAL = 19
    DAMAGE_CAUSED_BY_A_FALLING_LOAD_OFF_A_VEHICLE = 20

    @classmethod
    def labels(cls):
        return {
            AccidentType.PEDESTRIAN_INJURY: "Pedestrian injury",
            AccidentType.COLLISION_OF_FRONT_TO_SIDE: "Collision of front to side",
            AccidentType.COLLISION_OF_FRONT_TO_REAR_END: "Collision of front to rear-end",
            AccidentType.COLLISION_OF_SIDE_TO_SIDE_LATERAL: "Collision of side to side (lateral)",
            AccidentType.HEAD_ON_FRONTAL_COLLISION: "Head-on frontal collision",
            AccidentType.COLLISION_WITH_A_STOPPED_NON_PARKED_VEHICLE: "Collision with a stopped non-parked vehicle",
            AccidentType.COLLISION_WITH_A_PARKED_VEHICLE: "Collision with a parked vehicle",
            AccidentType.COLLISION_WITH_AN_INANIMATE_OBJECT: "Collision with an inanimate object",
            AccidentType.SWERVING_OFF_THE_ROAD_OR_ONTO_THE_PAVEMENT: "Swerving off the road or onto the pavement",
            AccidentType.OVERTURNED_VEHICLE: "Overturned vehicle",
            AccidentType.SKID: "Skid",
            AccidentType.INJURY_OF_A_PASSENGER_IN_A_VEHICLE: "Injury of a passenger in a vehicle",
            AccidentType.A_FALL_FROM_A_MOVING_VEHICLE: "A fall from a moving vehicle",
            AccidentType.FIRE: "Fire",
            AccidentType.OTHER: "Other",
            AccidentType.COLLISION_OF_REAR_END_TO_FRONT: "Collision of rear-end to front",
            AccidentType.COLLISION_OF_REAR_END_TO_SIDE: "Collision of rear-end to side",
            AccidentType.COLLISION_WITH_AN_ANIMAL: "Collision with an animal",
            AccidentType.DAMAGE_CAUSED_BY_A_FALLING_LOAD_OFF_A_VEHICLE: "Damage caused by a falling load off a vehicle",
        }
