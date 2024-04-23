import logging
from typing import Optional
from anyway.request_params import RequestParams
from anyway.widgets.widget import Widget
from anyway.backend_constants import BE_CONST
RC = BE_CONST.ResolutionCategories


class RoadSegmentWidget(Widget):
    # location_accuracy = 1 (עיגון מדויק) OR location_accuracy = 4 (מרכז קילומטר)
    __LOCATION_ACCURACY_FILTER: Optional[dict] = {"location_accuracy": [1, 4]}

    def __init__(self, request_params: RequestParams):
        if not RoadSegmentWidget.is_sub_urban(request_params):
            logging.error(
                f"RoadSegmentWidget initialized with missing location fields:{request_params}"
            )
            raise ValueError("SubUrban fields missing")
        super().__init__(request_params)

    @staticmethod
    def is_sub_urban(request_params: RequestParams) -> bool:
        return (
            request_params is not None
            and "road1" in request_params.location_info
            and (
                "road_segment_name" in request_params.location_info
                or "road_segment_id" in request_params.location_info
            )
        )

    @staticmethod
    def is_relevant(request_params: RequestParams) -> bool:
        return RoadSegmentWidget.is_sub_urban(request_params)

    @classmethod
    def get_location_accuracy_filter(cls, _: RC) -> Optional[dict]:
        return cls.__LOCATION_ACCURACY_FILTER
