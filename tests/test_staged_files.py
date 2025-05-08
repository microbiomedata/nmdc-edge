import pytest
import pandas as pd


from nmdc_automation.jgi_file_staging.staged_files import get_list_missing_staged_files
from nmdc_automation.jgi_file_staging.jgi_file_metadata import sample_records_to_sample_objects


def test_get_list_missing_staged_files(
    test_db, jgi_staging_config, monkeypatch, tmp_path, grow_analysis_df
):
    import os
    from pathlib import Path

    # Patch DataFrame.to_csv to a no-op to prevent file writes
    monkeypatch.setattr(pd.DataFrame, "to_csv", lambda *args, **kwargs: None)

    project_name = "Gp0587070"

    # Setup fake directory structure under tmp_path
    projects_dir_relative = jgi_staging_config["PROJECT"]["analysis_projects_dir"]
    project_dirname = f"{project_name}_analysis_projects"

    # Patch config to point to tmp_path
    jgi_staging_config["PROJECT"]["analysis_projects_dir"] = str(tmp_path)

    base_dir = tmp_path / project_dirname
    base_dir.mkdir(parents=True)

    analysis_proj_dir = base_dir / "Gp0587070"
    analysis_proj_dir.mkdir()

    # Add fake file
    (analysis_proj_dir / "fakefile.txt").touch()

    # Prepare the test database
    sample_objs = sample_records_to_sample_objects(grow_analysis_df.to_dict("records"))
    test_db.projects.insert_many([so.model_dump() for so in sample_objs])

    # Run the function under test
    missing_files = get_list_missing_staged_files(project_name, jgi_staging_config, test_db)

    # Check type and basic properties
    assert isinstance(missing_files, list)

    # Optional: assert no CSV files were written
    assert not any(tmp_path.glob("*.csv"))

