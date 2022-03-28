import logging
from anyway.request_params import RequestParams
from anyway.widgets.widget import Widget
from anyway.backend_constants import BE_CONST


class AllLocationsWidget(Widget):
    def __init__(self, request_params: RequestParams, name: str):
        if not AllLocationsWidget.is_all_locations(request_params):
            logging.error(
                f"AllLocationsWidget initialized with missing location fields:{request_params}"
            )
            raise ValueError("AllLocations fields missing")
        super().__init__(request_params, name)

    @staticmethod
    def is_all_locations(request_params: RequestParams) -> bool:
        return (
            request_params is not None
            and request_params.resolution in BE_CONST.SUPPORTED_RESOLUTIONS
        )

    @staticmethod
    def is_relevant(request_params: RequestParams) -> bool:
        return AllLocationsWidget.is_all_locations(request_params)
