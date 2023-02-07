from src.nmdcapi import nmdcapi, jprint
import requests
import pytest
import json
import os


class MockResponse:
    def __init__(self, resp, status_code=200):
        self.resp = resp
        self.status_code = status_code

    def json(self):
        return self.resp


@pytest.fixture
def token():
    resp = {
            'expires': {"minutes": 100},
            'access_token': 'bogus'
           }
    return resp


@pytest.fixture
def logged_in(monkeypatch):
    token = {
            'expires': {"minutes": 100},
            'access_token': 'bogus'
           }

    def mock_post(*args, **kwargs):
        return MockResponse(token)

    # apply the monkeypatch for requests.get to mock_get
    monkeypatch.setattr(requests, "post", mock_post)
    monkeypatch.setenv("HOME", "./test_data")
    return nmdcapi()


def test_missing_auth(token, monkeypatch):
    def mock_post(*args, **kwargs):
        return MockResponse({})

    # apply the monkeypatch for requests.get to mock_get
    monkeypatch.setattr(requests, "post", mock_post)
    monkeypatch.setenv("HOME", "/bogus")
    n = nmdcapi()
    assert n.token is None


def test_basics(logged_in, monkeypatch):
    n = logged_in

    assert n.token
    assert n.get_header()

    n.refresh_token()

    def mock_post(*args, **kwargs):
        return MockResponse({'blah': 1})

    monkeypatch.setattr(requests, "post", mock_post)
    resp = n.mint("nmdc", "mga0", 1)
    assert resp

    # Add decode description
    def mock_get(*args, **kwargs):
        return MockResponse({'description': '{"a": "b"}'})

    monkeypatch.setattr(requests, "get", mock_get)
    resp = n.get_object("xxx", decode=True)
    assert resp
    assert "metadata" in resp


def test_objects(logged_in, monkeypatch):
    n = logged_in
    assert n.token

    def mock_post(*args, **kwargs):
        data = json.loads(kwargs.get('data'))
        data["url"] = args[0]
        return MockResponse(data)

    monkeypatch.setattr(requests, "post", mock_post)
    fn = "./test_data/afile.sha256"
    if os.path.exists(fn):
        os.remove(fn)
    resp = n.create_object("./test_data/afile", "desc", "http://localhost/")
    assert "checksums" in resp

    resp = n.create_object("./test_data/afile", "desc", "http://localhost/")
    assert "checksums" in resp

    resp = n.post_objects({"a": "b"})
    assert "a" in resp

    def mock_put(*args, **kwargs):
        data = json.loads(kwargs.get('data'))
        return MockResponse(data)

    monkeypatch.setattr(requests, "put", mock_put)
    resp = n.set_type("abc", "metadatain")

    def mock_patch(*args, **kwargs):
        resp = json.loads(kwargs.get("data"))
        resp['url'] = args[0]
        return MockResponse(resp)
    monkeypatch.setattr(requests, "patch", mock_patch)
    resp = n.bump_time("abc")
    assert "created_time" in resp


def test_list_funcs(logged_in, monkeypatch):
    n = logged_in
    assert n.token
    mock_resp = json.load(open("./test_data/mock_jobs.json"))

    def mock_get(*args, **kwargs):
        assert "filter=" in args[0]
        assert "max_page_size=10" in args[0]
        return MockResponse(mock_resp)

    monkeypatch.setattr(requests, "get", mock_get)
    resp = n.list_jobs(filt="a=b", max=10)
    assert resp

    resp = n.list_ops(filt="a=b", max_page_size=10)
    assert resp

    resp = n.list_objs(filt="a=b", max_page_size=10)
    assert resp


def test_update_op(logged_in, monkeypatch):
    n = logged_in

    mock_resp = {'metadata': {"b": "c"}}

    def mock_get(*args, **kwargs):
        return MockResponse(mock_resp)

    monkeypatch.setattr(requests, "get", mock_get)

    def mock_patch(*args, **kwargs):
        resp = json.loads(kwargs.get("data"))
        resp['url'] = args[0]
        return MockResponse(resp)
    monkeypatch.setattr(requests, "get", mock_get)
    monkeypatch.setattr(requests, "patch", mock_patch)
    resp = n.update_op("abc", done=True, results={"a": "b"}, meta={"d": "e"})
    assert "b" in resp["metadata"]
    assert resp['url'] == 'https://api-dev.microbiomedata.org/operations/abc'


def test_jobs(logged_in, monkeypatch):
    n = logged_in

    def mock_get(*args, **kwargs):
        return MockResponse(args[0])

    monkeypatch.setattr(requests, "get", mock_get)
    resp = n.get_job("abc")
    assert "jobs/" in resp

    def mock_post(*args, **kwargs):
        data = {"url": args[0]}
        return MockResponse(data)

    monkeypatch.setattr(requests, "post", mock_post)
    resp = n.claim_job("abc")
    assert ":claim" in resp["url"]
    assert resp["claimed"] is False

    def mock_post(*args, **kwargs):
        data = {"url": args[0]}
        return MockResponse(data, status_code=409)

    monkeypatch.setattr(requests, "post", mock_post)
    resp = n.claim_job("abc")
    assert ":claim" in resp["url"]
    assert resp["claimed"] is True


def test_jprint():
    jprint({"a": "b"})
