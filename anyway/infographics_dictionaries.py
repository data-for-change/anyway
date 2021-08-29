# noinspection PyProtectedMember
from flask_babel import _

head_on_collisions_comparison_dict = dict(
    head_to_head_collision="התנגשות חזית בחזית", others="אחרות", head_to_head="חזיתיות"
)


# temporary until we'll create translations
class SmartDict(dict):
    def __missing__(self, key):
        return key


segment_dictionary = SmartDict()

# bogus calls to gettext to get pybabel extract to recognize the strings
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
