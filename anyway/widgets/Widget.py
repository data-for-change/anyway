import copy
import logging
from typing import Union, Dict, List, Optional, Type

from anyway.RequestParams import RequestParams


class Widget:
    """
    Base class for widgets. Each widget will be a class that is derived from Widget, and instantiated
    with RequestParams and its name.
    The Serialize() method returns the data that the API returns, and has structure that is specified below.
    To add a new widget sub-class:
    - Make is subclass of Widget
    - Set attribute rank
    - Implement method generate_items()
    - Optionally set additional attributes if needed, and alter the returned values of `is_in_cache()` and
      `is_included()` when needed.
    Returned Widget structure:
    `{
        'name': str,
        'data': {
                 'items': list (Array) | dictionary (Object),
                 'text': dictionary (Object) - can be empty
                 },
        'meta': {
                 'rank': int (Integer)
                 }
    }`
    """

    request_params: RequestParams
    name: str
    rank: int
    items: Union[Dict, List]
    text: Dict
    meta: Optional[Dict]

    def __init__(self, request_params: RequestParams, name: str):
        self.request_params = copy.deepcopy(request_params)
        self.name = name
        self.rank = -1
        self.items = {}
        self.text = {}
        self.meta = None
        self.information = ""

    def get_name(self) -> str:
        return self.name

    def get_rank(self) -> int:
        return self.rank

    @staticmethod
    def is_in_cache() -> bool:
        """Whether this widget is stored in the cache"""
        return True

    # noinspection PyMethodMayBeStatic
    def is_included(self) -> bool:
        """Whether this widget is included in the response"""
        return bool(self.items)

    def generate_items(self) -> None:
        """Generates the data of the widget and set it to self.items"""
        pass

    @staticmethod
    def is_relevant(request_params: RequestParams) -> bool:
        return True

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        if "name" in items:
            logging.debug(f"Widget.localize_items: widget {items['name']} should implement localize_items method")
        else:
            logging.error(f"Widget.localize_items: bad input (missing 'name' key):{items}")
        return items

    def serialize(self):
        if not self.items:
            self.generate_items()
        output = {"name": self.name, "data": {}}
        output["data"]["items"] = self.items
        if self.text:
            output["data"]["text"] = self.text
        if self.meta:
            output["meta"] = self.meta
        else:
            output["meta"] = {}
        output["meta"]["rank"] = self.rank
        output["meta"]["information"] = self.information
        return output


def register(widget_class: Type[Widget]) -> Type[Widget]:
    if widgets_dict.get(widget_class.name) is not None:
        logging.error(f"Double register:{widget_class.name}:{widget_class}\n")
    widgets_dict[widget_class.name] = widget_class
    logging.debug(f"register:{widget_class.name}:{widget_class}\n")
    return widget_class


widgets_dict: Dict[str, Type[Widget]] = {}
