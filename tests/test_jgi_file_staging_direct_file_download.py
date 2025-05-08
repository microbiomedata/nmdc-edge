import os
import sys
import pytest
import requests
import pandas as pd
from unittest import mock
from nmdc_automation.jgi_file_staging.direct_file_download import download_files, download_sample_file  # adjust import if needed

@pytest.fixture
def sample_csv(tmp_path):
    csv_file = tmp_path / "samples.csv"
    df = pd.DataFrame([
        {"apGoldId": "AP123", "file_name": "testfile.txt", "jdp_file_id": "file123"}
    ])
    df.to_csv(csv_file, index=False)
    return str(csv_file)


@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("JDP_TOKEN", "fake-token")

@pytest.fixture
def mock_requests_get():
    with mock.patch("requests.get") as mock_get:
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.iter_content.return_value = [b"data chunk"]
        mock_response.text = "OK"
        mock_get.return_value = mock_response
        yield mock_get

def test_download_sample_file_success(tmp_path, mock_requests_get):
    save_dir = tmp_path
    save_file = save_dir / "testfile.txt"
    files_dict = {"file_name": "testfile.txt", "jdp_file_id": "file123"}

    download_sample_file("fake-token", str(save_dir), files_dict)

    # Check the file was created
    assert save_file.exists()
    # Check the content
    assert save_file.read_bytes() == b"data chunk"
    # Check requests.get was called correctly
    mock_requests_get.assert_called_once()
    args, kwargs = mock_requests_get.call_args
    assert kwargs["headers"]["Authorization"] == "fake-token"

def test_download_files_creates_dir_and_calls_sample(tmp_path, sample_csv, jgi_staging_config, mock_env):
    with mock.patch("nmdc_automation.jgi_file_staging.direct_file_download.download_sample_file") as mock_download:
        project = "proj"
        download_files(project, jgi_staging_config, sample_csv)
        # Check directory was created
        config_dir = os.path.join(tmp_path, f"{project}_analysis_projects", "AP123")
        assert os.path.exists(config_dir)
        # Check download_sample_file was called
        mock_download.assert_called_once()

def test_download_sample_file_conflict_logs(tmp_path, monkeypatch):
    files_dict = {"file_name": "conflictfile.txt", "jdp_file_id": "file456"}
    save_dir = tmp_path
    save_file = save_dir / "conflictfile.txt"

    mock_response = mock.Mock()
    mock_response.status_code = 409
    mock_response.text = "Conflict"
    monkeypatch.setattr(requests, "get", mock.Mock(return_value=mock_response))

    # Should not raise or create file
    download_sample_file("fake-token", str(save_dir), files_dict)
    assert not save_file.exists()

def test_download_sample_file_error_exit(tmp_path, monkeypatch):
    files_dict = {"file_name": "errorfile.txt", "jdp_file_id": "file789"}
    save_dir = tmp_path

    mock_response = mock.Mock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    monkeypatch.setattr(requests, "get", mock.Mock(return_value=mock_response))

    with pytest.raises(SystemExit):
        download_sample_file("fake-token", str(save_dir), files_dict)
