#!/usr/bin/python
# -*- coding: utf-8 -*-
import csv
import datetime
import json

TABLES = {
    "SUG_DEREH" : {
        1 : "עירוני בצומת",
        2 : "עירוני לא בצומת",
        3 : "לא עירוני בצומת",
        4 : "לא עירוני לא בצומת",
    },
    "YEHIDA" : {
        11 : "מרחב חוף (חיפה)",
        12 : "מרחב גליל",
        14 : "מרחב עמקים",
        20 : "מרחב ת\"א",
        33 : "מרחב אילת",
        34 : "מרחב הנגב",
        36 : "מרחב שמשון (עד 1999)",
        37 : "מרחב שמשון (החל ב-2004)",
        38 : "מרחב לכיש",
        41 : "מרחב שומרון",
        43 : "מרחב יהודה",
        51 : "מרחב השרון",
        52 : "מרחב השפלה",
        61 : "מחוז ירושלים",
    },
    "SUG_YOM" : {
        1 : "חג",
        2 : "ערב חג",
        3 : "חול המועד",
        4 : "יום אחר",
    },
    "HUMRAT_TEUNA" : {
        1 : "קטלנית",
        2 : "קשה",
        3 : "קלה",
    },
    "SUG_TEUNA" : {
        1 : "פגיעה בהולך רגל",
        2 : "התנגשות חזית אל צד",
        3 : "התנגשות חזית באחור",
        4 : "התנגשות צד בצד",
        5 : "התנגשות חזית אל חזית",
        6 : "התנגשות עם רכב שנעצר ללא חניה",
        7 : "התנגשות עם רכב חונה",
        8 : "התנגשות עם עצם דומם",
        9 : "ירידה מהכביש או עלייה למדרכה",
        10 : "התהפכות",
        11 : "החלקה",
        12 : "פגיעה בנוסע בתוך כלי רכב",
        13 : "נפילה ברכב נע",
        14 : "שריפה",
        15 : "אחר",
        17 : "התנגשות אחור אל חזית",
        18 : "התנגשות אחור אל צד",
        19 : "התנגשות עם בעל חיים",
        20 : "פגיעה ממטען של רכב",
    },
    "ZURAT_DEREH" : {
        1 : "כניסה למחלף",
        2 : "ביציאה ממחלף",
        3 : "מ.חניה/ת. דלק",
        4 : "שיפוע תלול",
        5 : "עקום חד",
        6 : "על גשר מנהרה",
        7 : "מפגש מסילת ברזל",
        8 : "כביש ישר/צומת",
        9 : "אחר",
    },
    "HAD_MASLUL" : {
        1 : "חד סיטרי",
        2 : "דו סיטרי+קו הפרדה רצוף",
        3 : "דו סיטרי אין קו הפרדה רצוף",
        4 : "אחר",
    },
    "RAV_MASLUL" : {
        1 : "מיפרדה מסומנת בצבע",
        2 : "מיפרדה עם גדר בטיחות",
        3 : "מיפרדה בנויה ללא גדר בטיחות",
        4 : "מיפרדה לא בנויה",
        5 : "אחר",
    },
    "MEHIRUT_MUTERET" : {
        1 : "עד 50 קמ\"ש",
        2 : "60 קמ\"ש",
        3 : "70 קמ\"ש",
        4 : "80 קמ\"ש",
        5 : "90 קמ\"ש",
        6 : "100 קמ\"ש",
    },
    "TKINUT" : {
        1 : "אין ליקוי",
        2 : "שוליים גרועים",
        3 : "כביש משובש",
        4 : "שוליים גרועים וכביש משובש",
    },
    "ROHAV" : {
        1 : "עד 5 מטר",
        2 : "5 עד 7",
        3 : "7 עד 10.5",
        4 : "10.5 עד 14",
        5 : "יותר מ-14",
    },
    "SIMUN_TIMRUR" : {
        1 : "סימון לקוי/חסר",
        2 : "תימרור לקוי/חסר",
        3 : "אין ליקוי",
        4 : "לא נדרש תמרור",
    },
    "TEURA" : {
        1 : "אור יום רגיל",
        2 : "ראות מוגבלת עקב מזג אויר (עשן,ערפל)",
        3 : "לילה פעלה תאורה",
        4 : "קיימת תאורה בלתי תקינה/לא פועלת",
        5 : "לילה לא קיימת תאורה",
    },
    "BAKARA" : {
        1 : "אין בקרה",
        2 : "רמזור תקין",
        3 : "רמזור מהבהב צהוב",
        4 : "רמזור לא תקין",
        5 : "תמרור עצור",
        6 : "תמרור זכות קדימה",
        7 : "אחר",
    },
    "MEZEG_AVIR" : {
        1 : "בהיר",
        2 : "גשום",
        3 : "שרבי",
        4 : "ערפילי",
        5 : "אחר",
    },
    "PNE_KVISH" : {
        1 : "יבש",
        2 : "רטוב ממים",
        3 : "מרוח בחומר דלק",
        4 : "מכוסה בבוץ",
        5 : "חול או חצץ על הכביש",
        6 : "אחר",
    },
    "SUG_EZEM" : {
        1 : "עץ",
        2 : "עמוד חשמל/תאורה/טלפון",
        3 : "תמרור ושלט",
        4 : "גשר סימניו ומגיניו",
        5 : "מבנה",
        6 : "גדר בטיחות לרכב",
        7 : "חבית",
        8 : "אחר",
    },
    "MERHAK_EZEM" : {
        1 : "עד מטר",
        2 : "1-3 מטר",
        3 : "על הכביש",
        4 : "על שטח הפרדה",
    },
    "LO_HAZA" : {
        1 : "הלך בכיוון התנועה",
        2 : "הלך נגד",
        3 : "שיחק על הכביש",
        4 : "עמד על הכביש",
        5 : "היה על אי הפרדה",
        6 : "היה על שוליים/מדרכה",
        7 : "אחר",
    },
    "OFEN_HAZIYA" : {
        1 : "התפרץ אל הכביש",
        2 : "חצה שהוא מוסתר",
        3 : "חצה רגיל",
        4 : "אחר",
    },
    "MEKOM_HAZIYA" : {
        1 : "לא במעבר חציה ליד צומת",
        2 : "לא במעבר חציה לא ליד צומת",
        3 : "במעבר חציה בלי רמזור",
        4 : "במעבר חציה עם רמזור",
    },
    "KIVUN_HAZIYA" : {
        1 : "מימין לשמאל",
        2 : "משמאל לימין",
    },
    "STATUS_IGUN" : {
        1 : "עיגון מדויק",
        2 : "מרכז ישוב",
        3 : "מרכז דרך",
        4 : "מרכז קילומטר",
        9 : "לא עוגן",
    }
}

