from typing import Dict
from flask_babel import _
from anyway.request_params import RequestParams
from anyway.widgets.widget import register
from anyway.widgets.urban_widgets.urban_widget import UrbanWidget


@register
class VisionZero105090Widget(UrbanWidget):
    name: str = "vision_zero_10_50_90_widget"
    files = [__file__]

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params)
        self.rank = 38
        self.information = "A speed limit solution on an urban road"


    def generate_items(self) -> None:
        self.items = {"image_src": "vision_zero_10_50_90"}


    def is_included(self) -> bool:
        for pedestrian_adjective in ["הולך רגל", "הולכת רגל", "הולכי רגל", "הולכות רגל"]:
            if pedestrian_adjective in self.request_params.news_flash_description:
                return True
        return False


    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        items["data"]["text"] = {
            "title": _("A speed limit solution on an urban road")
        }
        return items
