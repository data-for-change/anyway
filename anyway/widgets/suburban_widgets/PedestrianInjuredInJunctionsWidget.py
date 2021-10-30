import logging
from datetime import datetime
from typing import List, Dict

from sqlalchemy import func, distinct, desc
from flask_babel import _
from anyway.RequestParams import RequestParams
from anyway.backend_constants import AccidentType
from anyway.models import VehicleMarkerView
from anyway.vehicle_type import VehicleCategory
from anyway.widgets.Widget import register
from anyway.widgets.suburban_widgets.SubUrbanWidget import SubUrbanWidget
from anyway.widgets.widget_utils import run_query, get_query
from anyway.app_and_db import db


@register
class PedestrianInjuredInJunctionsWidget(SubUrbanWidget):
    name: str = "pedestrian_injured_in_junctions"

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params, type(self).name)
        self.rank = 23
        self.text = {"title": "מספר נפגעים הולכי רגל בצמתים - רחוב בן יהודה, תל אביב"}

    def generate_items(self) -> None:
        self.items = PedestrianInjuredInJunctionsWidget.pedestrian_injured_in_junctions_mock_data()

    @staticmethod
    def pedestrian_injured_in_junctions_mock_data():  # Temporary for Frontend
        return [
            {"street name": "גורדון י ל", "count": 18},
            {"street name": "אידלסון אברהם", "count": 10},
            {"street name": "פרישמן", "count": 7},
        ]
