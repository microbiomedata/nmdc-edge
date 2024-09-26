import json
import os
from pymongo import MongoClient
from pathlib import Path
from pytest import fixture
from time import time
from yaml import load

from nmdc_automation.config import Config
from nmdc_automation.workflow_automation.workflows import Workflow



@fixture
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
    return base_test_dir / "fixtures"

@fixture(scope="session")
def test_data_dir(base_test_dir):
    return base_test_dir / "test_data"

@fixture(scope="session")
def workflows_config_dir(base_test_dir):
    return base_test_dir.parent / "nmdc_automation/config/workflows"

@fixture(scope="session")
def site_config(base_test_dir):
    return base_test_dir / "site_configuration_test.toml"

@fixture(scope="session")
def job_config(site_config):
    return Config(site_config)
