from src.wfutils import job
import os
import json
import requests


class MockResponse:
    def __init__(self, resp, status_code=200):
        self.resp = resp
        self.status_code = status_code

    def json(self):
        return self.resp


def test_job():
    tdir = os.path.dirname(__file__)
    tdata = os.path.join(tdir, "..", "test_data")
    rqcf = os.path.join(tdata, "rqc_response.json")
    rqc = json.load(open(rqcf))
    ajob = job("example", "jobid", conf=rqc['config'])
    ajob.debug = True
    ajob.dryrun = True
    assert ajob.get_state()
    status = ajob.cromwell_submit()
    print(status)


def test_log():
    ajob = job("example", "jobid", conf={})
    ajob.debug = True
    ajob.json_log({"a": "b"}, title="Test")


def test_check_meta(monkeypatch):
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


def test_set_state():
    ajob = job("example", "jobid", conf={})
    state = ajob.get_state()
    assert state
    bjob = job(state=state)
    assert bjob.activity_id == state['activity_id']
