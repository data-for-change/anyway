from pytest import fixture
from typing import Set
from anyway.backend_constants import BE_CONST

@fixture
def sources() -> Set[str]:
    return set([item.value for item in BE_CONST.Source])

def test_critical_is_a_valid_source(sources):
    assert 'critical' in sources

def test_critical_is_in_supported_sources():
    assert BE_CONST.Source.CRITICAL in BE_CONST.SUPPORTED_SOURCES