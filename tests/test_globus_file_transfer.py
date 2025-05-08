"""Test the globus_file_transfer module."""
import ast
import os
from unittest.mock import patch, Mock
import pandas as pd
from pathlib import Path
from testfixtures import Replace, mock_datetime

from nmdc_automation.jgi_file_staging.globus_file_transfer import (
    get_globus_manifest,
    create_globus_batch_file,
    create_globus_dataframe,
    get_project_globus_manifests
)
from nmdc_automation.jgi_file_staging.jgi_file_metadata import sample_records_to_sample_objects


def test_get_globus_manifests(monkeypatch, jgi_staging_config):
    mock_run = Mock()
    process_mocks = []
    side_effects = [
        {"stdout": "ERLowmetatpilot/\nGlobus_Download_201670_File_Manifest.csv\n", "returncode": 0},
        {"stdout": "", "returncode": 0},
        {"stdout": "NGESur0720SPAdes_8/\nRivsedcS19S_0091_2/\nGlobus_Download_201984_File_Manifest.csv", "returncode": 0},
        {"stdout": "", "returncode": 0},
        {"stdout": "ERLowmetatpilot/\nGlobus_Download_201670_File_Manifest.csv", "returncode": 0},
        {"stdout": "", "returncode": 0},
    ]
    for attrs in side_effects:
        p = Mock()
        p.configure_mock(**attrs)
        process_mocks.append(p)

    mock_run.side_effect = process_mocks
    monkeypatch.setattr("nmdc_automation.jgi_file_staging.globus_file_transfer.subprocess.run", mock_run)

    get_globus_manifest(201670, config=jgi_staging_config)
    assert mock_run.call_count == 2
    assert mock_run.mock_calls[0].args[0][2] == "65fa2422-e080-11ec-990f-3b4cfda38030:/73709/R201670"


def test_get_project_globus_manifests(monkeypatch, fixtures_dir, jgi_staging_config, test_db):
    mock_manifest = Mock(side_effect=[
        "Globus_Download_201545_File_Manifest.csv",
        "Globus_Download_201547_File_Manifest.csv",
        "Globus_Download_201572_File_Manifest.csv",
    ])
    monkeypatch.setattr("nmdc_automation.jgi_file_staging.globus_file_transfer.get_globus_manifest", mock_manifest)

    grow_analysis_df = pd.read_csv(os.path.join(fixtures_dir, "grow_analysis_projects.csv"))
    grow_analysis_df['projects'] = grow_analysis_df['projects'].apply(ast.literal_eval)
    grow_analysis_df['analysis_project_id'] = grow_analysis_df['analysis_project_id'].apply(str)
    grow_analysis_df.loc[:5, 'file_status'] = 'in transit'
    grow_analysis_df.loc[:5, 'request_id'] = 201545
    grow_analysis_df.loc[5:8, 'request_id'] = 201547
    grow_analysis_df.loc[9, 'request_id'] = 201572

    sample_objects = sample_records_to_sample_objects(grow_analysis_df.to_dict("records"))

    test_db.samples.insert_many([s.model_dump() for s in sample_objects])

    get_project_globus_manifests("Gp0587070", test_db, config=jgi_staging_config)

    assert mock_manifest.call_count == 2
    assert mock_manifest.mock_calls[0].args[0] == 201547
    assert mock_manifest.mock_calls[1].args[0] == 201572


def test_create_globus_df(monkeypatch, fixtures_dir, jgi_staging_config, grow_analysis_df, test_db):
    grow_analysis_df.loc[:5, 'file_status'] = 'in transit'
    grow_analysis_df.loc[:5, 'request_id'] = 201545
    grow_analysis_df.loc[5:8, 'request_id'] = 201547
    grow_analysis_df.loc[9, 'request_id'] = 201572

    sample_records = grow_analysis_df.to_dict("records")
    sample_objects = sample_records_to_sample_objects(sample_records)
    assert len(sample_objects) == 10

    test_db.samples.insert_many([s.model_dump() for s in sample_objects])

    mock_manifest = Mock(side_effect=[
        "Globus_Download_201545_File_Manifest.csv",
        "Globus_Download_201547_File_Manifest.csv",
        "Globus_Download_201572_File_Manifest.csv",
    ])
    monkeypatch.setattr("nmdc_automation.jgi_file_staging.globus_file_transfer.get_globus_manifest", mock_manifest)

    globus_df = create_globus_dataframe("Gp0587070", jgi_staging_config, test_db)

    assert len(globus_df) == 2
    assert globus_df.loc[0, "directory/path"] == "ERLowmetatpilot/IMG_Data"
    assert globus_df.loc[0, "filename"] == "Ga0502004_genes.fna"
    assert globus_df.loc[0, "file_id"] == "6141a2b4cc4ff44f36c8991a"
    assert globus_df.loc[0, "subdir"] == "R201545"
    assert globus_df.loc[1, "directory/path"] == "ERLowmetatpilot/Metagenome_Report_Tables"
    assert globus_df.loc[1, "md5 checksum"] == "d2b6bf768939813dca151f530e118c50"
    assert globus_df.loc[1, "filename"] == "Table_6_-_Ga0502004_sigs_annotation_parameters.txt"
    assert globus_df.loc[1, "subdir"] == "R201547"



def test_create_globus_batch_file(monkeypatch, fixtures_dir, jgi_staging_config, test_db, grow_analysis_df, tmp_path):
    import os

    mock_manifest = Mock(return_value="Globus_Download_201572_File_Manifest.csv")
    monkeypatch.setattr("nmdc_automation.jgi_file_staging.globus_file_transfer.get_globus_manifest", mock_manifest)
    grow_analysis_df["file_status"] = "ready"
    grow_analysis_df["request_id"] = "201572"

    sample_records = grow_analysis_df.to_dict("records")
    sample_objects = sample_records_to_sample_objects(sample_records)
    assert len(sample_objects) == 10

    test_db.samples.insert_many([s.model_dump() for s in sample_objects])

    # Patch where the file gets written to go into tmp_path
    monkeypatch.setattr("nmdc_automation.jgi_file_staging.globus_file_transfer.OUTPUT_DIR", tmp_path)

    with Replace(
        "nmdc_automation.jgi_file_staging.globus_file_transfer.datetime",
        mock_datetime(2022, 1, 1, 12, 22, 55, delta=0),
    ):
        globus_batch_filename, globus_analysis_df = create_globus_batch_file("Gp0587070", jgi_staging_config, test_db, tmp_path)

    assert globus_batch_filename.endswith(".txt")
    assert tmp_path in Path(globus_batch_filename).parents
    assert os.path.exists(globus_batch_filename)
