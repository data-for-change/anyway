import re
import string

def extract_tags(txt):
    """
    create tags for flashes
    :param text: flashes content
    :return: tags created for the flash
    """

    txt = txt.translate(txt.maketrans("","", string.punctuation))

    easy_injuries = ['קל']
    hard_injuries = ['קשה', 'אנוש']
    middle_injuries = ['בינוני']
    injuries_words = ['נפצע','פצוע']
    dead_words = ['הרג', 'מות', 'הרוג', 'מוות', 'קטלני']
    veichles = ['אופנוע','רכב', 'אופניים', 'משאית', 'אוטובוס', 'טרקטורון', 'קורקינט', 'טרקטור', 'אופניים חשמליים', 'קורקינט חשמלי']
    men_words = ['גבר', 'צעיר', 'נהג' , 'הולך רגל', 'ילד', 'נער', 'פעוט', 'תינוק', 'קשיש', 'רוכב']
    women_words = ['אישה', 'צעירה', 'נהגת', 'הולכת רגל', 'ילדה', 'נערה', 'פעוטה', 'תינוקת', 'קשישה', 'רוכבת', 'אשה', 'נשים']

    tags = []
    reg_exp = r'\s?{} '

    if any([re.search(reg_exp.format(option), txt) for option in easy_injuries]):
        tags.append('פצועים-קל')
    if any([re.search(reg_exp.format(option), txt) for option in men_words]):
        tags.append('גבר')
    if any([re.search(reg_exp.format(option), txt) for option in women_words]):
        tags.append('אישה')

    if any([option in txt for option in hard_injuries]):
        tags.append('פצועים-קשה')
    if any([option in txt for option in middle_injuries]):
        tags.append('פצועים-בינוני')
    if any([option in txt for option in injuries_words]):
        tags.append('פצועים')
    if any([option in txt for option in dead_words]):
        tags.append('הרוגים')

    veichles_tags = filter(lambda v: v in txt, veichles)
    tags.extend(veichles_tags)

    return ','.join(tags)