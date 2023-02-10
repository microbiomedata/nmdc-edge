from src.wfutils import job
import os
import json
import requests
from pytest import fixture


@fixture
def wfconf(monkeypatch):
    tdir = os.path.dirname(__file__)
    wfc = os.path.join(tdir, "..", "test_data", "wf_config")
    monkeypatch.setenv("WF_CONFIG_FILE", wfc)


class MockResponse:
    def __init__(self, resp, status_code=200):
        self.resp = resp
        self.status_code = status_code

    def json(self):
        return self.resp


def test_job(wfconf, requests_mock):
    requests_mock.real_http = True
    data = {"id": "123"}
    requests_mock.post("http://localhost:8088/api/workflows/v1", json=data)
    tdir = os.path.dirname(__file__)
    tdata = os.path.join(tdir, "..", "test_data")
    rqcf = os.path.join(tdata, "rqc_response.json")
    rqc = json.load(open(rqcf))
    ajob = job("example", "jobid", conf=rqc['config'])
    ajob.debug = True
    ajob.dryrun = False
    assert ajob.get_state()
    ajob.cromwell_submit()
    last = requests_mock.request_history[-1]
    assert last.method == "POST"
    assert last.url == "http://localhost:8088/api/workflows/v1"


def test_log(wfconf):
    ajob = job("example", "jobid", conf={})
    ajob.debug = True
    ajob.json_log({"a": "b"}, title="Test")


def test_check_meta(monkeypatch, wfconf):
    def mock_get(*args, **kwargs):
        return MockResponse({"status": "Submitted"})

    # apply the monkeypatch for requests.get to mock_get
    monkeypatch.setattr(requests, "get", mock_get)
    ajob = job("example", "jobid", conf={})
    ajob.jobid = "1234"
    resp = ajob.check_status()
    assert resp
    resp = ajob.get_metadata()
    assert resp


def test_set_state(wfconf):
    ajob = job("example", "jobid", conf={})
    state = ajob.get_state()
    assert state
    bjob = job(state=state)
    assert bjob.activity_id == state['activity_id']
