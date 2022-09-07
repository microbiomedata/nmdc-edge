import json
import os
from src.submitter import staging, submit
import requests
from pytest import fixture


test_dir = os.path.dirname(__file__)
test_data = os.path.join(test_dir, "..", "test_data")


# custom class to be the mock return value of requests.get()
class MockResponse:
    status_code = 200

    @staticmethod
    def json():
        return {"id": "mock_id_response"}

    @staticmethod
    def iter_content(chunk_size=0):
        return ""


@fixture
def mock_response(monkeypatch):
    """Requests.get() mocked to return {'mock_key':'mock_response'}."""

    def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get)

    def mock_post(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(requests, "post", mock_post)


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


def test_submit(mock_response):
    """
    Test basic job creation
    """
    fn = "rqc_response.json"
    job = read_json(fn)
    resp = submit(job)