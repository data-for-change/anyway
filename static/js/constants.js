var ADD_DISCUSSION = "צרו דיון";
var NEW_FEATURES = "עדכן אותי לגבי תכונות חדשות";

var PROVIDERS = {};
PROVIDERS[1] = PROVIDERS[3] = {
  name: "הלשכה המרכזית לסטטיסטיקה",
  url: "http://www.cbs.gov.il",
  logo: "cbs.png",
};
PROVIDERS[2] = {
  name: "איחוד הצלה",
  url: "http://www.1221.org.il",
  logo: "united.jpg",
};

var SEVERITY_FATAL = 1;
var SEVERITY_SEVERE = 2;
var SEVERITY_LIGHT = 3;
var SEVERITY_VARIOUS = 4;

var SEVERITY_ATTRIBUTES = {};
SEVERITY_ATTRIBUTES[SEVERITY_FATAL] = "showFatal";
SEVERITY_ATTRIBUTES[SEVERITY_SEVERE] = "showSevere";
SEVERITY_ATTRIBUTES[SEVERITY_LIGHT] = "showLight";

var ACCIDENT_TYPE_CAR_TO_CAR = -1; // Synthetic type
var ACCIDENT_TYPE_CAR_TO_OBJECT = -2; // Synthetic type
var ACCIDENT_TYPE_CAR_TO_PEDESTRIAN = 1;
var ACCIDENT_TYPE_FRONT_TO_SIDE = 2;
var ACCIDENT_TYPE_FRONT_TO_REAR = 3;
var ACCIDENT_TYPE_SIDE_TO_SIDE = 4;
var ACCIDENT_TYPE_FRONT_TO_FRONT = 5;
var ACCIDENT_TYPE_WITH_STOPPED_CAR_NO_PARKING = 6;
var ACCIDENT_TYPE_WITH_STOPPED_CAR_PARKING = 7;
var ACCIDENT_TYPE_WITH_STILL_OBJECT = 8;
var ACCIDENT_TYPE_OFF_ROAD_OR_SIDEWALK = 9;
var ACCIDENT_TYPE_ROLLOVER = 10;
var ACCIDENT_TYPE_SKID = 11;
var ACCIDENT_TYPE_HIT_PASSSENGER_IN_CAR = 12;
var ACCIDENT_TYPE_FALLING_OFF_MOVING_VEHICLE = 13;
var ACCIDENT_TYPE_FIRE = 14;
var ACCIDENT_TYPE_OTHER = 15;
var ACCIDENT_TYPE_BACK_TO_FRONT = 17;
var ACCIDENT_TYPE_BACK_TO_SIDE = 18;
var ACCIDENT_TYPE_WITH_ANIMAL = 19;
var ACCIDENT_TYPE_WITH_VEHICLE_LOAD = 20;
var ACCIDENT_TYPE_UNITED_HATZALA = 21;

var ICONS = {};
ICONS[SEVERITY_FATAL] = {};
ICONS[SEVERITY_SEVERE] = {};
ICONS[SEVERITY_LIGHT] = {};

