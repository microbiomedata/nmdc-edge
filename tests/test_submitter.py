import json
import os
from src.submitter import staging
import requests
from pytest import fixture


test_dir = os.path.dirname(__file__)
test_data = os.path.join(test_dir, "..", "test_data")


# custom class to be the mock return value of requests.get()
class MockResponse:
    @staticmethod
    def json():
        return {"mock_key": "mock_response"}

    @staticmethod
    def iter_content(chunk_size=0):
        return ""


@fixture
def mock_response(monkeypatch):
    """Requests.get() mocked to return {'mock_key':'mock_response'}."""

    def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get)


def read_json(fn):
    fp = os.path.join(test_data, fn)
    data = json.load(open(fp))
    return data


def test_staging(mock_response):
    """
    Test basic job creation
    """
    fn = "rqc_response.json"
    job = read_json(fn)
    resp = staging(job['config']['inputs'])
    print(resp)
