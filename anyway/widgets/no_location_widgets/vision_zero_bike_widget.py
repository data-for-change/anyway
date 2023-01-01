from typing import Dict
from anyway.widgets.widget import Widget
from anyway.request_params import RequestParams
from anyway.widgets.widget import register
from typing import Dict
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


    # noinspection PyUnboundLocalVariable
    def is_included(self) -> bool:
        return "אופניים" in self.request_params.news_flash_description

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        items["data"]["text"] = {"title": _("Bike transportation development solution")}
        return items