ICONS[SEVERITY_FATAL][ACCIDENT_TYPE_CAR_TO_PEDESTRIAN] = "/static/img/icons/vehicle_person_lethal.png";
ICONS[SEVERITY_SEVERE][ACCIDENT_TYPE_CAR_TO_PEDESTRIAN] = "/static/img/icons/vehicle_person_severe.png";
ICONS[SEVERITY_LIGHT][ACCIDENT_TYPE_CAR_TO_PEDESTRIAN] = "/static/img/icons/vehicle_person_medium.png";
ICONS[SEVERITY_FATAL][ACCIDENT_TYPE_CAR_TO_CAR] = "/static/img/icons/vehicle_vehicle_lethal.png";
ICONS[SEVERITY_SEVERE][ACCIDENT_TYPE_CAR_TO_CAR] = "/static/img/icons/vehicle_vehicle_severe.png";
ICONS[SEVERITY_LIGHT][ACCIDENT_TYPE_CAR_TO_CAR] = "/static/img/icons/vehicle_vehicle_medium.png";
ICONS[SEVERITY_FATAL][ACCIDENT_TYPE_CAR_TO_OBJECT] = "/static/img/icons/vehicle_object_lethal.png";
ICONS[SEVERITY_SEVERE][ACCIDENT_TYPE_CAR_TO_OBJECT] = "/static/img/icons/vehicle_object_severe.png";
ICONS[SEVERITY_LIGHT][ACCIDENT_TYPE_CAR_TO_OBJECT] = "/static/img/icons/vehicle_object_medium.png";
ICONS[SEVERITY_LIGHT][ACCIDENT_TYPE_UNITED_HATZALA] = "/static/img/icons/vehicle_unknown_medium.png";
ICONS[SEVERITY_SEVERE][ACCIDENT_TYPE_UNITED_HATZALA] = "/static/img/icons/vehicle_unknown_severe.png";

var MULTIPLE_ICONS = {};
MULTIPLE_ICONS[SEVERITY_FATAL] = "/static/img/icons/multiple_lethal.png";
MULTIPLE_ICONS[SEVERITY_SEVERE] = "/static/img/icons/multiple_severe.png";
MULTIPLE_ICONS[SEVERITY_LIGHT] = "/static/img/icons/multiple_medium.png";
MULTIPLE_ICONS[SEVERITY_VARIOUS] = "/static/img/icons/multiple_various.png";

var USER_LOCATION_ICON = "/static/img/icons/you_are_Here.png";
var DISCUSSION_ICON = "/static/img/icons/discussion.png";

var ACCIDENT_MINOR_TYPE_TO_TYPE = {};
ACCIDENT_MINOR_TYPE_TO_TYPE[ACCIDENT_TYPE_CAR_TO_PEDESTRIAN] = ACCIDENT_TYPE_CAR_TO_PEDESTRIAN;
ACCIDENT_MINOR_TYPE_TO_TYPE[ACCIDENT_TYPE_FRONT_TO_SIDE] = ACCIDENT_TYPE_CAR_TO_CAR;
ACCIDENT_MINOR_TYPE_TO_TYPE[ACCIDENT_TYPE_FRONT_TO_REAR] = ACCIDENT_TYPE_CAR_TO_CAR;
ACCIDENT_MINOR_TYPE_TO_TYPE[ACCIDENT_TYPE_SIDE_TO_SIDE] = ACCIDENT_TYPE_CAR_TO_CAR;
ACCIDENT_MINOR_TYPE_TO_TYPE[ACCIDENT_TYPE_FRONT_TO_FRONT] = ACCIDENT_TYPE_CAR_TO_CAR;
ACCIDENT_MINOR_TYPE_TO_TYPE[ACCIDENT_TYPE_WITH_STOPPED_CAR_NO_PARKING] = ACCIDENT_TYPE_CAR_TO_CAR;
ACCIDENT_MINOR_TYPE_TO_TYPE[ACCIDENT_TYPE_WITH_STOPPED_CAR_PARKING] = ACCIDENT_TYPE_CAR_TO_CAR;
ACCIDENT_MINOR_TYPE_TO_TYPE[ACCIDENT_TYPE_WITH_STILL_OBJECT] = ACCIDENT_TYPE_CAR_TO_OBJECT;
ACCIDENT_MINOR_TYPE_TO_TYPE[ACCIDENT_TYPE_OFF_ROAD_OR_SIDEWALK] = ACCIDENT_TYPE_CAR_TO_OBJECT;
ACCIDENT_MINOR_TYPE_TO_TYPE[ACCIDENT_TYPE_ROLLOVER] = ACCIDENT_TYPE_CAR_TO_OBJECT;
ACCIDENT_MINOR_TYPE_TO_TYPE[ACCIDENT_TYPE_SKID] = ACCIDENT_TYPE_CAR_TO_OBJECT;
ACCIDENT_MINOR_TYPE_TO_TYPE[ACCIDENT_TYPE_HIT_PASSSENGER_IN_CAR] = ACCIDENT_TYPE_CAR_TO_CAR;
ACCIDENT_MINOR_TYPE_TO_TYPE[ACCIDENT_TYPE_FALLING_OFF_MOVING_VEHICLE] = ACCIDENT_TYPE_CAR_TO_OBJECT;
ACCIDENT_MINOR_TYPE_TO_TYPE[ACCIDENT_TYPE_FIRE] = ACCIDENT_TYPE_CAR_TO_OBJECT;
ACCIDENT_MINOR_TYPE_TO_TYPE[ACCIDENT_TYPE_OTHER] = ACCIDENT_TYPE_CAR_TO_OBJECT;
ACCIDENT_MINOR_TYPE_TO_TYPE[ACCIDENT_TYPE_BACK_TO_FRONT] = ACCIDENT_TYPE_CAR_TO_CAR;
ACCIDENT_MINOR_TYPE_TO_TYPE[ACCIDENT_TYPE_BACK_TO_SIDE] = ACCIDENT_TYPE_CAR_TO_CAR;
ACCIDENT_MINOR_TYPE_TO_TYPE[ACCIDENT_TYPE_WITH_ANIMAL] = ACCIDENT_TYPE_CAR_TO_PEDESTRIAN;
ACCIDENT_MINOR_TYPE_TO_TYPE[ACCIDENT_TYPE_WITH_VEHICLE_LOAD] = ACCIDENT_TYPE_CAR_TO_CAR;
ACCIDENT_MINOR_TYPE_TO_TYPE[ACCIDENT_TYPE_UNITED_HATZALA] = ACCIDENT_TYPE_UNITED_HATZALA;

