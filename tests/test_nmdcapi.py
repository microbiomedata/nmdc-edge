from nmdc_automation.api.nmdcapi import NmdcRuntimeApi as nmdcapi
import json
import os


def test_basics(requests_mock, site_config_file, mock_api):
    n = nmdcapi(site_config_file)

    # Add decode description
    resp = {'description': '{"a": "b"}'}
    requests_mock.get("http://localhost:8000/objects/xxx", json=resp)
    resp = n.get_object("xxx", decode=True)
    assert resp is not None
    assert "metadata" in resp


def test_objects(requests_mock, site_config_file, test_data_dir, mock_api):
    n = nmdcapi(site_config_file)

    requests_mock.post("http://localhost:8000/objects", json={})
    fn = test_data_dir / "afile.sha256"
    if os.path.exists(fn):
        os.remove(fn)
    afile = test_data_dir / "afile"
    resp = n.create_object(str(afile), "desc", "http://localhost:8000/")
    resp = n.create_object(test_data_dir / "afile", "desc", "http://localhost:8000/")
    url = "http://localhost:8000/workflows/workflow_executions"
    requests_mock.post(url, json={"a": "b"})
    resp = n.post_workflow_executions({"a": "b"})
    assert "a" in resp

    requests_mock.put("http://localhost:8000/objects/abc/types", json={})
    resp = n.set_type("abc", "metadatain")

    requests_mock.patch("http://localhost:8000/objects/abc", json={"a": "b"})
    resp = n.bump_time("abc")
    assert "a" in resp


def test_list_funcs(requests_mock, site_config_file, test_data_dir, mock_api):
    n = nmdcapi(site_config_file)
    mock_resp = json.load(open(test_data_dir / "mock_jobs.json"))

    # TODO: ccheck the full url
    requests_mock.get("http://localhost:8000/jobs", json=mock_resp)
    resp = n.list_jobs(filt="a=b")
    assert resp is not None

    requests_mock.get("http://localhost:8000/operations", json=[])
    resp = n.list_ops(filt="a=b")
    assert resp is not None

    requests_mock.get("http://localhost:8000/objects", json=[])
    resp = n.list_objs(filt="a=b")
    assert resp is not None


def test_update_op(requests_mock, site_config_file, mock_api):
    n = nmdcapi(site_config_file)

    mock_resp = {'metadata': {"b": "c"}}

    # monkeypatch.setattr(requests, "get", mock_get)
    requests_mock.get("http://localhost:8000/operations/abc", json=mock_resp)
    requests_mock.patch("http://localhost:8000/operations/abc", json=mock_resp)
    # monkeypatch.setattr(requests, "get", mock_get)
    # monkeypatch.setattr(requests, "patch", mock_patch)
    resp = n.update_op("abc", done=True, results={"a": "b"}, meta={"d": "e"})
    assert "b" in resp["metadata"]


def test_jobs(requests_mock, site_config_file, mock_api):
    n = nmdcapi(site_config_file)

    requests_mock.get("http://localhost:8000/jobs/abc", json="jobs/")
    resp = n.get_job("abc")
    assert "jobs/" in resp

    resp = {"url": "jobs:claim"}
    url = "http://localhost:8000/jobs/abc:claim"
    requests_mock.post(url, json=resp, status_code=200)
    resp = n.claim_job("abc")
    assert ":claim" in resp["url"]
    assert resp["claimed"] is False

    requests_mock.post(url, json={}, status_code=409)
    resp = n.claim_job("abc")
    assert resp["claimed"] is True


def test_nmdcapi_get_token_with_retry(requests_mock, site_config_file):
    n = nmdcapi(site_config_file)
    token_url = "http://localhost:8000/token"

    requests_mock.post(
        token_url, [{"status_code": 401, "json": {"error": "Unauthorized"}},
                    {"status_code": 200, "json": {
                        "access_token": "mocked_access_token",
                        "expires": {"days": 1},
                    }}]
    )
    # sanity check
    assert n.token is None
    assert n.expires_at == 0

    # Call method under test - should retry and succeed
    n.get_token()

    # Check that the token was set
    assert n.token == "mocked_access_token"
    assert n.expires_at > 0

