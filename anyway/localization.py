#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pandas as pd

from anyway import field_names
from typing import Optional

import logging

logger = logging.getLogger("localizations")

_tables = {
    "SUG_DEREH": {
        1: "עירוני בצומת",
        2: "עירוני לא בצומת",
        3: "לא עירוני בצומת",
        4: "לא עירוני לא בצומת",
    },
    "YEHIDA": {
        11: "מרחב חוף (חיפה)",
        12: "מרחב גליל",
        14: "מרחב עמקים",
        20: 'מרחב ת"א',
        33: "מרחב אילת",
        34: "מרחב הנגב",
        36: "מרחב שמשון (עד 1999)",
        37: "מרחב שמשון (החל ב-2004)",
        38: "מרחב לכיש",
        41: "מרחב שומרון",
        43: "מרחב יהודה",
        51: "מרחב השרון",
        52: "מרחב השפלה",
        61: "מחוז ירושלים",
    },
    "SUG_YOM": {1: "חג", 2: "ערב חג", 3: "חול המועד", 4: "יום אחר"},
    "HUMRAT_TEUNA": {1: "קטלנית", 2: "קשה", 3: "קלה"},
    "SUG_TEUNA": {
        1: "פגיעה בהולך רגל",
        2: "התנגשות חזית אל צד",
        3: "התנגשות חזית באחור",
        4: "התנגשות צד בצד",
        5: "התנגשות חזית אל חזית",
        6: "התנגשות עם רכב שנעצר ללא חניה",
        7: "התנגשות עם רכב חונה",
        8: "התנגשות עם עצם דומם",
        9: "ירידה מהכביש או עלייה למדרכה",
        10: "התהפכות",
        11: "החלקה",
        12: "פגיעה בנוסע בתוך כלי רכב",
        13: "נפילה ברכב נע",
        14: "שריפה",
        15: "אחר",
        17: "התנגשות אחור אל חזית",
        18: "התנגשות אחור אל צד",
        19: "התנגשות עם בעל חיים",
        20: "פגיעה ממטען של רכב",
    },
    "ZURAT_DEREH": {
        1: "כניסה למחלף",
        2: "ביציאה ממחלף",
        3: "מ.חניה/ת. דלק",
        4: "שיפוע תלול",
        5: "עקום חד",
        6: "על גשר מנהרה",
        7: "מפגש מסילת ברזל",
        8: "כביש ישר/צומת",
        9: "אחר",
    },
    "HAD_MASLUL": {
        1: "חד סיטרי",
        2: "דו סיטרי+קו הפרדה רצוף",
        3: "דו סיטרי אין קו הפרדה רצוף",
        4: "אחר",
    },
    "RAV_MASLUL": {
        1: "מיפרדה מסומנת בצבע",
        2: "מיפרדה עם גדר בטיחות",
        3: "מיפרדה בנויה ללא גדר בטיחות",
        4: "מיפרדה לא בנויה",
        5: "אחר",
    },
    "MEHIRUT_MUTERET": {
        1: 'עד 50 קמ"ש',
        2: '60 קמ"ש',
        3: '70 קמ"ש',
        4: '80 קמ"ש',
        5: '90 קמ"ש',
        6: '100 קמ"ש',
    },
    "TKINUT": {1: "אין ליקוי", 2: "שוליים גרועים", 3: "כביש משובש", 4: "שוליים גרועים וכביש משובש"},
    "ROHAV": {1: "עד 5 מטר", 2: "5 עד 7", 3: "7 עד 10.5", 4: "10.5 עד 14", 5: "יותר מ-14"},
    "SIMUN_TIMRUR": {1: "סימון לקוי/חסר", 2: "תימרור לקוי/חסר", 3: "אין ליקוי", 4: "לא נדרש תמרור"},
    "TEURA": {
        1: "אור יום רגיל",
        2: "ראות מוגבלת עקב מזג אויר (עשן,ערפל)",
        3: "לילה פעלה תאורה",
        4: "קיימת תאורה בלתי תקינה/לא פועלת",
        5: "לילה לא קיימת תאורה",
    },
    "BAKARA": {
        1: "אין בקרה",
        2: "רמזור תקין",
        3: "רמזור מהבהב צהוב",
        4: "רמזור לא תקין",
        5: "תמרור עצור",
        6: "תמרור זכות קדימה",
        7: "אחר",
    },
    "MEZEG_AVIR": {1: "בהיר", 2: "גשום", 3: "שרבי", 4: "ערפילי", 5: "אחר"},
    "PNE_KVISH": {
        1: "יבש",
        2: "רטוב ממים",
        3: "מרוח בחומר דלק",
        4: "מכוסה בבוץ",
        5: "חול או חצץ על הכביש",
        6: "אחר",
    },
    "SUG_EZEM": {
        1: "עץ",
        2: "עמוד חשמל/תאורה/טלפון",
        3: "תמרור ושלט",
        4: "גשר סימניו ומגיניו",
        5: "מבנה",
        6: "גדר בטיחות לרכב",
        7: "חבית",
        8: "אחר",
    },
    "MERHAK_EZEM": {1: "עד מטר", 2: "1-3 מטר", 3: "על הכביש", 4: "על שטח הפרדה"},
    "LO_HAZA": {
        1: "הלך בכיוון התנועה",
        2: "הלך נגד",
        3: "שיחק על הכביש",
        4: "עמד על הכביש",
        5: "היה על אי הפרדה",
        6: "היה על שוליים/מדרכה",
        7: "אחר",
    },
    "OFEN_HAZIYA": {1: "התפרץ אל הכביש", 2: "חצה שהוא מוסתר", 3: "חצה רגיל", 4: "אחר"},
    "MEKOM_HAZIYA": {
        1: "לא במעבר חציה ליד צומת",
        2: "לא במעבר חציה לא ליד צומת",
        3: "במעבר חציה בלי רמזור",
        4: "במעבר חציה עם רמזור",
    },
    "KIVUN_HAZIYA": {1: "מימין לשמאל", 2: "משמאל לימין"},
    "STATUS_IGUN": {
        1: "עיגון מדויק",
        2: "מרכז ישוב",
        3: "מרכז דרך",
        4: "מרכז קילומטר",
        9: "לא עוגן",
    },
}

