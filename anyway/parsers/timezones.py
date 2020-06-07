from datetime import datetime, timezone, timedelta

ISREAL_SUMMER_TIMEZONE = timezone(offset=timedelta(hours=3))


def parse_creation_datetime(raw_date: str):
    """Unified time format detection and parsing.

    Examples:
    ynet: 'Sun, 31 May 2020 11:26:18 +0300'
    twitter: 'Sun May 31 08:26:18 +0000 2020'
    walla: 'Sun, 31 May 2020 08:26:18 GMT' or like ynet
    """
    try:
        # +0300 (ynet or walla)
        return datetime.strptime(raw_date, "%a, %d %b %Y %H:%M:%S %z").replace(
            tzinfo=ISREAL_SUMMER_TIMEZONE
        )
    except ValueError as ex:
        print(ex)
        try:
            # +0000 (twitter)
            time = datetime.strptime(raw_date, "%a %b %d %H:%M:%S %z %Y")
        except ValueError as ex:
            print(ex)
            # GMT (walla)
            time = datetime.strptime(raw_date, "%a, %d %b %Y %H:%M:%S %Z")
        return time.replace(tzinfo=timezone.utc).astimezone(tz=ISREAL_SUMMER_TIMEZONE)
