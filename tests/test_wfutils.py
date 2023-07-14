from nmdc_automation.workflow_automation.wfutils import WorkflowJob as job
import os
import json
from pytest import fixture
from nmdc_automation.workflow_automation.config import config


@fixture
def site_conf():
    return config("./configs/site_configuration.toml")


def test_job(site_conf, requests_mock):
    requests_mock.real_http = True
    data = {"id": "123"}
    requests_mock.post("http://localhost:8088/api/workflows/v1", json=data)
    tdir = os.path.dirname(__file__)
    tdata = os.path.join(tdir, "..", "test_data")
    rqcf = os.path.join(tdata, "rqc_response.json")
    rqc = json.load(open(rqcf))
    ajob = job(site_conf.conf, workflow_config=rqc['config'])
    ajob.debug = True
    ajob.dryrun = False
    assert ajob.get_state()
    ajob.cromwell_submit()
    last = requests_mock.request_history[-1]
    assert last.method == "POST"
    assert last.url == "http://localhost:8088/api/workflows/v1"


def test_log(site_conf):
    ajob = job(site_conf.conf, workflow_config={})
    # ajob = job("example", "jobid", conf={})
    ajob.debug = True
    ajob.json_log({"a": "b"}, title="Test")


def test_check_meta(site_conf, requests_mock):
    url = "http://localhost:8088/api/workflows/v1/1234/status"
    requests_mock.get(url, json={"status": "Submitted"})
    url = "http://localhost:8088/api/workflows/v1/1234/metadata"
    requests_mock.get(url, json={"status": "Submitted"})
    ajob = job(site_conf.conf, workflow_config={})
    ajob.jobid = "1234"
    resp = ajob.check_status()
    assert resp
    resp = ajob.get_metadata()
    assert resp


def test_set_state(site_conf):
    ajob = job(site_conf.conf, workflow_config={})
    state = ajob.get_state()
    assert state
    bjob = job(site_conf.conf, state=state)
    assert bjob.activity_id == state['activity_id']
