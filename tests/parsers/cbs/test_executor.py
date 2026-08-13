from pathlib import Path
from shutil import copyfile
from unittest.mock import MagicMock

import pandas as pd
import pytest

from anyway.app_and_db import app, db
from anyway.models import (
    AccidentMarker,
    AccidentMarkerView,
    CBSLocations,
    Involved,
    InvolvedMarkerView,
    InvolvedView,
    SDAccident,
    SDInvolved,
    Vehicle,
    VehicleMarkerView,
    VehiclesView,
)
from anyway.parsers.cbs import executor
from anyway.parsers.cbs.exceptions import CBSParsingFailed

TEMPLATE_CBS_DIRECTORY = Path("static/data/cbs/accidents_type_1/H20191111")
TEMPLATE_BATCH_NAME = "H20191111"
TEMPLATE_ACCIDENT_ID = 2019000069
REPLACEMENT_ACCIDENT_ID = 1
REPLACEMENT_PROVIDER_CODES = (1, 3)
ACCIDENT_YEAR = 2019
ACCIDENT_COLUMN = "TeunaID_FKT"
PROVIDER_COLUMN = "SemelSugTikLMS"
FAILURE_MESSAGE = "failure before commit"

RAW_CBS_MODELS = (
    AccidentMarker,
    Vehicle,
    Involved,
)

HEBREW_MODELS = (
    AccidentMarkerView,
    VehiclesView,
    InvolvedView,
    VehicleMarkerView,
    InvolvedMarkerView,
)

DERIVED_MODELS = (
    CBSLocations,
    SDAccident,
    SDInvolved,
)

AFFECTED_MODELS = (
    *RAW_CBS_MODELS,
    *HEBREW_MODELS,
    *DERIVED_MODELS,
)


def snapshot_table(model):
    columns = list(model.__table__.columns)
    primary_key = list(model.__table__.primary_key.columns)
    rows = db.session.query(*columns).order_by(*primary_key).all()
    return [
        tuple(None if value is None else str(value) for value in row)
        for row in rows
    ]


def snapshot_affected_tables():
    return {model.__tablename__: snapshot_table(model) for model in AFFECTED_MODELS}


def assert_preloaded_data_exists():
    assert (
        AccidentMarker.query.filter(
            AccidentMarker.id == TEMPLATE_ACCIDENT_ID,
            AccidentMarker.provider_code == 1,
            AccidentMarker.accident_year == ACCIDENT_YEAR,
        ).count()
        == 1
    )

    assert (
        Vehicle.query.filter(
            Vehicle.accident_id == TEMPLATE_ACCIDENT_ID,
            Vehicle.provider_code == 1,
            Vehicle.accident_year == ACCIDENT_YEAR,
        ).count()
        > 0
    )

    assert (
        Involved.query.filter(
            Involved.accident_id == TEMPLATE_ACCIDENT_ID,
            Involved.provider_code == 1,
            Involved.accident_year == ACCIDENT_YEAR,
        ).count()
        > 0
    )


def find_template_file(suffix):
    matches = list(TEMPLATE_CBS_DIRECTORY.glob(f"*{suffix}"))
    assert len(matches) == 1, f"Expected one {suffix} file in {TEMPLATE_CBS_DIRECTORY}"
    return matches[0]


def select_template_row(dataframe):
    rows = dataframe.loc[dataframe[ACCIDENT_COLUMN] == TEMPLATE_ACCIDENT_ID].copy()
    assert not rows.empty, (
        f"Accident {TEMPLATE_ACCIDENT_ID} is missing from the CBS fixture"
    )
    return rows.iloc[[0]]


def rewrite_as_replacement_row(row, provider_code):
    row = row.copy()
    row[ACCIDENT_COLUMN] = REPLACEMENT_ACCIDENT_ID
    row[PROVIDER_COLUMN] = provider_code
    return row


def write_minimal_cbs_table(suffix, target_dir, provider_code):
    dataframe = pd.read_csv(
        find_template_file(suffix), encoding=executor.CONTENT_ENCODING
    )
    row = rewrite_as_replacement_row(select_template_row(dataframe), provider_code)
    row.to_csv(
        target_dir / f"{TEMPLATE_BATCH_NAME}{suffix}",
        index=False,
        encoding=executor.CONTENT_ENCODING,
    )


def copy_required_lookup_files(target_dir):
    for suffix in ("Dictionary.csv", "DicStreets.csv"):
        copyfile(
            find_template_file(suffix),
            target_dir / f"{TEMPLATE_BATCH_NAME}{suffix}",
        )


def create_replacement_cbs_directory(tmp_path):
    """Create replacement input from the template CBS fixture.

    Select one accident and one related vehicle/involved row, change the
    accident ID, and duplicate the resulting dataset for providers 1 and 3.
    """
    root = tmp_path / "cbs"
    for provider_code in REPLACEMENT_PROVIDER_CODES:
        target = root / f"accidents_type_{provider_code}" / TEMPLATE_BATCH_NAME
        target.mkdir(parents=True)
        for suffix in ("AccData.csv", "VehData.csv", "InvData.csv"):
            write_minimal_cbs_table(suffix, target, provider_code)
        copy_required_lookup_files(target)
    return root


