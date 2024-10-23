from typing import Dict, Optional
from flask_babel import _
from anyway.widgets.widget import register
from anyway.request_params import RequestParams
from anyway.widgets.urban_widgets.urban_widget import UrbanWidget


@register
class VisionZero105090Widget(UrbanWidget):
    name: str = "vision_zero_10_50_90"
    files = [__file__]

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params)
        self.rank = 38

    def generate_items(self) -> None:
        self.items = {"image_src": "vision_zero_10_50_90"}

    @staticmethod
    def is_included_according_to_request_params(request_params: RequestParams) -> bool:
        for pedestrian_adjective in ["הולך רגל", "הולכת רגל", "הולכי רגל", "הולכות רגל"]:
            if request_params.news_flash_description and pedestrian_adjective in request_params.news_flash_description:
                return True
            if request_params.news_flash_title and pedestrian_adjective in request_params.news_flash_title:
                return True
        return False

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        items["data"]["text"] = {
            "title": _("A speed limit solution on an urban road by vizion zero")
        }
        items["meta"]["information"] = _("A speed limit solution on an urban road by vizion zero")
        return items

    @classmethod
    def update_result(cls, request_params: RequestParams, cached_items: Dict) -> Optional[Dict]:
        return cached_items if cls.is_included_according_to_request_params(request_params) else None
