from flask_babel import _

driver_type_hebrew_dict = dict(
    professional_driver="נהג מקצועי", private_vehicle_driver="נהג פרטי", other_driver="לא ידוע"
)
head_on_collisions_comparison_dict = dict(
    head_to_head_collision="התנגשות חזית בחזית", others="אחרות", head_to_head="חזיתיות"
)
english_accident_severity_dict = {1: "fatal", 2: "severe", 3: "light"}

accident_type_dict = {1: _("Pedestrian injury"),
                          2: _("Collision of front to side"),
                          3: _("Collision of front to rear-end"),
                          4: _("Collision of side to side (lateral)"),
                          5: _("Head-on frontal collision"),
                          6: _("Collision with a stopped non-parked vehicle"),
                          7: _("Collision with a parked vehicle"),
                          8: _("Collision with an inanimate object"),
                          9: _("Swerving off the road or onto the pavement"),
                          10: _("Overturned vehicle"),
                          11: _("Skid"),
                          12: _("Injury of a passenger in a vehicle"),
                          13: _("A fall from a moving vehicle"),
                          14: _("Fire"),
                          15: _("Other"),
                          17: _("Collision of rear-end to front"),
                          18: _("Collision of rear-end to side"),
                          19: _("Collision with an animal"),
                          20: _("Damage caused by a falling load off a vehicle")}

# temporary until we'll create translations
class smart_dict(dict):
    def __missing__(self, key):
        return key

segment_dictionary = smart_dict()