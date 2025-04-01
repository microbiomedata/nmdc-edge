import copy
import json
from pathlib import PosixPath, Path

import pytest
from pytest import fixture
from unittest import mock
import requests_mock
import shutil
from unittest.mock import patch, PropertyMock, Mock

from nmdc_schema.nmdc import Database
from nmdc_automation.workflow_automation.watch_nmdc import (
    Watcher,
    FileHandler,
    JobManager,
    RuntimeApiHandler,
)
from nmdc_automation.workflow_automation.wfutils import WorkflowJob
from tests.fixtures import db_utils


# FileHandler init tests
def test_file_handler_init_from_state_file(site_config, initial_state_file_1_failure, tmp_path):
    copy_state_file = tmp_path / "copy_state.json"
    shutil.copy(initial_state_file_1_failure, copy_state_file)
    fh = FileHandler(site_config, initial_state_file_1_failure)
    assert fh
    assert fh.state_file
    assert isinstance(fh.state_file, PosixPath)
    assert fh.state_file.exists()
    assert fh.state_file.is_file()
    # delete state file
    fh.state_file = None
    assert not fh.state_file

    # test setter
    fh.state_file = initial_state_file_1_failure
    assert fh.state_file
    assert fh.state_file.exists()
    assert fh.state_file.is_file()

    # unlink state file
    fh.state_file.unlink()
    assert not fh.state_file.exists()
    fh.state_file = copy_state_file
    assert fh.state_file.exists()
    assert fh.state_file.is_file()


def test_file_handler_init_from_config_agent_state(site_config, initial_state_file_1_failure, tmp_path):
    with patch("nmdc_automation.config.siteconfig.SiteConfig.agent_state", new_callable=PropertyMock) as mock_agent_state:
        mock_agent_state.return_value = initial_state_file_1_failure
        fh = FileHandler(site_config)
        assert fh
        assert fh.state_file
        assert fh.state_file.exists()


def test_file_handler_init_default_state(site_config):
    # sanity check
    assert site_config.agent_state is None
    fh = FileHandler(site_config)
    assert fh
    assert fh.state_file
    assert fh.state_file.exists()
    # delete everything in the state file leaving an empty file
    with open(fh.state_file, "w") as f:
        f.write("")
    assert fh.state_file.stat().st_size == 0

    # create new FileHandler - should create new state file
    fh2 = FileHandler(site_config)
    assert fh2
    assert fh2.state_file
    assert fh2.state_file.exists()


def test_file_handler_read_state(site_config, initial_state_file_1_failure):
    fh = FileHandler(site_config, initial_state_file_1_failure)
    state = fh.read_state()
    assert state
    assert isinstance(state, dict)
    assert state.get("jobs")
    assert isinstance(state.get("jobs"), list)
    assert len(state.get("jobs")) == 1


def test_file_handler_write_state(site_config, initial_state_file_1_failure, fixtures_dir):
    fh = FileHandler(site_config, initial_state_file_1_failure)
    state = fh.read_state()
    assert state
    # add new job
    new_job = json.load(open(fixtures_dir / "new_state_job.json"))
    assert new_job
    state["jobs"].append(new_job)
    fh.write_state(state)
    # read state
    new_state = fh.read_state()
    assert new_state
    assert isinstance(new_state, dict)
    assert new_state.get("jobs")
    assert isinstance(new_state.get("jobs"), list)
    assert len(new_state.get("jobs")) == 2
    # reset state
    fh.write_state(state)


def test_file_handler_get_output_path(site_config, initial_state_file_1_failure, fixtures_dir):
    # Arrange
    was_informed_by = "nmdc:1234"
    workflow_execution_id = "nmdc:56789"
    mock_job = Mock()
    mock_job.was_informed_by = was_informed_by
    mock_job.workflow_execution_id = workflow_execution_id

    expected_output_path = site_config.data_dir / Path(was_informed_by) / Path(workflow_execution_id)

    fh = FileHandler(site_config, initial_state_file_1_failure)

    # Act
    output_path = fh.get_output_path(mock_job)

    # Assert
    assert output_path
    assert isinstance(output_path, PosixPath)
    assert output_path == expected_output_path


