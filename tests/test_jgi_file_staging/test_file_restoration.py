"""
Unit tests for the file restoration process in the JGI file staging system.
"""
import os
from unittest.mock import patch, MagicMock
import pytest
from tests.fixtures import db_utils
import pandas as pd

from nmdc_automation.jgi_file_staging.file_restoration import restore_files, update_file_statuses, check_restore_status
from nmdc_automation.jgi_file_staging.jgi_file_metadata import sample_records_to_sample_objects


@patch('nmdc_automation.jgi_file_staging.jgi_file_metadata.requests.post')
def test_restore_files(mock_post, import_config_file, grow_analysis_df, test_db, monkeypatch):
    db_utils.reset_db(test_db)
    test_db.samples.delete_many({})

    # Set the JDP_TOKEN in environment
    monkeypatch.setenv('JDP_TOKEN', 'fake-token')

    # mock API call for file restore request
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        'updated_count': 0, 'restored_count': 4, 'request_id': '220699', 'request_status_url':
            'https://files.jgi.doe.gov/request_archived_files/requests/220699'}

    # insert samples into database
    grow_analysis_df.loc[grow_analysis_df['file_size'] > 30000, 'file_status'] = 'PURGED'
    grow_analysis_df['request_id'] = '220699'
    grow_analysis_df['project'] = 'Gp0587070'
    sample_records = grow_analysis_df.to_dict('records')
    sample_objects = sample_records_to_sample_objects(sample_records)
    test_db.samples.insert_many([sample.model_dump() for sample in sample_objects])

    num_restore_samples = len([m for m in test_db.samples.find({'file_status': 'PURGED'})])
    assert num_restore_samples == 5
    output = restore_files('Gp0587070', import_config_file, test_db)
    assert output == f"requested restoration of {num_restore_samples} files"


@patch('nmdc_automation.jgi_file_staging.jgi_file_metadata.requests.post')
def test_restore_files_no_samples(mock_post, import_config_file, test_db, monkeypatch):
    """
    Test the restore_files function when there are no samples to restore.
    """
    db_utils.reset_db(test_db)
    test_db.samples.delete_many({})

    monkeypatch.setenv('JDP_TOKEN', 'fake-token')

    # Insert samples that are NOT PURGED
    test_db.samples.insert_many([
        {'sample_id': 's1', 'file_status': 'restored', 'project': 'Gp0587070'},
        {'sample_id': 's2', 'file_status': 'restored', 'project': 'Gp0587070'},
    ])

    output = restore_files('Gp0587070', import_config_file, test_db)
    assert output == 'No samples to restore'
    mock_post.assert_not_called()


def test_restore_files_missing_token(import_config_file, test_db, monkeypatch):
    """
    Test that the restore_files function raises a SystemExit when the JDP_TOKEN is not set.
    """
    test_db.samples.delete_many({})
    test_db.samples.insert_one({'projects': 'Gp0587070', 'file_status': 'PURGED'})
    monkeypatch.delenv('JDP_TOKEN', raising=False)

    with pytest.raises(SystemExit):
        restore_files('Gp0587070', import_config_file, test_db)



@patch('nmdc_automation.jgi_file_staging.jgi_file_metadata.requests.post')
def test_restore_files_api_failure(mock_post, import_config_file, test_db, monkeypatch):
    monkeypatch.setenv('JDP_TOKEN', 'fake-token')

    mock_post.return_value.status_code = 500
    mock_post.return_value.text = 'Internal Server Error'

    test_db.samples.insert_one({'projects': 'Gp0587070', 'file_status': 'PURGED', 'file_size': 1, 'jdp_file_id': 'id1'})

    output = restore_files('Gp0587070', import_config_file, test_db)
    assert output == 'Internal Server Error'


@patch('nmdc_automation.jgi_file_staging.jgi_file_metadata.requests.post')
def test_restore_files_with_restore_csv(mock_post, tmp_path, import_config_file, test_db, monkeypatch):
    """
    Test the restore_files function with a restore CSV file.
    """
    monkeypatch.setenv('JDP_TOKEN', 'fake-token')

    # Create restore CSV
    csv_file = tmp_path / 'restore.csv'
    df = pd.DataFrame([{
        'projects': 'Gp0587070',
        'file_status': 'PURGED',
        'file_size': 1,
        'jdp_file_id': 'id1'
    }])
    df.to_csv(csv_file, index=False)

    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {'request_id': '123'}

    output = restore_files('Gp0587070', import_config_file, test_db, restore_csv=str(csv_file))
    assert 'requested restoration of' in output


@patch('nmdc_automation.jgi_file_staging.jgi_file_metadata.requests.post')
def test_restore_files_bad_proxies(mock_post, tmp_path, test_db, monkeypatch):
    # Create a config file with invalid proxies
    config_file = tmp_path / 'config.ini'
    config_file.write_text(
        '[JDP]\nproxies = {bad_json}\nmax_restore_request = 1e13\n[GLOBUS]\nglobus_user_name = user\nmailto = user@example.com\n'
        )

    monkeypatch.setenv('JDP_TOKEN', 'fake-token')

    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {'request_id': '123'}

    test_db.samples.insert_one({'projects': 'Gp0587070', 'file_status': 'PURGED', 'file_size': 1, 'jdp_file_id': 'id1'})

    restore_files('Gp0587070', str(config_file), test_db)
    mock_post.assert_called()

