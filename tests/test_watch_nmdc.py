import copy
import json
from pathlib import Path, PosixPath
from pytest import fixture

from nmdc_automation.workflow_automation.watch_nmdc import (
    Watcher,
    JobManager,
    FileHandler,
    RuntimeApiHandler,
)
from nmdc_automation.workflow_automation.wfutils import WorkflowJob
from tests.fixtures import db_utils



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


def test_watcher_file_handler(site_config_file, site_config, fixtures_dir, tmp_path):
    w = Watcher(site_config_file)
    assert w

    # Test FileHandler
    assert w.file_handler
    assert w.file_handler.state_file
    assert w.file_handler.state_file.exists()
    assert w.file_handler.state_file.is_file()
    assert isinstance(w.file_handler.state_file, PosixPath)
    # read state
    start_state = w.file_handler.read_state()
    assert start_state
    assert isinstance(start_state, dict)
    exp_num_jobs = 1
    assert len(start_state.get("jobs")) == exp_num_jobs
    # write state
    new_job = db_utils.read_json("new_state_job.json")
    assert new_job
    new_state = copy.deepcopy(start_state)
    new_state["jobs"].append(new_job)
    w.file_handler.write_state(new_state)
    state = w.file_handler.read_state()
    assert len(state.get("jobs")) == exp_num_jobs + 1
    # reset state
    w.file_handler.write_state(start_state)
    # check reset
    state = w.file_handler.read_state()
    assert len(state.get("jobs")) == exp_num_jobs

    # test FileHandler methods that take a WorkflowJob object
    # get output path
    job_state = db_utils.read_json("mags_job_state.json")
    job = WorkflowJob(site_config, job_state)
    assert job
    output_dir = w.file_handler.get_output_path(job)
    assert output_dir
    assert isinstance(output_dir, PosixPath)
    # write metadata
    w.file_handler.write_metadata_if_not_exists(job, tmp_path)
    # look for metadata file
    assert tmp_path / "metadata.json"







    assert w.job_manager

    assert w.runtime_api_handler

    w.restore_from_checkpoint()
    w.job_manager.job_checkpoint()
    w.restore_from_checkpoint()


@fixture
def mock_runtime_api_handler(site_config, mock_api):
    pass


def test_claim_jobs(requests_mock, site_config_file, mock_api):
    requests_mock.real_http = True
    w = Watcher(site_config_file)
    job_id = "nmdc:b7eb8cda-a6aa-11ed-b1cf-acde48001122"
    resp = {
            'id': 'nmdc:1234',
            'detail': {'id': 'nmdc:1234'}
            }
    requests_mock.post(f"http://localhost/jobs/{job_id}:claim", json=resp)
    # w.claim_jobs()
    # w.cycle()
    # resp = w.job_manager.find_job_by_opid("nmdc:1234")
    # assert resp


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
    state_file = fixtures_dir / "mags_job_state.json"