accidents_file = "data/H20101042AccData.csv"
cities_file = "data/cities.csv"
streets_file = "data/H20101042DicStreets.csv"
dictionary_file = "data/H20101042Dictionary.csv"
urban_intersection_file = "data/H20101042IntersectUrban.csv"
non_urban_intersection_file = "data/H20101042IntersectNonUrban.csv"

cities = [x for x in csv.DictReader(open(cities_file))]
streets = [x for x in csv.DictReader(open(streets_file))]
dictionary_data = [x for x in csv.DictReader(open(dictionary_file))]
urban_intersection = [x for x in csv.DictReader(open(urban_intersection_file))]
non_urban_intersection = [x for x in csv.DictReader(open(non_urban_intersection_file))]

cities_dict = {x["SEMEL"] : x["NAME"] for x in cities}

def number(param, value, accident):
    return int(value) if value else None

def fixed_table(param, value, accident):
    return TABLES[param][int(value)] if value and int(value) in TABLES[param] else None

def dictionary(param, value, accident):
    for item in dictionary_data:
        if item["MS_TAVLA"] == param and item["KOD"] == value:
            return dictionary_data[2]

    return  None

def boolean(param, value, accident):
    return True if value == 1 else False

def cities_map(param, value, accident):
    return cities_dict[value] if value in cities_dict else ""

def streets_map(param, value, accident):
    for street in streets:
        if street["ishuv"] == accident["SEMEL_YISHUV"] and value == street["SEMEL_RECHOV"]:
            return street["SHEM_RECHOV"]

def urban_intersection_map(param, value, accident):
    return value

def non_urban_intersection_map(param, value, accident):
    return value

