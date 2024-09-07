from anyway.widgets.widget import Widget
from anyway.widgets.widget import register
from anyway.request_params import RequestParams
from typing import Dict, Optional
# noinspection PyProtectedMember
from flask_babel import _
import logging


@register
class VisionZeroBikeWidget(Widget):
    name: str = "vision_zero_bike"
    files = [__file__]

    def __init__(self, request_params: RequestParams):
        if request_params.news_flash_description is None:
            logging.error(f"VisionZeroBikeWidget initialized with missing description field : {request_params}")
        super().__init__(request_params)
        self.information = _("Main principles in zero vision's bike transportation development")
        self.rank = 33

    def generate_items(self) -> None:
        self.items = {"image_src": "vision_zero_bike"}

    @staticmethod
    def is_included_according_to_request_params(request_params: RequestParams) -> bool:
        return (request_params.news_flash_description and
                "אופניים" in request_params.news_flash_description) or\
               (request_params.news_flash_title and "אופניים" in request_params.news_flash_title)

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        items["data"]["text"] = {"title": _("Bike transportation development solution")}
        return items

    @classmethod
    def update_result(cls, request_params: RequestParams, cached_items: Dict) -> Optional[Dict]:
        return cached_items if cls.is_included_according_to_request_params(request_params) else None

    @staticmethod
    def is_relevant(request_params: RequestParams) -> bool:
        return request_params.news_flash_description is not None