def test_file_handler_write_metadata_if_not_exists(site_config, initial_state_file_1_failure, fixtures_dir, tmp_path):
    # Arrange
    was_informed_by = "nmdc:1234"
    workflow_execution_id = "nmdc:56789"
    job_metadata = {"id": "xyz-123-456", "status": "Succeeded"}
    mock_job = Mock()
    mock_job.was_informed_by = was_informed_by
    mock_job.workflow_execution_id = workflow_execution_id
    mock_job.job.metadata = job_metadata


    # patch config.data_dir
    with patch("nmdc_automation.config.siteconfig.SiteConfig.data_dir", new_callable=PropertyMock) as mock_data_dir:
        mock_data_dir.return_value = tmp_path
        fh = FileHandler(site_config, initial_state_file_1_failure)

        # Act
        metadata_path = fh.write_metadata_if_not_exists(mock_job)

        # Assert
        assert metadata_path
        assert metadata_path.exists()
        assert metadata_path.is_file()


# JobManager tests
def test_job_manager_init(site_config, initial_state_file_1_failure):
    # Arrange
    fh = FileHandler(site_config, initial_state_file_1_failure)
    jm = JobManager(site_config, fh)
    assert jm
    assert jm.file_handler
    assert jm.file_handler.state_file


def test_job_manager_restore_from_state(site_config, initial_state_file_1_failure):
    # Arrange
    fh = FileHandler(site_config, initial_state_file_1_failure)
    jm = JobManager(site_config, fh, init_cache=False)
    # Act
    jm.restore_from_state()
    # Assert
    assert jm.job_cache
    assert isinstance(jm.job_cache, list)
    assert len(jm.job_cache) == 1
    assert isinstance(jm.job_cache[0], WorkflowJob)

    # job has been cached - get new workflow jobs from state should not return any
    new_jobs = jm.get_new_workflow_jobs_from_state()
    assert not new_jobs


def test_job_manager_job_checkpoint(site_config, initial_state_file_1_failure):
    # Arrange
    fh = FileHandler(site_config, initial_state_file_1_failure)
    jm = JobManager(site_config, fh)
    # Act
    data = jm.job_checkpoint()
    # Assert
    assert data
    assert isinstance(data, dict)
    assert data.get("jobs")
    assert isinstance(data.get("jobs"), list)
    assert len(data.get("jobs")) == 1


def test_job_manager_save_checkpoint(site_config, initial_state_file_1_failure):
    # Arrange
    fh = FileHandler(site_config, initial_state_file_1_failure)
    jm = JobManager(site_config, fh)
    # Act
    jm.save_checkpoint()
    # Assert
    assert fh.state_file.exists()
    assert fh.state_file.is_file()

    # cleanup
    fh.state_file.unlink()

def test_job_manager_find_job_by_opid(site_config, initial_state_file_1_failure):
    # Arrange
    fh = FileHandler(site_config, initial_state_file_1_failure)
    jm = JobManager(site_config, fh)
    # Act
    job = jm.find_job_by_opid("nmdc:test-opid")
    # Assert
    assert job
    assert isinstance(job, WorkflowJob)
    assert job.opid == "nmdc:test-opid"
    assert not job.done


def test_job_manager_prepare_and_cache_new_job(site_config, initial_state_file_1_failure, fixtures_dir):
    # Arrange
    fh = FileHandler(site_config, initial_state_file_1_failure)
    jm = JobManager(site_config, fh)
    new_job_state = json.load(open(fixtures_dir / "new_state_job.json"))
    assert new_job_state
    new_job = WorkflowJob(site_config, new_job_state)
    # Act
    opid = "nmdc:test-opid-2"
    job = jm.prepare_and_cache_new_job(new_job, opid)
    # Assert
    assert job
    assert isinstance(job, WorkflowJob)
    assert job.opid == opid
    assert not job.done
    # cleanup
    jm.job_cache = []