def configure_replacement_import(monkeypatch, replacement_directory):
    monkeypatch.setattr(
        executor.ImporterUI,
        "source_path",
        lambda self: str(replacement_directory),
    )
    monkeypatch.setattr(
        executor.ImporterUI,
        "is_delete_all",
        lambda self: True,
    )


def count_replacement_rows(model, accident_id_column):
    return (
        model.query.filter(
            accident_id_column == REPLACEMENT_ACCIDENT_ID,
            model.provider_code.in_(REPLACEMENT_PROVIDER_CODES),
            model.accident_year == ACCIDENT_YEAR,
        ).count()
    )


def assert_replacement_reached_raw_and_safety_data_tables():
    expected_rows = len(REPLACEMENT_PROVIDER_CODES)

    # Raw CBS import completed for both providers.
    assert count_replacement_rows(AccidentMarker, AccidentMarker.id) == expected_rows
    assert count_replacement_rows(Vehicle, Vehicle.accident_id) == expected_rows
    assert count_replacement_rows(Involved, Involved.accident_id) == expected_rows

    # Derived safety-data generation also completed.
    assert count_replacement_rows(SDAccident, SDAccident.accident_id) == expected_rows
    assert count_replacement_rows(SDInvolved, SDInvolved.accident_id) == expected_rows


def fail_when_pipeline_attempts_to_commit(monkeypatch):
    def fail_commit():
        assert_replacement_reached_raw_and_safety_data_tables()
        raise RuntimeError(FAILURE_MESSAGE)

    monkeypatch.setattr(db.session, "commit", fail_commit)


def assert_tables_unchanged(before, after):
    for table_name, original_rows in before.items():
        assert after[table_name] == original_rows, (
            f"{table_name} changed despite rollback"
        )


@pytest.fixture
def mock_s3_data_retriever(monkeypatch):
    monkeypatch.setattr("anyway.parsers.cbs.executor.S3DataRetriever", MagicMock())


@pytest.fixture
def mock_shutil(monkeypatch):
    monkeypatch.setattr("anyway.parsers.cbs.executor.shutil", MagicMock())


def test_import_streets_is_called_once_when_source_is_s3(
    monkeypatch, mock_s3_data_retriever, mock_shutil
):
    # Arrange
    delete_cbs_entries = MagicMock()
    monkeypatch.setattr("anyway.parsers.cbs.executor.delete_cbs_entries", delete_cbs_entries)
    monkeypatch.setattr("anyway.parsers.cbs.executor.fill_db_geo_data", MagicMock())
    monkeypatch.setattr("anyway.parsers.cbs.executor.create_tables", MagicMock())
    monkeypatch.setattr(
        "anyway.parsers.cbs.executor.recreate_table_for_location_extraction", MagicMock()
    )
    monkeypatch.setattr("anyway.parsers.cbs.executor.sd_utils.load_data", MagicMock())
    monkeypatch.setattr("anyway.parsers.cbs.executor.db.session.commit", MagicMock())

    # Act
    executor.main(batch_size=MagicMock(), source="s3")

    # Assert
    delete_cbs_entries.assert_called_once()


def test_cbs_parsing_failed_is_raised_when_something_bad_happens(monkeypatch):
    monkeypatch.setattr(
        "anyway.parsers.cbs.executor._import_from_s3", MagicMock(return_value=0)
    )
    monkeypatch.setattr("anyway.parsers.cbs.executor.fill_db_geo_data", MagicMock())
    monkeypatch.setattr(
        "anyway.parsers.cbs.executor.create_tables",
        MagicMock(side_effect=Exception("something bad")),
    )
    rollback = MagicMock()
    monkeypatch.setattr("anyway.parsers.cbs.executor.db.session.rollback", rollback)

    with pytest.raises(
        CBSParsingFailed,
        match="Exception occurred while loading the cbs data: something bad",
    ):
        executor.main(batch_size=MagicMock(), source="s3")

    rollback.assert_called_once()


#The test asserts data exists before import, creates replacement input, 
#asserts data was imported, triggers rollback before final commit,
#and asserts final snapshot matches original snapshot.
@pytest.mark.partial_db
def test_failed_cbs_import_preserves_existing_data(monkeypatch, tmp_path):
    """A failed CBS replacement import must preserve the existing database."""

    with app.app_context():
        assert_preloaded_data_exists()
        original_state = snapshot_affected_tables()

        replacement_directory = create_replacement_cbs_directory(tmp_path)
        configure_replacement_import(monkeypatch, replacement_directory)
        fail_when_pipeline_attempts_to_commit(monkeypatch)

        with pytest.raises(CBSParsingFailed, match=FAILURE_MESSAGE):
            executor.main(batch_size=100, source="local_dir_for_tests_only")

        db.session.expire_all()
        state_after_rollback = snapshot_affected_tables()
        assert_tables_unchanged(before=original_state, after=state_after_rollback)
