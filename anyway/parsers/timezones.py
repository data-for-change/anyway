from datetime import datetime, timezone, timedelta

ISREAL_SUMMER_TIMEZONE = timezone(offset=timedelta(hours=3))


def is_tz_aware(dt):
    return dt.tzinfo.utcoffset(dt) is not None and dt.tzinfo is not None


def parse_creation_datetime(raw_date: str):
    """Unified time format detection and parsing.

    Examples:
    ynet: 'Sun, 31 May 2020 11:26:18 +0300'
    twitter: 'Sun May 31 08:26:18 +0000 2020'
    walla: 'Sun, 31 May 2020 08:26:18 GMT' or like ynet
    """
    try:
        # +0200 or +0300 depending on daylight saving time (ynet or walla)
        time = datetime.strptime(raw_date, "%a, %d %b %Y %H:%M:%S %z")
    except ValueError:
        try:
            # +0000 (twitter)
            time = datetime.strptime(raw_date, "%a %b %d %H:%M:%S %z %Y")
        except ValueError:
            # GMT (walla)
            time = datetime.strptime(raw_date, "%a, %d %b %Y %H:%M:%S %Z")
            time = time.replace(tzinfo=timezone.utc)
    assert is_tz_aware(time)
    time = time.astimezone(tz=ISREAL_SUMMER_TIMEZONE)
    return time


def from_db(date):
    # DB holds timezone as UTC; to get local-timezone pretty-printing, we change it on load time
    return date.astimezone(tz=ISREAL_SUMMER_TIMEZONE)