FIELD_FUNCTIONS = {
    "pk_teuna_fikt" : ("מזהה", number, None),
    "SUG_DEREH" : ("סוג דרך", fixed_table, "SUG_DEREH"),
    "SEMEL_YISHUV" : ("ישוב", cities_map, None), #from dictionary
    "REHOV1" : ("רחוב 1", streets_map, None), #from dicstreets (with SEMEL_YISHUV)
    "REHOV2" : ("רחוב 2", streets_map, None), #from dicstreets (with SEMEL_YISHUV)
    "BAYIT" : ("מספר בית", number, None),
    "ZOMET_IRONI" : ("צומת עירוני", urban_intersection_map, None),#from intersect urban dictionary
    "KVISH1" : ("כביש 1", urban_intersection_map, None), #from intersect urban dictionary
    "KVISH2" : ("כביש 2", urban_intersection_map, None),#from intersect urban dictionary
    "ZOMET_LO_IRONI" : ("צומת לא עירוני", non_urban_intersection_map, None),#from non urban dictionary
    "YEHIDA" : ("יחידה", fixed_table, "YEHIDA"),
    "SUG_YOM" : ("סוג יום", fixed_table, "SUG_YOM"),
    "RAMZOR" : ("רמזור", boolean, None),
    "HUMRAT_TEUNA" : ("חומרת תאונה", fixed_table, "HUMRAT_TEUNA"),
    "SUG_TEUNA" : ("סוג תאונה", fixed_table, "SUG_TEUNA"),
    "ZURAT_DEREH" : ("צורת דרך", fixed_table, "ZURAT_DEREH"),
    "HAD_MASLUL" : ("חד מסלול", fixed_table, "HAD_MASLUL"),
    "RAV_MASLUL" : ("רב מסלול", fixed_table, "RAV_MASLUL"),
    "MEHIRUT_MUTERET" : ("מהירות מותרת", fixed_table, "MEHIRUT_MUTERET"),
    "TKINUT" : ("תקינות", fixed_table, "TKINUT"),
    "ROHAV" : ("רוחב", fixed_table, "ROHAV"),
    "SIMUN_TIMRUR" : ("סימון תמרור", fixed_table, "SIMUN_TIMRUR"),
    "TEURA" :  ("תאורה", fixed_table, "TEURA"),
    "BAKARA" :  ("בקרה", fixed_table, "BAKARA"),
    "MEZEG_AVIR" :  ("מזג אוויר", fixed_table, "MEZEG_AVIR"),
    "PNE_KVISH" :  ("פני כביש", fixed_table, "PNE_KVISH"),
    "SUG_EZEM" :  ("סוג עצם", fixed_table, "SUG_EZEM"),
    "MERHAK_EZEM" :  ("מרחק עצם", fixed_table, "MERHAK_EZEM"),
    "LO_HAZA" :  ("לא חצה", fixed_table, "LO_HAZA"),
    "OFEN_HAZIYA" : ("אופן חציה", fixed_table, "OFEN_HAZIYA"),
    "MEKOM_HAZIYA" : ("מקום חציה", fixed_table, "MEKOM_HAZIYA"),
    "KIVUN_HAZIYA" : ("כיוון חציה", fixed_table, "MEKOM_HAZIYA"),
    "STATUS_IGUN" : ("עיגון", fixed_table, "STATUS_IGUN"),
    "MAHOZ" : ("מחוז", dictionary, 77),
    "NAFA" : ("נפה", dictionary, 79),
    "EZOR_TIVI" : ("אזור טבעי", dictionary, 80),
    "MAAMAD_MINIZIPALI" : ("מעמד מוניציפלי", dictionary, 78),
    "ZURAT_ISHUV" : ("צורת יישוב", dictionary, 81),
}

FIELD_LIST = [
    "SUG_DEREH", "SEMEL_YISHUV", "REHOV1", "REHOV2", "BAYIT", "ZOMET_IRONI", "KVISH1", "KVISH2",
    "ZOMET_LO_IRONI", "YEHIDA", "SUG_YOM", "RAMZOR",
    "HUMRAT_TEUNA", "SUG_TEUNA", "ZURAT_DEREH", "HAD_MASLUL", "RAV_MASLUL", "MEHIRUT_MUTERET", "TKINUT", "ROHAV",
    "SIMUN_TIMRUR", "TEURA","BAKARA", "MEZEG_AVIR", "PNE_KVISH", "SUG_EZEM", "MERHAK_EZEM", "LO_HAZA", "OFEN_HAZIYA",
    "MEKOM_HAZIYA", "KIVUN_HAZIYA", "MAHOZ", "NAFA", "EZOR_TIVI", "MAAMAD_MINIZIPALI", "ZURAT_ISHUV", 
]

def import_data():
    accidents_csv = csv.DictReader(open(accidents_file))
    accidents_gps_coordinates = json.loads(open("data/gps.json").read())

    # oh dear.
    i = -1

    for accident in accidents_csv:
        i += 1
        output_line = {}
        output_fields = {}
        description_strings = []
        for field in FIELD_LIST:
            field_name, processor, parameter = FIELD_FUNCTIONS[field]
            output_line[field] = processor(parameter, accident[field], accident)
            if output_line[field]:
                if field in [
                        "SHNAT_TEUNA",
                        "HODESH_TEUNA",
                        "YOM_BE_HODESH",
                        "SHAA",
                        "REHOV1",
                        "REHOV2",
                        "BAYIT",
                        "SEMEL_YISHUV",
                        "HUMRAT_TEUNA",
                        "X",
                        "Y"]:
                    continue
                description_strings.append("%s: %s" % (field_name, output_line[field]))

        if not accident["X"] or not accident["Y"]:
            continue

        accident_date = datetime.datetime(int(accident["SHNAT_TEUNA"]), int(accident["HODESH_TEUNA"]), int(accident["YOM_BE_HODESH"]), int(accident["SHAA"]) % 24, 0, 0)
        address = "%s%s, %s" % (output_line["REHOV1"], " %s" % output_line["BAYIT"] if output_line["BAYIT"] != 9999 else "", output_line["SEMEL_YISHUV"])

        description = "\n".join(description_strings)

        output_fields["date"] = accident_date    
        output_fields["description"] = description
        output_fields["id"] = int(accident["pk_teuna_fikt"])
        output_fields["severity"] = int(accident["HUMRAT_TEUNA"])
        output_fields["address"] = address

        output_fields["lat"] = accidents_gps_coordinates[i]["lat"]
        output_fields["lng"] = accidents_gps_coordinates[i]["lng"]
        yield output_fields


if __name__ == "__main__":
    for data in import_data():
        print data["description"]
        print

