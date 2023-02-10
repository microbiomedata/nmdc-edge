from src.nmdcapi import nmdcapi, jprint
import pytest
import json
import os
from time import time


@pytest.fixture
def mock_api(monkeypatch, requests_mock):
    monkeypatch.setenv("NMDC_API_URL", "http://localhost")
    monkeypatch.setenv("NMDC_CLIENT_ID", "anid")
    monkeypatch.setenv("NMDC_CLIENT_SECRET", "asecret")
    resp = {"expires": {"minutes": time()+60},
            "access_token": "abcd"
            }
    requests_mock.post("http://localhost/token", json=resp)


def test_basics(mock_api, requests_mock):
    n = nmdcapi()

    requests_mock.post("http://localhost/ids/mint", json={})
    resp = n.mint("nmdc", "mga0", 1)
    assert resp is not None

    # Add decode description
    resp = {'description': '{"a": "b"}'}
    requests_mock.get("http://localhost/objects/xxx", json=resp)
    resp = n.get_object("xxx", decode=True)
    assert resp is not None
    assert "metadata" in resp


def test_objects(mock_api, requests_mock):
    n = nmdcapi()

    requests_mock.post("http://localhost/objects", json={})
    fn = "./test_data/afile.sha256"
    if os.path.exists(fn):
        os.remove(fn)
    resp = n.create_object("./test_data/afile", "desc", "http://localhost/")
    # assert "checksums" in resp

    resp = n.create_object("./test_data/afile", "desc", "http://localhost/")
    # assert "checksums" in resp
    url = "http://localhost/v1/workflows/activities"
    requests_mock.post(url, json={"a": "b"})
    resp = n.post_objects({"a": "b"})
    assert "a" in resp

    requests_mock.put("http://localhost/objects/abc/types", json={})
    resp = n.set_type("abc", "metadatain")

    requests_mock.patch("http://localhost/objects/abc", json={"a": "b"})
    resp = n.bump_time("abc")
    assert "a" in resp


def test_list_funcs(mock_api, requests_mock):
    n = nmdcapi()
    mock_resp = json.load(open("./test_data/mock_jobs.json"))

    # TODO: ccheck the full url
    requests_mock.get("http://localhost/jobs", json=mock_resp)
    resp = n.list_jobs(filt="a=b", max=10)
    assert resp is not None

    requests_mock.get("http://localhost/operations", json=[])
    resp = n.list_ops(filt="a=b", max_page_size=10)
    assert resp is not None

    requests_mock.get("http://localhost/objects", json=[])
    resp = n.list_objs(filt="a=b", max_page_size=10)
    assert resp is not None


def test_update_op(mock_api, requests_mock):
    n = nmdcapi()

    mock_resp = {'metadata': {"b": "c"}}

    # monkeypatch.setattr(requests, "get", mock_get)
    requests_mock.get("http://localhost/operations/abc", json=mock_resp)
    requests_mock.patch("http://localhost/operations/abc", json=mock_resp)
    # monkeypatch.setattr(requests, "get", mock_get)
    # monkeypatch.setattr(requests, "patch", mock_patch)
    resp = n.update_op("abc", done=True, results={"a": "b"}, meta={"d": "e"})
    assert "b" in resp["metadata"]


def test_jobs(mock_api, requests_mock):
    n = nmdcapi()

    requests_mock.get("http://localhost/jobs/abc", json="jobs/")
    resp = n.get_job("abc")
    assert "jobs/" in resp

    resp = {"url": "jobs:claim"}
    url = "http://localhost/jobs/abc:claim"
    requests_mock.post(url, json=resp, status_code=200)
    resp = n.claim_job("abc")
    assert ":claim" in resp["url"]
    assert resp["claimed"] is False

    requests_mock.post(url, json={}, status_code=409)
    resp = n.claim_job("abc")
    assert resp["claimed"] is True


def test_jprint():
    jprint({"a": "b"})