_fields = {
    "pk_teuna_fikt": "מזהה",
    "SUG_DEREH": "סוג דרך",
    "SHEM_ZOMET": "שם צומת",
    "SEMEL_YISHUV": "ישוב",  # from dictionary
    "REHOV1": "רחוב 1",  # from dicstreets (with SEMEL_YISHUV)
    "REHOV2": "רחוב 2",  # from dicstreets (with SEMEL_YISHUV)
    "BAYIT": "מספר בית",
    "ZOMET_IRONI": "צומת עירוני",  # from intersect urban dictionary
    "KVISH1": "כביש 1",  # from intersect urban dictionary
    "KVISH2": "כביש 2",  # from intersect urban dictionary
    "ZOMET_LO_IRONI": "צומת לא עירוני",  # from non urban dictionary
    "YEHIDA": "יחידה",
    "SUG_YOM": "סוג יום",
    "RAMZOR": "רמזור",
    "HUMRAT_TEUNA": "חומרת תאונה",
    "SUG_TEUNA": "סוג תאונה",
    "ZURAT_DEREH": "צורת דרך",
    "HAD_MASLUL": "חד מסלול",
    "RAV_MASLUL": "רב מסלול",
    "MEHIRUT_MUTERET": "מהירות מותרת",
    "TKINUT": "תקינות",
    "ROHAV": "רוחב",
    "SIMUN_TIMRUR": "סימון תמרור",
    "TEURA": "תאורה",
    "BAKARA": "בקרה",
    "MEZEG_AVIR": "מזג אוויר",
    "MEZEG_AVIR_UNITED": "מזג אוויר",
    "PNE_KVISH": "פני כביש",
    "SUG_EZEM": "סוג עצם",
    "MERHAK_EZEM": "מרחק עצם",
    "LO_HAZA": "לא חצה",
    "OFEN_HAZIYA": "אופן חציה",
    "MEKOM_HAZIYA": "מקום חציה",
    "KIVUN_HAZIYA": "כיוון חציה",
    "STATUS_IGUN": "עיגון",
    "MAHOZ": "מחוז",
    "NAFA": "נפה",
    "EZOR_TIVI": "אזור טבעי",
    "MAAMAD_MINIZIPALI": "מעמד מוניציפלי",
    "ZURAT_ISHUV": "צורת יישוב",
    "VEHICLE_TYPE": "סוג רכב",
    "VIOLATION_TYPE": "סוג עבירה",
    "RSA_LICENSE_PLATE": "סוג לוחית רישוי",
}

try:
    _cities = pd.read_csv("static/data/cities.csv", encoding="utf-8", index_col=field_names.sign)
except FileNotFoundError:
    pass


def get_field(field, value=None):
    if value:
        table = _tables.get(field, None)
        return table.get(value, None) if table else None

    return _fields.get(field, None)


def get_supported_tables():
    return _tables.keys()


def get_city_name(symbol_id, lang: str = "he") -> Optional[str]:
    column_to_fetch = field_names.name if lang == "he" else "ENGLISH_NAME"
    try:
        return _cities.loc[symbol_id, column_to_fetch]
    except Exception:
        return None


