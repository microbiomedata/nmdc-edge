from nmdc_automation.workflow_automation.wfutils import WorkflowJob
import json



def test_job(job_config, requests_mock, test_data_dir):
    requests_mock.real_http = True
    data = {"id": "123"}
    requests_mock.post("http://localhost:8088/api/workflows/v1", json=data)
    rqcf = test_data_dir / "rqc_response.json"
    rqc = json.load(open(rqcf))
    ajob = WorkflowJob(job_config, workflow_config=rqc['config'])
    ajob.debug = True
    ajob.dryrun = False
    assert ajob.get_state()
    ajob.cromwell_submit()
    last = requests_mock.request_history[-1]
    assert last.method == "POST"
    assert last.url == "http://localhost:8088/api/workflows/v1"


def test_log(job_config):
    ajob = WorkflowJob(job_config, workflow_config={})
    # ajob = job("example", "jobid", conf={})
    ajob.debug = True
    ajob.json_log({"a": "b"}, title="Test")


def test_check_meta(job_config, requests_mock):
    url = "http://localhost:8088/api/workflows/v1/1234/status"
    requests_mock.get(url, json={"status": "Submitted"})
    url = "http://localhost:8088/api/workflows/v1/1234/metadata"
    requests_mock.get(url, json={"status": "Submitted"})
    ajob = WorkflowJob(job_config, workflow_config={})
    ajob.jobid = "1234"
    resp = ajob.check_status()
    assert resp
    resp = ajob.get_metadata()
    assert resp


def test_set_state(job_config):
    ajob = WorkflowJob(job_config, workflow_config={})
    state = ajob.get_state()
    assert state
    bjob = WorkflowJob(job_config, state=state)
    assert bjob.activity_id == state['activity_id']


def test_workflow_job(job_config, mock_job_state, requests_mock):
    # Mock the Cromwell status request
    job_id = mock_job_state.get('cromwell_jobid', '34b41f4a-fe50-4c00-bb60-444104b4c024')
    mock_url = f"http://localhost:8088/api/workflows/v1/{job_id}/status"

    # Set the mocked response for the Cromwell status endpoint
    requests_mock.get(mock_url, json={"status": "Succeeded"})

    wf_job = WorkflowJob(job_config, state=mock_job_state)
    assert wf_job.activity_id == mock_job_state['activity_id']

    wfdict = wf_job.as_workflow_execution_dict()
    assert wfdict['id'] == mock_job_state['activity_id']

