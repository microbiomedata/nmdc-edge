import mongomock
import pandas as pd
from pathlib import Path
import pytest


from nmdc_automation.jgi_file_staging.jgi_file_metadata import (
    get_access_token,
    check_access_token,
    get_sequence_id,
    get_analysis_projects_from_proposal_id,
    sample_records_to_sample_objects,
)
from nmdc_automation.jgi_file_staging.models import Sample


FIXTURE_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def mock_get(mocker):
    return mocker.patch(
        "nmdc_automation.jgi_file_staging.jgi_file_metadata.requests.get"
    )


def test_get_access_token(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.text = "ed42ef1556708305eaf8"
    access_token = get_access_token()
    assert access_token == "ed42ef1556708305eaf8"


def test_check_access_token(mock_get, config):
    mock_get.return_value.status_code = 200
    access_token = "ed42ef1556708305eaf8"
    access_token = check_access_token(access_token)
    assert access_token == "ed42ef1556708305eaf8"


def test_check_access_token_invalid(mocker):
    # Mock get_request to fail once, then succeed
    get_request_mock = mocker.patch('nmdc_automation.jgi_file_staging.jgi_file_metadata.get_request')
    get_request_mock.side_effect = [
        None,  # simulate 404 or failure → triggers fallback
        {"some": "data"}  # simulate success after new token
    ]

    # Mock get_access_token to return a new token
    get_access_token_mock = mocker.patch('nmdc_automation.jgi_file_staging.jgi_file_metadata.get_access_token')
    get_access_token_mock.return_value = "ed42ef155670"

    access_token = "ed42ef1556708305eaf8"
    result = check_access_token(access_token)

    assert result == "ed42ef155670"



def test_get_sequence_id(mock_get, config):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = [{"itsApId": 1323348}]
    sequence_id = get_sequence_id(
        "Ga0499978", "ed42ef155670",
    )
    assert sequence_id == [1323348]

    mock_get.return_value.status_code = 403
    sequence_id = get_sequence_id(
        "Ga0499978", "ed42ef155670",
    )
    assert sequence_id == []


def test_get_analysis_projects_from_proposal_id(mock_get):
    mock_data = pd.read_csv(Path.joinpath(FIXTURE_DIR, "grow_gold_analysis_projects.csv")).to_dict("records")
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = mock_data

    gold_analysis_data = get_analysis_projects_from_proposal_id("11111", "ed42ef155670")
    assert gold_analysis_data[0] == {
        "apGoldId": "Ga0499978",
        "apType": "Metagenome Analysis",
        "studyId": "Gs0149396",
        "itsApId": 1323348,
        "projects": "['Gp0587070']",
    }

    assert gold_analysis_data[5] == {
        "apGoldId": "Ga0451723",
        "apType": "Metagenome Analysis",
        "studyId": "Gs0149396",
        "itsApId": 1279803,
        "projects": "['Gp0503551']",
    }


def test_sample_model_instance_creation(monkeypatch, grow_analysis_df):
    sample_dict = grow_analysis_df.to_dict("records")[0]
    sample_model = Sample(**sample_dict)
    assert sample_model.apGoldId == "Ga0499978"
    assert sample_model.studyId == "Gs0149396"
    assert sample_model.itsApId == 1323348
    assert sample_model.projects == ['Gp0587070']
    assert sample_model.biosample_id == "Gb0305643"
    assert sample_model.seq_id == "s1323445"
    assert sample_model.file_name == "52614.1.394702.GCACTAAC-CCAAGACT.filtered-report.txt"
    assert sample_model.file_status == "RESTORED"
    assert sample_model.file_size == 3645
    assert sample_model.jdp_file_id == "6190d7d30de2fc3298da6f7a"
    assert sample_model.md5sum == "fcd87248b5922a8bd0d530bcb23bffae"
    assert sample_model.analysis_project_id == "p1323348"



def test_sample_records_to_sample_objects(test_db, grow_analysis_df):
    exp_sample_count = len(grow_analysis_df)

    sample_records = grow_analysis_df.to_dict("records")
    assert len(sample_records) == exp_sample_count

    sample_objects = sample_records_to_sample_objects(sample_records)
    assert len(sample_objects) == exp_sample_count