def join_hebrew_strings(strings, sep_a=' ,', sep_b=' ו-'):
    if len(strings) < 2:
        return ''.join(strings)
    elif len(strings) == 2:
        return sep_b.join(strings)
    else:
        return sep_a.join(strings[:-1]) + sep_b + strings[-1]
        
def to_hebrew(output):
    def get_injured_count_hebrew(data):
        severity_light_count = data.get('light_injured_count')
        if severity_light_count == 0:
            severity_light_count_text = ''
        elif severity_light_count == 1:
            severity_light_count_text = 'פצוע אחד קל'
        else:
            severity_light_count_text = f'{severity_light_count} פצועים קל'

        severity_severe_count = data.get('severe_injured_count')
        if severity_severe_count == 0:
            severity_severe_count_text = ''
        elif severity_severe_count == 1:
            severity_severe_count_text = 'פצוע אחד קשה'
        else:
            severity_severe_count_text = f'{severity_severe_count} פצועים קשה'

        severity_fatal_count = data.get('killed_count')
        if severity_fatal_count == 0:
            severity_fatal_count_text = ''
        elif severity_fatal_count == 1:
            severity_fatal_count_text = 'הרוג אחד'
        else:
            severity_fatal_count_text = f'{severity_fatal_count} הרוגים'
        return join_hebrew_strings(list(filter(lambda s: s != '', [severity_fatal_count_text, severity_severe_count_text, severity_light_count_text])))
        
    
    def most_severe_accidents_table_hebrew():
        date_range = output.get('meta').get('dates_comment').get('date_range')
        most_severe_accidents_table = list(filter(lambda widget: widget.get('name') == 'most_severe_accidents_table', output.get('widgets')))[0]
        most_severe_accidents_table_items = most_severe_accidents_table.get('data').get('items')
        
        if len(most_severe_accidents_table_items) == 1:
            text = " התאונה החמורה האחרונה שהתרחשה בכביש" 
        elif len(most_severe_accidents_table_items) > 1:
            text = f"\u202b{len(most_severe_accidents_table_items)}\u202c התאונות החמורות האחרונות שהתרחשו בכביש " 
        text += f" {output.get('meta').get('location_info').get('road1')} במקטע {output.get('meta').get('location_info').get('road_segment_name')} בין השנים {date_range[0]}-{date_range[1]}:\n"
        # todo: change סוג תאונה to the actual type
        text += '\n'.join([f'בתאריך {item.get("date")} בשעה {item.get("hour")} התרחשה תאונה מסוג {"סוג תאונה"}, נפגעים: {get_injured_count_hebrew(item)}.' for item in most_severe_accidents_table_items])        

        return text
    
    def head_on_collisions_comparison_percentage_hebrew():
        def get_fatal_accidents_percentage(item):
            frontal_accidents_count = list(filter(lambda x: x.get('desc') == 'frontal',item))[0].get('count')
            other_accidents_count = list(filter(lambda x: x.get('desc') == 'others',item))[0].get('count')
            total = frontal_accidents_count + other_accidents_count
            if total == 0:
                return None
            
            return round(frontal_accidents_count / total * 100)

        date_range = output.get('meta').get('dates_comment').get('date_range')
        head_on_collisions_comparison = list(filter(lambda widget: widget.get('name') == 'head_on_collisions_comparison', output.get('widgets')))
        if len(head_on_collisions_comparison) == 0:
            return ''
        else:
            head_on_collisions_comparison = head_on_collisions_comparison[0]
        head_on_collisions_comparison_items = head_on_collisions_comparison.get('data').get('items')
        
        specific_road_segment_fatal_accidents = head_on_collisions_comparison_items.get('specific_road_segment_fatal_accidents')        
        specific_road_segment_fatal_accidents_percentage = get_fatal_accidents_percentage(specific_road_segment_fatal_accidents)
        all_roads_fatal_accidents = head_on_collisions_comparison_items.get('all_roads_fatal_accidents')
        all_roads_fatal_accidents_percentage = get_fatal_accidents_percentage(all_roads_fatal_accidents)
        text = f'אחוז התאונות הקטלניות החזיתיות בשנים {date_range[0]}-{date_range[1]} בכלל הכבישים הבינעירוניים בארץ עומד על: {all_roads_fatal_accidents_percentage}%. בכביש {output.get("meta").get("location_info").get("road1")} במקטע {output.get("meta").get("location_info").get("road_segment_name")} ניתן לראות אחוז גבוה יחסית של תאונות קטלניות חזיתיות העומד על: {specific_road_segment_fatal_accidents_percentage}%'

        return text
        
        

    def injured_count_by_severity_hebrew():
        date_range = output.get('meta').get('dates_comment').get('date_range')
        injured_count_by_severity = list(filter(lambda widget: widget.get('name') == 'injured_count_by_severity', output.get('widgets')))
        if len(injured_count_by_severity) == 0:
            return ''
        else:
            injured_count_by_severity = injured_count_by_severity[0]

        severity_light_count = injured_count_by_severity.get('data').get('items').get('light_injured_count')
        if severity_light_count == 0:
            severity_light_count_text = ''
        elif severity_light_count == 1:
            severity_light_count_text = 'פצוע אחד קל'
        else:
            severity_light_count_text = f'{severity_light_count} פצועים קל'

        severity_severe_count = injured_count_by_severity.get('data').get('items').get('severe_injured_count')
        if severity_severe_count == 0:
            severity_severe_count_text = ''
        elif severity_severe_count == 1:
            severity_severe_count_text = 'פצוע אחד קשה'
        else:
            severity_severe_count_text = f'{severity_severe_count} פצועים קשה'

        severity_fatal_count = injured_count_by_severity.get('data').get('items').get('killed_count')
        if severity_fatal_count == 0:
            severity_fatal_count_text = ''
        elif severity_fatal_count == 1:
            severity_fatal_count_text = 'הרוג אחד'
        else:
            severity_fatal_count_text = f'{severity_fatal_count} הרוגים'
        total_accidents_count = injured_count_by_severity.get('data').get('items').get('total_injured_count')

        if output.get('meta').get('resolution') == 'STREET':
            text = f"בעיר {output.get('meta').get('location_info').get('yishuv_name')} ברחוב {output.get('meta').get('location_info').get('street1_hebrew')} "
        elif output.get('meta').get('resolution') == 'SUBURBAN_ROAD':
            text = f"בכביש {output.get('meta').get('location_info').get('road1')} במקטע {output.get('meta').get('location_info').get('road_segment_name')} "            
        else:
            raise Exception(f"cannot convert to hebrew for resolution : {output.get('meta').get('resolution')}")
        text += f"בשנים {date_range[0]}-{date_range[1]} נפגעו {total_accidents_count} אנשים כתוצאה מתאונות דרכים, מתוכן: "
        text += f"{join_hebrew_strings([severity_fatal_count_text, severity_severe_count_text, severity_light_count_text])}"
        text = f".{text}"
        return text

    def accident_count_by_severity_hebrew():
        date_range = output.get('meta').get('dates_comment').get('date_range')
        accident_count_by_severity = list(filter(lambda widget: widget.get('name') == 'accident_count_by_severity', output.get('widgets')))[0]
        severity_light_count = accident_count_by_severity.get('data').get('items').get('severity_light_count')
        if severity_light_count == 0:
            severity_light_count_text = ''
        elif severity_light_count == 1:
            severity_light_count_text = 'קלה אחת' 
        else:
            severity_light_count_text = f'{severity_light_count} קלות'

        severity_severe_count = accident_count_by_severity.get('data').get('items').get('severity_severe_count')
        if severity_severe_count == 0:
            severity_severe_count_text = ''
        elif severity_severe_count == 1:
            severity_severe_count_text = 'קשה אחת'
        else:
            severity_severe_count_text = f'{severity_severe_count} קשות'

        severity_fatal_count = accident_count_by_severity.get('data').get('items').get('severity_fatal_count')
        if severity_fatal_count == 0:
            severity_fatal_count_text = ''
        elif severity_fatal_count == 1:
            severity_fatal_count_text = 'קטלנית אחת'
        else:
            severity_fatal_count_text = f'{severity_fatal_count} קטלניות'
        total_accidents_count = accident_count_by_severity.get('data').get('items').get('total_accidents_count')


        if output.get('meta').get('resolution') == 'STREET':
            text = f"בעיר {output.get('meta').get('location_info').get('yishuv_name')} ברחוב {output.get('meta').get('location_info').get('street1_hebrew')} "
        elif output.get('meta').get('resolution') == 'SUBURBAN_ROAD':
            text = f"בכביש {output.get('meta').get('location_info').get('road1')} במקטע {output.get('meta').get('location_info').get('road_segment_name')} "            
        else:
            raise Exception(f"cannot convert to hebrew for resolution : {output.get('meta').get('resolution')}")
        text += f"בשנים {date_range[0]}-{date_range[1]} התרחשו {total_accidents_count} תאונות דרכים, מתוכן: "
        text += f"{join_hebrew_strings([severity_fatal_count_text, severity_severe_count_text, severity_light_count_text])}"
        text = f".{text}"
        return text


    result = {}
    try:
        result['injured_count_by_severity'] = injured_count_by_severity_hebrew()
        result['accident_count_by_severity'] = accident_count_by_severity_hebrew()
        result['most_severe_accidents_table'] = most_severe_accidents_table_hebrew()
        result['head_on_collisions_comparison_percentage_hebrew'] = head_on_collisions_comparison_percentage_hebrew()

        return result
    except Exception as exception:
        result['error'] = exception
      
