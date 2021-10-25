import datetime
from dataclasses import dataclass
from typing import Dict, Any

from anyway.models import NewsFlash


@dataclass
class RequestParams:
    """
    Input for infographics data generation, per api call
    """

    news_flash_obj: NewsFlash
    years_ago: int
    location_text: str
    location_info: Dict[str, Any]
    resolution: Dict
    gps: Dict
    start_time: datetime.date
    end_time: datetime.date
    lang: str

    def __str__(self):
        return f"RequestParams(location_text:{self.location_text}, start_time:{self.start_time}, end_time:{self.end_time}, lang:{self.lang})"