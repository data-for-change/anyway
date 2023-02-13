import logging
from anyway.request_params import RequestParams
from anyway.widgets.widget import Widget


class RoadSegmentWidget(Widget):
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
