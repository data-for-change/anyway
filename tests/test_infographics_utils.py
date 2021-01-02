import datetime
from unittest import mock

from anyway.infographics_utils import InjuredCountPerAgeGroupWidget


def test_filter_and_group_injured_count_per_age_group():
    params = mock.MagicMock()
    params.location_info = {"road1": "20"}
    params.start_time = datetime.date(2014, 1, 1)
    params.end_time = datetime.date(2015, 1, 1)
    inj_data = InjuredCountPerAgeGroupWidget(params)
    good_res = {
        "15-19": {"severe": 2},
        "20-24": {"severe": 5},
        "25-34": {"severe": 5},
        "35-44": {"fatal": 2, "severe": 7},
        "45-54": {"severe": 2},
        "55-64": {"severe": 2},
        "unknown": {"severe": 1},
        "65+": {"severe": 5},
    }
    inj_data.generate_items()

    assert inj_data.items == good_res
