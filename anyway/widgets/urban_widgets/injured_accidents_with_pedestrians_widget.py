import logging
from collections import defaultdict
from typing import Dict

from sqlalchemy import func, or_
from sqlalchemy.sql.elements import and_
from flask_babel import _
from anyway.request_params import RequestParams
from anyway.app_and_db import db
from anyway.backend_constants import InjurySeverity, InjuredType
from anyway.widgets.widget_utils import (
    add_empty_keys_to_gen_two_level_dict,
    gen_entity_labels,
    format_2_level_items,
    add_resolution_location_accuracy_filter,
    get_expression_for_fields,
)
from anyway.models import InvolvedMarkerView
from anyway.widgets.widget import register
from anyway.widgets.urban_widgets.urban_widget import UrbanWidget


@register
class InjuredAccidentsWithPedestriansWidget(UrbanWidget):
    name: str = "injured_accidents_with_pedestrians"
    files = [__file__]

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params)
        self.rank = 18
        self.information = "Injured and killed pedestrians by severity and year"

    def validate_parameters(self, yishuv_symbol, street1):
        # TODO: validate each parameter and display message accordingly
        return (
            yishuv_symbol is not None
            and street1 is not None
            and self.request_params.years_ago is not None
        )

    @staticmethod
    def convert_to_dict(query_results):
        res = defaultdict(
            lambda: {
                InjurySeverity.KILLED.value: 0,
                InjurySeverity.SEVERE_INJURED.value: 0,
                InjurySeverity.LIGHT_INJURED.value: 0,
            }
        )
        for query_result in query_results:
            res[str(query_result.accident_year)][query_result.injury_severity] += query_result.count
        return res

    def generate_items(self) -> None:
        try:
            yishuv_symbol = self.request_params.location_info.get("yishuv_symbol")
            street1 = self.request_params.location_info.get("street1")

            # if not self.validate_parameters(yishuv_symbol, street1_hebrew):
            #     # TODO: this will fail since there is no news_flash_obj in request_params
            #     logging.exception(f"Could not validate parameters yishuv_name + street1_hebrew in widget : {self.name}")
            #     return None

            loc_accuracy = add_resolution_location_accuracy_filter(
                None,
                self.request_params.resolution
            )
            loc_ex = get_expression_for_fields(loc_accuracy, InvolvedMarkerView)
            query = (
                db.session.query(InvolvedMarkerView)
                .with_entities(
                    InvolvedMarkerView.accident_year,
                    InvolvedMarkerView.injury_severity,
                    func.count().label("count"),
                )
                .filter(loc_ex)
                .filter(InvolvedMarkerView.accident_yishuv_symbol == yishuv_symbol)
                .filter(
                    InvolvedMarkerView.injury_severity.in_(
                        [
                            InjurySeverity.KILLED.value,
                            InjurySeverity.SEVERE_INJURED.value,
                            InjurySeverity.LIGHT_INJURED.value,
                        ]
                    )
                )
                .filter(InvolvedMarkerView.injured_type == InjuredType.PEDESTRIAN.value)
                .filter(
                    or_(
                        InvolvedMarkerView.street1 == street1,
                        InvolvedMarkerView.street2 == street1,
                    )
                )
                .filter(
                    and_(
                        InvolvedMarkerView.accident_timestamp >= self.request_params.start_time,
                        InvolvedMarkerView.accident_timestamp <= self.request_params.end_time,
                    )
                )
                .group_by(InvolvedMarkerView.accident_year, InvolvedMarkerView.injury_severity)
            )

            res = add_empty_keys_to_gen_two_level_dict(
                self.convert_to_dict(query.all()),
                [
                    str(year)
                    for year in range(
                        self.request_params.start_time.year, self.request_params.end_time.year + 1
                    )
                ],
                InjurySeverity.codes(),
            )
            self.items = format_2_level_items(res, None, InjurySeverity)

        except Exception as e:
            logging.error(f"InjuredAccidentsWithPedestriansWidget.generate_items(): {e}")
            raise

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        items["data"]["text"] = {
            "title": _("Pedestrian accidents by severity and year"),
            "subtitle": _(request_params.location_text),
            "labels": gen_entity_labels(InjurySeverity),
        }
        return items
