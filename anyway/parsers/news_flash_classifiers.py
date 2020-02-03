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
    accident_words = [u'תאונ', ]
    working_accidents_words = [u'תאונת עבודה', u'תאונות עבודה']
    involved_words = [u'רכב', u'אוטובוס', u"ג'יפ", u'משאית', u'קטנוע', u'טרקטור',
                      u'אופנוע', u'אופניים', u'קורקינט', u'הולך רגל', u'הולכת רגל',
                      u'הולכי רגל']
    hurt_words = [u'פגע', u'פגיע', u'פגוע', u'הרג', u'הריג', u'הרוג', u'פצע', 'פציע',
                  u'פצוע', u'התנגש', u'התהפך', u'התהפכ']
    shooting_words = [u' ירי ', u' ירייה ', u' יריות ']
    shooting_startswith = [u' ירי', u' ירייה', u' יריות']

    explicit_accident = any([val in text for val in accident_words])
    not_work_accident = all([val not in text for val in working_accidents_words])
    involved = any([val in text for val in involved_words])
    hurt = any([val in text for val in hurt_words])
    no_shooting = all([val not in text for val in shooting_words]) and all(
        [not text.startswith(val) for val in shooting_startswith])

    return ((explicit_accident and not_work_accident) or (involved and hurt)) and no_shooting
