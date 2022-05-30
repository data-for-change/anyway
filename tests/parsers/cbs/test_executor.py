from unittest.mock import MagicMock

import pytest

from anyway.parsers.cbs.executor import main

@pytest.fixture
def mock_s3_data_retriever(monkeypatch):
    monkeypatch.setattr('anyway.parsers.cbs.executor.S3DataRetriever', MagicMock())

@pytest.fixture
def mock_shutil(monkeypatch):
    monkeypatch.setattr('anyway.parsers.cbs.executor.shutil', MagicMock())

def test_import_streets_is_called_once_when_source_is_s3(monkeypatch, mock_s3_data_retriever, mock_shutil):
    # Arrange
    import_streets_mock = MagicMock()
    monkeypatch.setattr('anyway.parsers.cbs.executor.import_streets_into_db', import_streets_mock)
    monkeypatch.setattr('anyway.parsers.cbs.executor.load_existing_streets', MagicMock())
    monkeypatch.setattr('anyway.parsers.cbs.executor.delete_cbs_entries', MagicMock())
    monkeypatch.setattr('anyway.parsers.cbs.executor.fill_db_geo_data', MagicMock())
    monkeypatch.setattr('anyway.parsers.cbs.executor.create_tables', MagicMock())

    # Act
    main(batch_size=MagicMock(), source='s3')

    # Assert
    import_streets_mock.assert_called_once()

