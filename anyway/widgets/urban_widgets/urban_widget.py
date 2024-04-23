import logging
from typing import Optional
from anyway.request_params import RequestParams
from anyway.widgets.widget import Widget
from anyway.backend_constants import BE_CONST
RC = BE_CONST.ResolutionCategories


class UrbanWidget(Widget):
    # location_accuracy = 1 (עיגון מדויק) OR location_accuracy = 3 (מרכז דרך)
    __LOCATION_ACCURACY_FILTER: Optional[dict] = {"location_accuracy": [1, 3]}

    def __init__(self, request_params: RequestParams):
        if not UrbanWidget.is_urban(request_params):
            logging.error(f"UrbanWidget initialized with missing location fields:{request_params}")
            raise ValueError("Urban fields missing")
        super().__init__(request_params)

    @staticmethod
    def is_urban(request_params: RequestParams) -> bool:
        return (
            request_params is not None
            and "yishuv_name" in request_params.location_info
            and "street1_hebrew" in request_params.location_info
        )

    @staticmethod
    def is_relevant(request_params: RequestParams) -> bool:
        return UrbanWidget.is_urban(request_params)

    @classmethod
    def get_location_accuracy_filter(cls, _: RC) -> Optional[dict]:
        return cls.__LOCATION_ACCURACY_FILTER
