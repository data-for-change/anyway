import logging
from typing import Dict, List

# noinspection PyProtectedMember
from flask_babel import _
from anyway.backend_constants import InjurySeverity, InjuredType, BE_CONST as BE
from anyway.request_params import RequestParams
from anyway.widgets.all_locations_widgets.killed_injured_count_per_severity_vehicle_widget_utils import (
    KilledInjuredCountPerSeverityVehicleWidgetUtils,
)
from anyway.widgets.all_locations_widgets.all_locations_widget import (
    AllLocationsWidget,
    killed_injured_count_by_severity_vehicle_widget_utils,
)
from anyway.widgets.widget import register
from anyway.widgets.widget_utils import (
    add_empty_keys_to_gen_two_level_dict,
    gen_entity_labels,
    get_location_text,
)
from anyway.vehicle_type import VehicleType, UNKNOWN_VEHICLE_TYPE

INJURY_ORDER = [InjurySeverity.LIGHT_INJURED, InjurySeverity.SEVERE_INJURED, InjurySeverity.KILLED]


@register
class KilledInjuredCountPerVehicleStackedWidget(AllLocationsWidget):
    name: str = "killed_injured_count_by_severity_vehicle_widget"
    files = [__file__, killed_injured_count_by_severity_vehicle_widget_utils.__file__]

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params)
        self.rank = 30

    def generate_items(self) -> None:

        raw_data = KilledInjuredCountPerSeverityVehicleWidgetUtils.filter_and_group_injured_count_per_severity_vehicle(
            self.request_params
        )

        partial_processed = add_empty_keys_to_gen_two_level_dict(
            raw_data,
            [vehicle_type.get_label() for vehicle_type in VehicleType]
            + [InjuredType.PEDESTRIAN.get_label()],
            InjurySeverity.codes(),
        )

        structured_data_list = []
        for vehicle_type_label, severity_dict in partial_processed.items():
            ordered_list = [
                {BE.LKEY: inj.get_label(), BE.VAL: severity_dict.get(inj.value, 0)}
                for inj in INJURY_ORDER
            ]
            structured_data_list.append({BE.LKEY: vehicle_type_label, BE.SERIES: ordered_list})

        self.items = structured_data_list

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        if request_params.lang != "en":
            for item in items["data"]["items"]:

                try:
                    if item["label_key"] == UNKNOWN_VEHICLE_TYPE:
                        item["label_key"] = _(InjuredType.PEDESTRIAN.get_label())
                    else:
                        item["label_key"] = _(
                            VehicleType(item["label_key"]).get_english_display_name()
                        )
                except ValueError:
                    logging.exception(
                        f"KilledInjuredCountPerVehicleTypeStackedWidget.localize_items: item:{item}"
                    )

        location_text = get_location_text(request_params)
        items["data"]["text"] = {
            "title": _("Killed and injured stacked per vehicle type"),
            "subtitle": _(location_text),
            "labels_map": gen_entity_labels(InjurySeverity),
        }
        items["meta"]["information"] = _(
            "Injured count per vehicle type and injury severity. The graph shows all injury severities: fatal, severe, and light."
        )
        return items

    def is_included(self) -> bool:
        killed_injured_count = sum(
            item["value"] for entry in self.items for item in entry["series"]
        )
        return killed_injured_count > 0

    @staticmethod
    def get_injured_type_list() -> List[str]:

        return [injured_type.get_label() for injured_type in InjuredType]
