import logging
from anyway.request_params import RequestParams
from anyway.widgets.widget import Widget


class UrbanWidget(Widget):
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
