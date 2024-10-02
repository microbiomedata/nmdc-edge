from nmdc_automation.workflow_automation.watch_nmdc import Watcher
from nmdc_automation.workflow_automation.wfutils import WorkflowJob
from pytest import fixture
from unittest.mock import patch



@fixture(autouse=True)
def mock_cromwell(requests_mock, test_data_dir):
    requests_mock.real_http = True
    data = {"id": "1234"}
    cromwell_url = "http://localhost:8088/api/workflows/v1"
    requests_mock.post(cromwell_url, json=data)
    afile_path = test_data_dir / "afile"
    bfile_path = test_data_dir / "bfile"
    metadata = {'outputs': {
          "nmdc_rqcfilter.filtered_final": str(afile_path),
          "nmdc_rqcfilter.filtered_stats_final": str(bfile_path),
          "nmdc_rqcfilter.stats": {
            "input_read_count": 11431762,
            "input_read_bases": 1726196062,
            "output_read_bases": 1244017053,
            "output_read_count": 8312566
            },
        }}
    requests_mock.get(f"{cromwell_url}/1234/metadata", json=metadata)
    data = {"status": "Succeeded"}
    requests_mock.get(f"{cromwell_url}/1234/status", json=data)


def test_watcher(site_config_file):
    w = Watcher(site_config_file)
    w.restore_from_checkpoint()
    w.job_manager.job_checkpoint()
    w.restore_from_checkpoint()


def test_claim_jobs(requests_mock, site_config_file, mock_api):
    requests_mock.real_http = True
    w = Watcher(site_config_file)
    job_id = "nmdc:b7eb8cda-a6aa-11ed-b1cf-acde48001122"
    resp = {
            'id': 'nmdc:1234',
            'detail': {'id': 'nmdc:1234'}
            }
    requests_mock.post(f"http://localhost/jobs/{job_id}:claim", json=resp)
    w.claim_jobs()
    w.cycle()
    resp = w.job_manager.find_job_by_opid("nmdc:1234")
    assert resp


def test_reclaim_job(requests_mock, site_config_file, mock_api):
    requests_mock.real_http = True

    w = Watcher(site_config_file)
    job_id = "nmdc:b7eb8cda-a6aa-11ed-b1cf-acde48001122"
    resp = {
            'id': 'nmdc:1234',
            'detail': {'id': 'nmdc:1234'}
            }
    requests_mock.post(f"http://localhost/jobs/{job_id}:claim", json=resp,
                       status_code=409)
    w.claim_jobs()
    resp = w.job_manager.find_job_by_opid("nmdc:1234")
    assert resp



def test_watcher_restore_from_checkpoint(site_config_file, fixtures_dir):
    state_file = fixtures_dir / "job_state.json"