def test_job_manager_prepare_and_cache_new_job_force(site_config, initial_state_file_1_failure, fixtures_dir):
    # Arrange
    fh = FileHandler(site_config, initial_state_file_1_failure)
    jm = JobManager(site_config, fh)
    #already has an opid
    new_job_state = json.load(open(fixtures_dir / "mags_workflow_state.json"))
    assert new_job_state
    new_job = WorkflowJob(site_config, new_job_state)
    # Act
    opid = "nmdc:test-opid-1"
    job = jm.prepare_and_cache_new_job(new_job, opid, force=True)
    # Assert
    assert job
    assert isinstance(job, WorkflowJob)
    assert job.opid == opid
    assert not job.done
    assert job in jm.job_cache
    # resubmit the job without force it will return None
    job2 = jm.prepare_and_cache_new_job(job, opid)
    assert not job2
    # try again with force
    job2 = jm.prepare_and_cache_new_job(job, opid, force=True)
    assert job2
    assert isinstance(job2, WorkflowJob)
    assert job2.opid == opid


def test_job_manager_get_finished_jobs(site_config, initial_state_file_1_failure, fixtures_dir):

    # Arrange - initial state has 1 failure and is not done
    fh = FileHandler(site_config, initial_state_file_1_failure)
    jm = JobManager(site_config, fh)

    # Add a finished job: finished job is not done, but has a last_status of Succeeded
    new_job_state = json.load(open(fixtures_dir / "mags_workflow_state.json"))
    assert new_job_state
    new_job = WorkflowJob(site_config, new_job_state)
    jm.job_cache.append(new_job)
    # sanity check
    assert len(jm.job_cache) == 2

    # add a failed job
    failed_job_state = json.load(open(fixtures_dir / "failed_job_state_2.json"))
    assert failed_job_state
    failed_job = WorkflowJob(site_config, failed_job_state)
    assert failed_job.job_status.lower() == "failed"
    jm.job_cache.append(failed_job)
    # sanity check
    assert len(jm.job_cache) == 3

    # Mock requests for job status
    with requests_mock.Mocker() as m:
        # Mock the successful job status
        m.get(
            "http://localhost:8088/api/workflows/v1/9492a397-eb30-472b-9d3b-abc123456789/status",
            json={"status": "Succeeded"}
            )
        # Mock the failed job status
        m.get(
            "http://localhost:8088/api/workflows/v1/12345678-abcd-efgh-ijkl-9876543210/status",
            json={"status": "Failed"}
            )

        # Act
        successful_jobs, failed_jobs = jm.get_finished_jobs()
        # Assert
        assert successful_jobs
        assert failed_jobs
    # cleanup
    jm.job_cache = []


def test_job_manager_process_successful_job(site_config, initial_state_file_1_failure, fixtures_dir):
    # mock job.job.get_job_metadata - use fixture cromwell/succeded_metadata.json
    job_metadata = json.load(open(fixtures_dir / "mags_job_metadata.json"))
    with patch("nmdc_automation.workflow_automation.wfutils.CromwellRunner.get_job_metadata") as mock_get_metadata:
        mock_get_metadata.return_value = job_metadata

        # Arrange
        fh = FileHandler(site_config, initial_state_file_1_failure)
        jm = JobManager(site_config, fh)
        new_job_state = json.load(open(fixtures_dir / "mags_workflow_state.json"))
        assert new_job_state
        new_job = WorkflowJob(site_config, new_job_state)
        jm.job_cache.append(new_job)
        # Act
        db = jm.process_successful_job(new_job)
        # Assert
        assert db
        assert isinstance(db, Database)
        assert new_job.done
        assert new_job.job_status == "Succeeded"
        # cleanup
        jm.job_cache = []


def test_job_manager_get_finished_jobs_1_failure(site_config, initial_state_file_1_failure, fixtures_dir):
    # Arrange
    with requests_mock.Mocker() as mocker:
        # Mock the GET request for the workflow status
        mocker.get(
            "http://localhost:8088/api/workflows/v1/9492a397-eb30-472b-9d3b-abc123456789/status",
            json={"status": "Failed"}  # Mocked response body
        )
        fh = FileHandler(site_config, initial_state_file_1_failure)
        jm = JobManager(site_config, fh)
        # job handler should initialize the job_cache from the state file by default
        assert jm.job_cache
        assert isinstance(jm.job_cache, list)
        assert len(jm.job_cache) == 1

        successful_jobs, failed_jobs = jm.get_finished_jobs()
        assert not successful_jobs
        assert failed_jobs
        failed_job = failed_jobs[0]
        assert failed_job.job_status == "Failed"

