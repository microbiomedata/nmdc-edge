import json
import os
from pymongo import MongoClient
from pathlib import Path
from pytest import fixture
import requests_mock
import shutil
from time import time
from unittest.mock import Mock
from yaml import load, Loader


from nmdc_automation.config import SiteConfig
from nmdc_automation.workflow_automation.models import WorkflowConfig
from tests.fixtures import db_utils
from nmdc_automation.workflow_automation.wfutils import WorkflowJob

@fixture(scope="session")
def mock_job_state():
    state = db_utils.read_json(
        "mags_workflow_state.json"
    )
    return state


@fixture(scope="session")
def mags_config(fixtures_dir)->WorkflowConfig:
    yaml_file = fixtures_dir / "mags_config.yaml"
    wf = load(open(yaml_file), Loader)
    # normalize the keys from Key Name to key_name
    wf = {k.replace(" ", "_").lower(): v for k, v in wf.items()}
    return WorkflowConfig(**wf)


@fixture(scope="session")
def test_db():
    conn_str = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    return MongoClient(conn_str).test

@fixture(autouse=True)
def mock_api(monkeypatch, requests_mock, test_data_dir):
    monkeypatch.setenv("NMDC_API_URL", "http://localhost")
    monkeypatch.setenv("NMDC_CLIENT_ID", "anid")
    monkeypatch.setenv("NMDC_CLIENT_SECRET", "asecret")
    token_resp = {"expires": {"minutes": time()+60},
            "access_token": "abcd"
            }
    requests_mock.post("http://localhost/token", json=token_resp)
    resp = ["nmdc:abcd"]
    requests_mock.post("http://localhost/pids/mint", json=resp)
    requests_mock.post(
        "http://localhost/workflows/workflow_executions",
        json=resp
        )
    requests_mock.post("http://localhost/pids/bind", json=resp)

    rqcf = test_data_dir / "rqc_response2.json"
    rqc = json.load(open(rqcf))
    rqc_resp = {"resources": [rqc]}
    requests_mock.get("http://localhost/jobs", json=rqc_resp)

    requests_mock.patch("http://localhost/operations/nmdc:1234", json={})
    requests_mock.get("http://localhost/operations/nmdc:1234", json={'metadata': {}})


@fixture(scope="session")
def base_test_dir():
    return Path(__file__).parent

@fixture(scope="session")
def fixtures_dir(base_test_dir):
    path = base_test_dir / "fixtures"
    # get the absolute path
    return path.resolve()

@fixture(scope="session")
def test_data_dir(base_test_dir):
    return base_test_dir / "test_data"

@fixture(scope="session")
def workflows_config_dir(base_test_dir):
    return base_test_dir.parent / "nmdc_automation/config/workflows"


@fixture(scope="session")
def site_config_file(base_test_dir):
    return base_test_dir / "site_configuration_test.toml"

@fixture(scope="session")
def site_config(site_config_file):
    return SiteConfig(site_config_file)

@fixture
def initial_state_file(fixtures_dir, tmp_path):
    state_file = fixtures_dir / "initial_state.json"
    # make a working copy in tmp_path
    copied_state_file = tmp_path / "initial_state.json"
    shutil.copy(state_file, copied_state_file)
    return copied_state_file


# Sample Cromwell API responses
CROMWELL_SUCCESS_RESPONSE = {
    "id": "cromwell-job-id-12345",
    "status": "Succeeded",
    "outputs": {
        "output_file": "/path/to/output.txt"
    }
}

CROMWELL_FAIL_RESPONSE = {
    "id": "cromwell-job-id-54321",
    "status": "Failed",
    "failures": [
        {"message": "Error processing job"}
    ]
}

JOB_SUBMIT_RESPONSE = {
    "id": "cromwell-workflow-id",
  "status": "Submitted",
  "submission": "2024-10-13T12:34:56.789Z",
  "workflowName": "workflow_name",
  "workflowRoot": "gs://path/to/workflow/root",
  "metadataSource": "Unarchived",
  "outputs": {},
  "labels": {
    "label1": "value1",
    "label2": "value2"
  },
  "parentWorkflowId": None,
  "rootWorkflowId": "cromwell-root-id"
}

@fixture
def mock_cromwell_api(fixtures_dir):
    successful_job_metadata = json.load(open(fixtures_dir / 'cromwell/succeeded_metadata.json'))
    with requests_mock.Mocker() as m:
        # Mock the Cromwell submit job endpoint
        m.post('http://localhost:8088/api/workflows/v1', json=JOB_SUBMIT_RESPONSE, status_code=201)

        # Mock Cromwell status check endpoint
        m.get(
            'http://localhost:8088/api/workflows/v1/cromwell-job-id-12345/status', json={
                "id": "cromwell-job-id-12345",
                "status": "Succeeded"
            }
            )

        # Mock Cromwell failure scenario
        m.get('http://localhost:8088/api/workflows/v1/cromwell-job-id-54321/status', json=CROMWELL_FAIL_RESPONSE)

        # Mock Cromwell metadata endpoint
        m.get(
            'http://localhost:8088/api/workflows/v1/cromwell-job-id-12345/metadata',
            json=successful_job_metadata
            )

        yield m