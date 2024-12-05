import mongomock
import pandas as pd
from pathlib import Path
import pytest


from nmdc_automation.jgi_file_staging.jgi_file_metadata import (
    get_access_token,
    get_mongo_db,
    check_access_token,
    get_sequence_id,
    get_analysis_projects_from_proposal_id,
    insert_samples_into_mongodb,
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
    access_token = check_access_token(access_token, eval(config["JDP"]["delay"]))
    assert access_token == "ed42ef1556708305eaf8"


def test_check_access_token_invalid(mocker, mock_get, config):
    response_mock1 = mocker.Mock()
    response_mock1.status_code = 400
    response_mock1.text = "ed42ef1556"
    response_mock2 = mocker.Mock()
    response_mock2.status_code = 200
    response_mock2.text = "ed42ef155670"
    mock_get.side_effect = [response_mock1, response_mock2]

    access_token = "ed42ef1556708305eaf8"
    access_token = check_access_token(access_token, eval(config["JDP"]["delay"]))
    assert access_token == "ed42ef155670"


def test_get_sequence_id(mock_get, config):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = [{"itsSpid": 1323348}]
    sequence_id = get_sequence_id(
        "Ga0499978", "ed42ef155670", eval(config["JDP"]["delay"])
    )
    assert sequence_id == 1323348

    mock_get.return_value.status_code = 403
    sequence_id = get_sequence_id(
        "Ga0499978", "ed42ef155670", eval(config["JDP"]["delay"])
    )
    assert sequence_id == None


def test_get_analysis_projects_from_proposal_id(mock_get):
    mock_get.return_value.json.return_value = pd.read_csv(
        Path.joinpath(FIXTURE_DIR, "grow_gold_analysis_projects.csv")
    ).to_dict("records")
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
    assert sample_model.itsApId == "a1323348"
    assert sample_model.projects == "['Gp0587070']"
    assert sample_model.biosample_id == "Gb0305643"
    assert sample_model.seq_id == "s1323445"
    assert sample_model.file_name == "52614.1.394702.GCACTAAC-CCAAGACT.filtered-report.txt"
    assert sample_model.file_status == "RESTORED"
    assert sample_model.file_size == 3645
    assert sample_model.jdp_file_id == "6190d7d30de2fc3298da6f7a"
    assert sample_model.md5sum == "fcd87248b5922a8bd0d530bcb23bffae"
    assert sample_model.analysis_project_id == "p1323348"



# TODO: fix this test.  Data fixtures are raising ValidationError from
# the pydantic Sample model
@mongomock.patch(servers=(("localhost", 27017),), on_new="create")
def test_insert_samples_into_mongodb(monkeypatch, grow_analysis_df):
    monkeypatch.setenv("MONGO_DBNAME", "test_db")
    client = get_mongo_db()
    mdb = client["test_db"]

    insert_samples_into_mongodb(grow_analysis_df.to_dict("records"))
    mdb = get_mongo_db()
    sample = mdb.samples.find_one({"apGoldId": "Ga0499978"})
    assert sample["studyId"] == "Gs0149396"
