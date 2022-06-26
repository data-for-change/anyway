import logging
from collections import defaultdict
from typing import Dict

from sqlalchemy import func, or_
from sqlalchemy.sql.elements import and_
from flask_babel import _
from anyway.request_params import RequestParams
from anyway.app_and_db import db
from anyway.backend_constants import InjurySeverity, InjuredType, BE_CONST
from anyway.widgets.widget_utils import (
    add_empty_keys_to_gen_two_level_dict,
    gen_entity_labels,
    format_2_level_items,
)
from anyway.models import NewsFlash, InvolvedMarkerView
from anyway.widgets.widget import register
from anyway.widgets.urban_widgets.urban_widget import UrbanWidget


@register
class InjuredAccidentsWithPedestriansWidget(UrbanWidget):
    name: str = "injured_accidents_with_pedestrians"

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params, type(self).name)
        self.rank = 18
        self.information = "Injured and killed pedestrians by severity and year"

    def validate_parameters(self, yishuv_name, street1_hebrew):
        # TODO: validate each parameter and display message accordingly
        return (
            yishuv_name is not None
            and street1_hebrew is not None
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
            yishuv_name = self.request_params.location_info.get("yishuv_name")
            street1_hebrew = self.request_params.location_info.get("street1_hebrew")

            if not self.validate_parameters(yishuv_name, street1_hebrew):
                logging.exception(
                    f"Could not validate parameters for {NewsFlash} : {self.request_params.news_flash_obj.id}"
                )
                return None

            query = (
                db.session.query(InvolvedMarkerView)
                .with_entities(
                    InvolvedMarkerView.accident_year,
                    InvolvedMarkerView.injury_severity,
                    func.count().label("count"),
                )
                .filter(InvolvedMarkerView.accident_yishuv_name == yishuv_name)
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
                        InvolvedMarkerView.street1_hebrew == street1_hebrew,
                        InvolvedMarkerView.street2_hebrew == street1_hebrew,
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
            self.items = format_2_level_items(res, None, InjurySeverity, total=True)

        except Exception as e:
            logging.error(f"InjuredAccidentsWithPedestriansWidget.generate_items(): {e}")
            raise

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        items["data"]["text"] = {
            "title": _("Pedestrian accidents by severity and year")
            + f" - {request_params.location_text}",
            "labels": {**gen_entity_labels(InjurySeverity),
            **{BE_CONST.TOTAL : _("total_injured")}}
        }
        return items
