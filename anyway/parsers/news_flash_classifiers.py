def tweet_with_accident_vehicle_and_person(text):
    """
    check if tweet contains words indicating an accident between person and vehicle
    :param text: tweet text
    :return: boolean, true if tweet contains words, false for others
    """
    if ("הולך רגל" in text or "הולכת רגל" in text or "נהג" in text or "אדם" in text) and (
        "רכב" in text
        or "מכונית" in text
        or "אופנוע" in text
        or "ג'יפ" in text
        or "טרקטור" in text
        or "משאית" in text
        or "אופניים" in text
        or "קורקינט" in text
    ):
        return True
    return False


def tweet_with_car_accident(text):
    """
    check if tweet contains words indicating a car accident
    :param text: tweet text
    :return: boolean, true if tweet contains words, false for others
    """
    if "תאונת דרכים" in text or "ת.ד" in text:
        return True
    return False


def tweet_with_vehicles(text):
    """
    check if tweet contains veichle word
    :param text: tweet text
    :return: boolean, true if tweet contains vehicle, false for others
    """
    if (
        "רכב" in text
        or "מכונית" in text
        or "אופנוע" in text
        or "ג'יפ" in text
        or "טרקטור" in text
        or "משאית" in text
        or "אופניים" in text
        or "קורקינט" in text
    ):
        return True
    return False


def classify_tweets(text):
    """
    classify tweets for tweets about car accidents and others
    :param text: tweet text
    :return: boolean, true if tweet is about car accident, false for others
    """
    return text.startswith("בשעה") and (
        tweet_with_accident_vehicle_and_person(text)
        or tweet_with_car_accident(text)
        or tweet_with_vehicles(text)
    )


def classify_organization(source):
    source_to_organization_mapping = {"twitter": "מד״א", "ynet": "ynet", "walla": "וואלה"}
    return source_to_organization_mapping.get(source, source)


def classify_rss(text):
    """
    classify ynet news flash for news flash about car accidents and others
    :param text: news flash text
    :return: boolean, true if news flash is about car accident, false for others
    """
    accident_words = ["תאונ"]
    working_accidents_words = ["תאונת עבודה", "תאונות עבודה"]
    involved_words = [
        "רכב",
        "אוטובוס",
        "ג'יפ",
        "משאית",
        "קטנוע",
        "טרקטור",
        "אופנוע",
        "אופניים",
        "קורקינט",
        "הולך רגל",
        "הולכת רגל",
        "הולכי רגל",
    ]
    hurt_words = [
        "פגע",
        "פגיע",
        "פגוע",
        "הרג",
        "הריג",
        "הרוג",
        "פצע",
        "פציע",
        "פצוע",
        "התנגש",
        "התהפך",
        "התהפכ",
        "החליק",
        "החלק",
    ]
    shooting_words = [" ירי ", " ירייה ", " יריות "]
    shooting_startswith = [" ירי", " ירייה", " יריות"]

    explicit_accident = any([val in text for val in accident_words])
    not_work_accident = all([val not in text for val in working_accidents_words])
    involved = any([val in text for val in involved_words])
    hurt = any([val in text for val in hurt_words])
    no_shooting = all([val not in text for val in shooting_words]) and all(
        [not text.startswith(val) for val in shooting_startswith]
    )

    return ((explicit_accident and not_work_accident) or (involved and hurt)) and no_shooting
