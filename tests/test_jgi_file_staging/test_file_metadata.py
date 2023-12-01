import configparser
import pytest

from nmdc_automation.jgi_file_staging.jgi_file_metadata import (
    get_access_token,
    check_access_token,
)


def test_get_access_token(mocker):
    mock_get = mocker.patch(
        "nmdc_automation.jgi_file_staging.jgi_file_metadata.requests.get"
    )
    mock_get.return_value.status_code = 200
    mock_get.return_value.text = "ed42ef1556708305eaf8"
    ACCESS_TOKEN = get_access_token()
    assert ACCESS_TOKEN == "ed42ef1556708305eaf8"


def test_check_access_token(mocker, config):
    mock_get = mocker.patch(
        "nmdc_automation.jgi_file_staging.jgi_file_metadata.requests.get"
    )
    mock_get.return_value.status_code = 200
    ACCESS_TOKEN = "ed42ef1556708305eaf8"
    ACCESS_TOKEN = check_access_token(ACCESS_TOKEN, eval(config["JDP"]["delay"]))
    assert ACCESS_TOKEN == "ed42ef1556708305eaf8"


def test_check_access_token_invalid(mocker, config):
    mock_get = mocker.patch(
        "nmdc_automation.jgi_file_staging.jgi_file_metadata.requests.get"
    )
    response_mock1 = mocker.Mock()
    response_mock1.status_code = 400
    response_mock1.text = "ed42ef1556"
    response_mock2 = mocker.Mock()
    response_mock2.status_code = 200
    response_mock2.text = "ed42ef155670"
    mock_get.side_effect = [response_mock1, response_mock2]

    ACCESS_TOKEN = "ed42ef1556708305eaf8"
    ACCESS_TOKEN = check_access_token(ACCESS_TOKEN, eval(config["JDP"]["delay"]))
    assert ACCESS_TOKEN == "ed42ef155670"