var DEFAULT_ICON = ICONS[1][1];

function getIcon(accidentType, severity) {
    var icon = DEFAULT_ICON;
    try {
        if (accidentType == "multiple") {
            icon = MULTIPLE_ICONS[severity];
        } else {
            icon = ICONS[severity][ACCIDENT_MINOR_TYPE_TO_TYPE[accidentType]];
        }
    } catch (err) {
        // stick to default icon
    }
    if (isRetina){
        var googleIcon = {
            url: icon,
            scaledSize: new google.maps.Size(30, 50)
        };
        icon = googleIcon;
    }

    return icon;
}

var TYPE_STRING = [
    "",
    "תאונה",
    "הצעה",
    "עצומה"
];

var TYPES_MAP = {};
TYPES_MAP['Accident'] = TYPE_STRING[1];

var SEVERITY_MAP = {};
SEVERITY_MAP[SEVERITY_FATAL] = 'קטלנית';
SEVERITY_MAP[SEVERITY_SEVERE] = 'קשה';
SEVERITY_MAP[SEVERITY_LIGHT] = 'קלה';

var SUBTYPE_STRING = [
    "פגיעה בהולך רגל",
    "התנגשות חזית אל צד",
    "התנגשות חזית באחור",
    "התנגשות צד בצד",
    "התנגשות חזית אל חזית",
    "התנגשות עם רכב שנעצר ללא חניה",
    "התנגשות עם רכב חונה",
    "התנגשות עם עצם דומם",
    "ירידה מהכביש או עלייה למדרכה",
    "התהפכות",
    "החלקה",
    "פגיעה בנוסע בתוך כלי רכב",
    "נפילה ברכב נע",
    "שריפה",
    "אחר",
    "התנגשות אחור אל חזית",
    "התנגשות אחור אל צד",
    "התנגשות עם בעל חיים",
    "פגיעה ממטען של רכב"
];


var FILTER_MARKERS = 0;
var FILTER_INFO = 1;
var FILTER_DATE = 2;

var SELECTED_MARKER = '(נבחר)';
