import pytest
import pandas as pd
import ast
import os
from pathlib import Path

from nmdc_automation.jgi_file_staging.staged_files import get_list_missing_staged_files
from nmdc_automation.jgi_file_staging.jgi_file_metadata import sample_records_to_sample_objects
from nmdc_automation.db.nmdc_mongo import get_test_db


@pytest.fixture
def grow_analysis_df(fixtures_dir):
    df = pd.read_csv(os.path.join(fixtures_dir, "grow_analysis_projects.csv"))
    df["file_status"] = "ready"
    df["projects"] = df["projects"].apply(ast.literal_eval)
    return df


@pytest.fixture
def populated_mdb(grow_analysis_df):
    sample_objects = sample_records_to_sample_objects(grow_analysis_df.to_dict("records"))
    mdb = get_test_db()
    mdb.projects.insert_many([so.model_dump() for so in sample_objects])
    return mdb


@pytest.mark.parametrize("project_name,config_file", [
    ("test_project", "test_config.yaml"),
])
def test_get_list_missing_staged_files(
    populated_mdb, project_name, config_file, monkeypatch, tmp_path
):
    # Patch anything that would write to disk (if necessary)
    monkeypatch.setattr(
        "nmdc_automation.jgi_file_staging.staged_files.OUTPUT_FILE", tmp_path / "dummy.csv"
    )
    # Run the function under test
    missing_files = get_list_missing_staged_files(project_name, config_file, populated_mdb)

    # Check type and basic properties
    assert isinstance(missing_files, list)

    # Optional: add more specific assertions here
    # Example: check that no file was written
    assert not any(tmp_path.glob("*.csv"))
