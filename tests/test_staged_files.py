import pytest
import pandas as pd
from numpy.ma.core import equal

from nmdc_automation.jgi_file_staging.staged_files import get_list_missing_staged_files
from nmdc_automation.jgi_file_staging.jgi_file_metadata import sample_records_to_sample_objects


def test_get_list_missing_staged_files(
    test_db, jgi_staging_config, monkeypatch, tmp_path, grow_analysis_df
):
    import os
    from pathlib import Path
    test_db.samples.drop()
    # Patch DataFrame.to_csv to a no-op to prevent file writes
    monkeypatch.setattr(pd.DataFrame, "to_csv", lambda *args, **kwargs: None)

    project_name = "grow_project"

    # Setup fake directory structure under tmp_path
    project_dirname = f"{project_name}_analysis_projects"

    # Patch config to point to tmp_path
    jgi_staging_config["PROJECT"]["analysis_projects_dir"] = str(tmp_path)

    base_dir = tmp_path / project_dirname
    base_dir.mkdir(parents=True)

    # Prepare the test database
    sample_objs = sample_records_to_sample_objects(grow_analysis_df.to_dict("records"))
    try:
        test_db.samples.insert_many([so.model_dump() for so in sample_objs])
        # Add fake files
        for row in grow_analysis_df.loc[0:8, :].itertuples():
            analysis_proj_dir = base_dir / row.apGoldId
            analysis_proj_dir.mkdir() if not analysis_proj_dir.exists() else analysis_proj_dir
            (analysis_proj_dir / row.file_name).touch()
        # Run the function under test
        missing_files = get_list_missing_staged_files(project_name, jgi_staging_config, test_db)

        # Check type and basic properties
        assert isinstance(missing_files, list)
        assert len(missing_files) == 1

        # Optional: assert no CSV files were written
        assert not any(tmp_path.glob("*.csv"))
        assert equal(missing_files[0], {'apGoldId': 'Ga0499978', 'file_name': 'rqc-stats.pdf'})
    finally:
        test_db.samples.drop()