@mock.patch("nmdc_automation.workflow_automation.wfutils.WorkflowStateManager.generate_submission_files")
def test_job_manager_process_failed_job_1_failure(
        mock_generate_submission_files, site_config, initial_state_file_1_failure, mock_cromwell_api):
    # Arrange
    mock_generate_submission_files.return_value = {
        "workflowSource": "workflowSource",
        "workflowDependencies": "workflowDependencies",
        "workflowInputs": "workflowInputs",
        "labels": "labels"
    }
    fh = FileHandler(site_config, initial_state_file_1_failure)
    jm = JobManager(site_config, fh)
    failed_job = jm.job_cache[0]
    # Act
    jobid = jm.process_failed_job(failed_job)
    assert jobid



def test_job_manager_process_failed_job_2_failures(site_config, initial_state_file_1_failure, fixtures_dir):
    # Arrange
    fh = FileHandler(site_config, initial_state_file_1_failure)
    jm = JobManager(site_config, fh)
    failed_job_state = json.load(open(fixtures_dir / "failed_job_state_2.json"))
    assert failed_job_state
    failed_job = WorkflowJob(site_config, failed_job_state)
    jm.job_cache.append(failed_job)
    # Act
    jm.process_failed_job(failed_job)
    # Assert
    assert failed_job.done
    assert failed_job.job_status == "Failed"


@fixture
def mock_runtime_api_handler(site_config, mock_api):
    pass

@mock.patch("nmdc_automation.workflow_automation.wfutils.CromwellRunner.submit_job")
def test_claim_jobs(mock_submit, site_config_file, site_config, fixtures_dir):
    # Arrange
    mock_submit.return_value = {"id": "nmdc:1234", "detail": {"id": "nmdc:1234"}}
    with patch(
            "nmdc_automation.workflow_automation.watch_nmdc.RuntimeApiHandler.claim_job"
            ) as mock_claim_job, requests_mock.Mocker() as m:
        mock_claim_job.return_value = {"id": "nmdc:1234", "detail": {"id": "nmdc:1234"}}
        job_state = json.load(open(fixtures_dir / "mags_workflow_state.json"))
        # remove the opid
        job_state.pop("opid")
        unclaimed_wfj = WorkflowJob(site_config, workflow_state=job_state)

        # mock the status URL response
        status_url = f"http://localhost:8088/api/workflows/v1/{unclaimed_wfj.job.job_id}/status"
        m.get(status_url, json={"id": "nmdc:1234", "status": "Succeeded"})

        w = Watcher(site_config_file)
        w.claim_jobs(unclaimed_jobs=[unclaimed_wfj])

        # Assert
        assert unclaimed_wfj.job_status


def test_runtime_manager_get_unclaimed_jobs(site_config, initial_state_file_1_failure, fixtures_dir, mock_api):
    # Arrange
    rt = RuntimeApiHandler(site_config)
    # Act
    unclaimed_jobs = rt.get_unclaimed_jobs(rt.config.allowed_workflows)
    # Assert
    assert unclaimed_jobs


def test_reclaim_job(requests_mock, site_config_file, mock_api):
    requests_mock.real_http = True

    w = Watcher(site_config_file)
    job_id = "nmdc:b7eb8cda-a6aa-11ed-b1cf-acde48001122"
    resp = {'id': 'nmdc:1234', 'detail': {'id': 'nmdc:1234'}}
    requests_mock.post(
        f"http://localhost/jobs/{job_id}:claim", json=resp, status_code=409
        )  # w.claim_jobs()  # resp = w.job_manager.find_job_by_opid("nmdc:1234")  # assert resp


def test_watcher_restore_from_checkpoint(site_config_file, fixtures_dir):
    state_file = fixtures_dir / "mags_workflow_state.json"
