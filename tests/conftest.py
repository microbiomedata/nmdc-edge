import os
from pymongo import MongoClient
from pathlib import Path
from pytest import fixture
from time import time

from nmdc_automation.config import Config


@fixture
def test_db():
    conn_str = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    return MongoClient(conn_str).test

@fixture(autouse=True)
def mock_api(monkeypatch, requests_mock):
    monkeypatch.setenv("NMDC_API_URL", "http://localhost")
    monkeypatch.setenv("NMDC_CLIENT_ID", "anid")
    monkeypatch.setenv("NMDC_CLIENT_SECRET", "asecret")
    resp = {"expires": {"minutes": time()+60},
            "access_token": "abcd"
            }
    requests_mock.post("http://localhost/token", json=resp)

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
def config_dir(base_test_dir):
    return base_test_dir.parent / "configs"

@fixture(scope="session")
def site_config(base_test_dir):
    return base_test_dir / "site_configuration_test.toml"

@fixture(scope="session")
def job_config(site_config):
    return Config(site_config)