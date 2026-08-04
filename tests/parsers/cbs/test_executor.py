from unittest.mock import MagicMock

import pytest

from anyway.parsers.cbs.exceptions import CBSParsingFailed
from anyway.parsers.cbs.executor import main

@pytest.fixture
def mock_s3_data_retriever(monkeypatch):
    monkeypatch.setattr('anyway.parsers.cbs.executor.S3DataRetriever', MagicMock())

@pytest.fixture
def mock_shutil(monkeypatch):
    monkeypatch.setattr('anyway.parsers.cbs.executor.shutil', MagicMock())

def test_import_streets_is_called_once_when_source_is_s3(monkeypatch, mock_s3_data_retriever, mock_shutil):
    # Arrange
    delete_cbs_entries = MagicMock()
    monkeypatch.setattr('anyway.parsers.cbs.executor.delete_cbs_entries', delete_cbs_entries)
    monkeypatch.setattr('anyway.parsers.cbs.executor.fill_db_geo_data', MagicMock())
    monkeypatch.setattr('anyway.parsers.cbs.executor.create_tables', MagicMock())
    monkeypatch.setattr('anyway.parsers.cbs.executor.recreate_table_for_location_extraction', MagicMock())
    monkeypatch.setattr('anyway.parsers.cbs.executor.sd_utils.load_data', MagicMock())
    monkeypatch.setattr('anyway.parsers.cbs.executor.db.session.commit', MagicMock())

    # Act
    main(batch_size=MagicMock(), source='s3')

    # Assert
    delete_cbs_entries.assert_called_once()


@pytest.mark.skip(reason="Test should be improved when improving testing for cbs pipiline")
def test_cbs_parsing_failed_is_raised_when_something_bad_happens(monkeypatch):
    monkeypatch.setattr('anyway.parsers.cbs.executor._import_from_s3', MagicMock(return_value=0))
    monkeypatch.setattr('anyway.parsers.cbs.executor.fill_db_geo_data', MagicMock())
    monkeypatch.setattr('anyway.parsers.cbs.executor.create_tables',
                        MagicMock(side_effect=Exception('something bad')))
    rollback = MagicMock()
    monkeypatch.setattr('anyway.parsers.cbs.executor.db.session.rollback', rollback)

    with pytest.raises(CBSParsingFailed, match='Exception occurred while loading the cbs data: something bad'):
        main(batch_size=MagicMock(), source='s3')

    rollback.assert_called_once()
