"""
Unit tests for the file restoration process in the JGI file staging system.
"""
import os
from unittest.mock import patch, MagicMock

from tests.fixtures import db_utils

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


@patch.dict(os.environ, {'JDP_TOKEN': 'dummy_token'})
@patch('nmdc_automation.jgi_file_staging.file_restoration.get_db')
@patch('nmdc_automation.jgi_file_staging.file_restoration.update_file_statuses')
@patch('nmdc_automation.jgi_file_staging.jgi_file_metadata.requests.post')
def test_restore_files_exceed_max(mock_post, mock_update_file_statuses, mock_get_db, import_config_file, grow_analysis_df,
                                  test_db):
    db_utils.reset_db(test_db)

    # Mock requests.post to return a successful response
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        'updated_count': 0,
        'restored_count': 4,
        'request_id': 220699,
        'request_status_url': 'https://files.jgi.doe.gov/request_archived_files/requests/220699',
    }

    # Mock MongoDB connection
    mock_db = MagicMock()
    mock_samples_collection = MagicMock()
    mock_samples_collection.find.return_value = grow_analysis_df.to_dict('records')
    mock_db.samples = mock_samples_collection
    mock_get_db.return_value = mock_db

    # Call the function under test
    output = restore_files('Gp0587070', import_config_file, test_db)
    assert output == "No samples to restore"