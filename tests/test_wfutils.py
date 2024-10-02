from nmdc_automation.workflow_automation.wfutils import (
    WorkflowJobDeprecated,
    get_workflow_execution_record_for_job,
    CromwellJobRunner,
    WorkflowJob
)
from nmdc_automation.workflow_automation.models import get_base_workflow_execution_keys
import json



def test_job(site_config, requests_mock, test_data_dir):
    requests_mock.real_http = True
    data = {"id": "123"}
    requests_mock.post("http://localhost:8088/api/workflows/v1", json=data)
    rqcf = test_data_dir / "rqc_response.json"
    rqc = json.load(open(rqcf))
    ajob = WorkflowJobDeprecated(site_config, workflow_config=rqc['config'])
    ajob.debug = True
    ajob.dryrun = False
    assert ajob.get_state()
    ajob.cromwell_submit()
    last = requests_mock.request_history[-1]
    assert last.method == "POST"
    assert last.url == "http://localhost:8088/api/workflows/v1"


def test_log(site_config):
    ajob = WorkflowJobDeprecated(site_config, workflow_config={})
    # ajob = job("example", "jobid", conf={})
    ajob.debug = True
    ajob.json_log({"a": "b"}, title="Test")


def test_check_meta(site_config, requests_mock):
    url = "http://localhost:8088/api/workflows/v1/1234/status"
    requests_mock.get(url, json={"status": "Submitted"})
    url = "http://localhost:8088/api/workflows/v1/1234/metadata"
    requests_mock.get(url, json={"status": "Submitted"})
    ajob = WorkflowJobDeprecated(site_config, workflow_config={})
    ajob.jobid = "1234"
    resp = ajob.check_status()
    assert resp
    resp = ajob.get_cromwell_metadata()
    assert resp


def test_set_state(site_config):
    ajob = WorkflowJobDeprecated(site_config, workflow_config={})
    state = ajob.get_state()
    assert state
    bjob = WorkflowJobDeprecated(site_config, state=state)
    assert bjob.activity_id == state['activity_id']


def test_workflow_job(site_config, mock_job_state, requests_mock):
    # Mock the Cromwell status request
    job_id = mock_job_state.get('cromwell_jobid', '34b41f4a-fe50-4c00-bb60-444104b4c024')
    mock_url = f"http://localhost:8088/api/workflows/v1/{job_id}/status"

    # Set the mocked response for the Cromwell status endpoint
    requests_mock.get(mock_url, json={"status": "Succeeded"})

    wf_job = WorkflowJobDeprecated(site_config, state=mock_job_state)
    assert wf_job.activity_id == mock_job_state['activity_id']

    wfdict = wf_job.as_workflow_execution_dict()
    assert wfdict['id'] == mock_job_state['activity_id']


def test_cromwell_job_runner(site_config, fixtures_dir):
    # load cromwell metadata
    cromwell_metadata = json.load(open(fixtures_dir / "cromwell_metadata.json"))
    job_runner = CromwellJobRunner("http://fake.url.org", cromwell_metadata)

    job_metadata = job_runner.job_metadata
    assert job_metadata['status'] == "Succeeded"

def test_workflow_job_as_workflow_execution_dict(site_config, fixtures_dir):
    # load cromwell metadata
    cromwell_metadata = json.load(open(fixtures_dir / "cromwell_metadata.json"))
    job_runner = CromwellJobRunner("http://fake.url.org", cromwell_metadata)

    # load job state
    job_state = json.load(open(fixtures_dir / "mags_job_state.json"))

    # create a WorkflowJob object
    wf_job = WorkflowJob(site_config, job_state, job_runner)
    assert wf_job.workflow_execution_id == job_state['activity_id']

    job_meta = wf_job.job_runner.job_metadata
    assert job_meta['status'] == "Succeeded"

    wfe_dict = wf_job.as_workflow_execution_dict
    assert wfe_dict['id'] == job_state['activity_id']

    for key in get_base_workflow_execution_keys():
        # doesn't have has_output yet
        if key == "has_output":
            continue
        assert key in wfe_dict
















