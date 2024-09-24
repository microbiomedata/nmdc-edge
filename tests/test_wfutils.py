from nmdc_automation.workflow_automation.wfutils import WorkflowJob as job
import json



def test_job(job_config, requests_mock, test_data_dir):
    requests_mock.real_http = True
    data = {"id": "123"}
    requests_mock.post("http://localhost:8088/api/workflows/v1", json=data)
    rqcf = test_data_dir / "rqc_response.json"
    rqc = json.load(open(rqcf))
    ajob = job(job_config, workflow_config=rqc['config'])
    ajob.debug = True
    ajob.dryrun = False
    assert ajob.get_state()
    ajob.cromwell_submit()
    last = requests_mock.request_history[-1]
    assert last.method == "POST"
    assert last.url == "http://localhost:8088/api/workflows/v1"


def test_log(job_config):
    ajob = job(job_config, workflow_config={})
    # ajob = job("example", "jobid", conf={})
    ajob.debug = True
    ajob.json_log({"a": "b"}, title="Test")


def test_check_meta(job_config, requests_mock):
    url = "http://localhost:8088/api/workflows/v1/1234/status"
    requests_mock.get(url, json={"status": "Submitted"})
    url = "http://localhost:8088/api/workflows/v1/1234/metadata"
    requests_mock.get(url, json={"status": "Submitted"})
    ajob = job(job_config, workflow_config={})
    ajob.jobid = "1234"
    resp = ajob.check_status()
    assert resp
    resp = ajob.get_metadata()
    assert resp


def test_set_state(job_config):
    ajob = job(job_config, workflow_config={})
    state = ajob.get_state()
    assert state
    bjob = job(job_config, state=state)
    assert bjob.activity_id == state['activity_id']
