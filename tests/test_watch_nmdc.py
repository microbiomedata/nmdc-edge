import copy
import json
from pathlib import PosixPath, Path
from pytest import fixture
import shutil
from unittest.mock import patch, PropertyMock, Mock

from nmdc_automation.workflow_automation.watch_nmdc import (
    Watcher,
    FileHandler,
    JobManager
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
    metadata = {'outputs': {"nmdc_rqcfilter.filtered_final": str(afile_path),
        "nmdc_rqcfilter.filtered_stats_final": str(bfile_path),
        "nmdc_rqcfilter.stats": {"input_read_count": 11431762, "input_read_bases": 1726196062,
            "output_read_bases": 1244017053, "output_read_count": 8312566}, }}
    requests_mock.get(f"{cromwell_url}/1234/metadata", json=metadata)
    data = {"status": "Succeeded"}
    requests_mock.get(f"{cromwell_url}/1234/status", json=data)


# FileHandler init tests
def test_file_handler_init_from_state_file(site_config, initial_state_file, tmp_path):
    copy_state_file = tmp_path / "copy_state.json"
    shutil.copy(initial_state_file, copy_state_file)
    fh = FileHandler(site_config, initial_state_file)
    assert fh
    assert fh.state_file
    assert isinstance(fh.state_file, PosixPath)
    assert fh.state_file.exists()
    assert fh.state_file.is_file()
    # delete state file
    fh.state_file = None
    assert not fh.state_file

    # test setter
    fh.state_file = initial_state_file
    assert fh.state_file
    assert fh.state_file.exists()
    assert fh.state_file.is_file()

    # unlink state file
    fh.state_file.unlink()
    assert not fh.state_file.exists()
    fh.state_file = copy_state_file
    assert fh.state_file.exists()
    assert fh.state_file.is_file()


def test_file_handler_init_from_config_agent_state(site_config, initial_state_file, tmp_path):
    with patch("nmdc_automation.config.siteconfig.SiteConfig.agent_state", new_callable=PropertyMock) as mock_agent_state:
        mock_agent_state.return_value = initial_state_file
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


def test_file_handler_read_state(site_config, initial_state_file):
    fh = FileHandler(site_config, initial_state_file)
    state = fh.read_state()
    assert state
    assert isinstance(state, dict)
    assert state.get("jobs")
    assert isinstance(state.get("jobs"), list)
    assert len(state.get("jobs")) == 1


def test_file_handler_write_state(site_config, initial_state_file, fixtures_dir):
    fh = FileHandler(site_config, initial_state_file)
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


def test_file_handler_get_output_path(site_config, initial_state_file, fixtures_dir):
    # Arrange
    was_informed_by = "nmdc:1234"
    workflow_execution_id = "nmdc:56789"
    mock_job = Mock()
    mock_job.was_informed_by = was_informed_by
    mock_job.workflow_execution_id = workflow_execution_id

    expected_output_path = site_config.data_dir / Path(was_informed_by) / Path(workflow_execution_id)

    fh = FileHandler(site_config, initial_state_file)

    # Act
    output_path = fh.get_output_path(mock_job)

    # Assert
    assert output_path
    assert isinstance(output_path, PosixPath)
    assert output_path == expected_output_path


def test_file_handler_write_metadata_if_not_exists(site_config, initial_state_file, fixtures_dir, tmp_path):
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
        fh = FileHandler(site_config, initial_state_file)

        # Act
        metadata_path = fh.write_metadata_if_not_exists(mock_job)

        # Assert
        assert metadata_path
        assert metadata_path.exists()
        assert metadata_path.is_file()


# JobManager tests
def test_job_manager_init(site_config, initial_state_file):
    # Arrange
    fh = FileHandler(site_config, initial_state_file)
    jm = JobManager(site_config, fh)
    assert jm
    assert jm.file_handler
    assert jm.file_handler.state_file


def test_job_manager_restore_from_state(site_config, initial_state_file):
    # Arrange
    fh = FileHandler(site_config, initial_state_file)
    jm = JobManager(site_config, fh, init_cache=False)
    # Act
    jm.restore_from_state()
    # Assert
    assert jm.job_cache
    assert isinstance(jm.job_cache, list)
    assert len(jm.job_cache) == 1
    assert isinstance(jm.job_cache[0], WorkflowJob)


def test_job_manager_job_checkpoint(site_config, initial_state_file):
    # Arrange
    fh = FileHandler(site_config, initial_state_file)
    jm = JobManager(site_config, fh)
    # Act
    data = jm.job_checkpoint()
    # Assert
    assert data
    assert isinstance(data, dict)
    assert data.get("jobs")
    assert isinstance(data.get("jobs"), list)
    assert len(data.get("jobs")) == 1


def test_job_manager_save_checkpoint(site_config, initial_state_file):
    # Arrange
    fh = FileHandler(site_config, initial_state_file)
    jm = JobManager(site_config, fh)
    # Act
    jm.save_checkpoint()
    # Assert
    assert fh.state_file.exists()
    assert fh.state_file.is_file()

    # cleanup
    fh.state_file.unlink()

def test_job_manager_find_job_by_opid(site_config, initial_state_file):
    # Arrange
    fh = FileHandler(site_config, initial_state_file)
    jm = JobManager(site_config, fh)
    # Act
    job = jm.find_job_by_opid("nmdc:test-opid")
    # Assert
    assert job
    assert isinstance(job, WorkflowJob)
    assert job.opid == "nmdc:test-opid"
    assert not job.done


def test_job_manager_prepare_and_cache_new_job(site_config, initial_state_file, fixtures_dir):
    # Arrange
    fh = FileHandler(site_config, initial_state_file)
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



@fixture
def mock_runtime_api_handler(site_config, mock_api):
    pass


def test_claim_jobs(site_config_file, site_config,  fixtures_dir):
    # Arrange
    with (patch("nmdc_automation.workflow_automation.watch_nmdc.RuntimeApiHandler.claim_job") as mock_claim_job):
        mock_claim_job.return_value = {"id": "nmdc:1234", "detail": {"id": "nmdc:1234"}}
        job_record = json.load(open(fixtures_dir / "mags_job_metadata.json"))
        unclaimed_wfj = WorkflowJob(site_config, job_record)
        w = Watcher(site_config_file)
        w.claim_jobs(unclaimed_jobs=[unclaimed_wfj])


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
