def tweet_with_accident_veichle_and_person(text):
    """
    check if tweet contains words indicating an accident between person and veichle
    :param text: tweet text
    :return: boolean, true if tweet contains words, false for others
    """
    if ((u'הולך רגל' in text or u'הולכת רגל' in text or u'נהג' in text
         or u'אדם' in text)
            and (u'רכב' in text or u'מכונית' in text or u'אופנוע' in text
                 or u"ג'יפ" in text or u'טרקטור' in text or u'משאית' in text
                 or u'אופניים' in text or u'קורקינט' in text)):
        return True
    return False

def tweet_with_car_accident(text):
    """
    check if tweet contains words indicating a car accident
    :param text: tweet text
    :return: boolean, true if tweet contains words, false for others
    """
    if u'תאונת דרכים' in text or u'ת.ד' in text:
        return True
    return False


def tweet_with_veichles(text):
    """
    check if tweet contains veichle word
    :param text: tweet text
    :return: boolean, true if tweet contains veichle, false for others
    """
    if u'רכב' in text or u'מכונית' in text or u'אופנוע' in text or u"ג'יפ" in text or u'טרקטור' in text or u'משאית' in text or \
        u'אופניים' in text or u'קורקינט' in text:
        return True
    return False



def classify_tweets(text):
    """
    classify tweets for tweets about car accidents and others
    :param text: tweet text
    :return: boolean, true if tweet is about car accident, false for others
    """
    return text.startswith(u'בשעה') and (tweet_with_accident_veichle_and_person(text) or tweet_with_car_accident(text) or tweet_with_veichles(text))


def classify_ynet(text):
    """
    classify ynet news flash for news flash about car accidents and others
    :param text: news flash text
    :return: boolean, true if news flash is about car accident, false for others
    """
    return ((u'תאונ' in text and u'תאונת עבודה' not in text and u'תאונות עבודה' not in text)
            or ((u'רכב' in text or u'אוטובוס' in text or u"ג'יפ" in text
                 or u'משאית' in text or u'קטנוע' in text or u'טרקטור'
                 in text or u'אופנוע' in text or u'אופניים' in text or u'קורקינט'
                 in text or u'הולך רגל' in text or u'הולכת רגל' in text
                 or u'הולכי רגל' in text) and
                (u'פגע' in text or u'פגיע' in text or u'פגוע' in text or
                 u'הרג' in text or u'הריג' in text or u'הרוג' in text or
                 u'פצע' in text or u'פציע' in text or u'פצוע' in text or
                 text or u'התנגש' in text or u'התהפך'
                 in text or u'התהפכ' in text))) and \
           (u' ירי ' not in text and not text.startswith(u' ירי') and
            u' ירייה ' not in text and not text.startswith(u' ירייה') and
            u' יריות ' not in text and not text.startswith(u' יריות'))
