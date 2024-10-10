from nmdc_automation.workflow_automation.wfutils import (
    CromwellRunner,
    WorkflowJob,
    WorkflowStateManager
)
from nmdc_automation.workflow_automation.models import DataObject, workflow_process_factory
from nmdc_schema.nmdc import MagsAnalysis, EukEval
import json
import os
import pytest
import requests
import tempfile
from unittest import mock



def test_workflow_job(site_config, fixtures_dir):
    workflow_state = json.load(open(fixtures_dir / "mags_workflow_state.json"))
    job_metadata = json.load(open(fixtures_dir / "mags_job_metadata.json"))

    job = WorkflowJob(site_config, workflow_state, job_metadata)
    assert job
    assert job.workflow_execution_id == workflow_state['activity_id']


def test_cromwell_job_runner(site_config, fixtures_dir):
    # load cromwell metadata
    job_metadata = json.load(open(fixtures_dir / "mags_job_metadata.json"))
    job_state = json.load(open(fixtures_dir / "mags_workflow_state.json"))
    job_runner = CromwellRunner(site_config, job_state, job_metadata)
    assert job_runner


def test_cromwell_job_runner_get_job_status(site_config, fixtures_dir, mock_cromwell_api):
    # load cromwell metadata
    job_metadata = json.load(open(fixtures_dir / "mags_job_metadata.json"))
    job_state = json.load(open(fixtures_dir / "mags_workflow_state.json"))
    # successful job from the test fixtures
    job_state['cromwell_jobid'] = "cromwell-job-id-12345"
    job_metadata['id'] = "cromwell-job-id-12345"

    job_runner = CromwellRunner(site_config, job_state, job_metadata)
    status = job_runner.get_job_status()
    assert status
    assert status == "Succeeded"

    # failed job from the test fixtures
    job_state['cromwell_jobid'] = "cromwell-job-id-54321"
    job_metadata['id'] = "cromwell-job-id-54321"
    job_runner = CromwellRunner(site_config, job_state, job_metadata)
    status = job_runner.get_job_status()
    assert status
    assert status == "Failed"


def test_cromwell_job_runner_get_job_metadata(site_config, fixtures_dir, mock_cromwell_api):
    # load cromwell metadata
    job_metadata = json.load(open(fixtures_dir / "mags_job_metadata.json"))
    job_state = json.load(open(fixtures_dir / "mags_workflow_state.json"))
    # successful job from the test fixtures
    job_state['cromwell_jobid'] = "cromwell-job-id-12345"
    job_metadata['id'] = "cromwell-job-id-12345"

    job_runner = CromwellRunner(site_config, job_state, job_metadata)
    metadata = job_runner.get_job_metadata()
    assert metadata
    assert metadata['id'] == "cromwell-job-id-12345"
    # check that the metadata is cached
    assert job_runner.metadata == metadata


def test_cromwell_job_runner_submit_job(site_config, fixtures_dir, mock_cromwell_api):
    # load cromwell metadata
    job_metadata = json.load(open(fixtures_dir / "mags_job_metadata.json"))
    job_state = json.load(open(fixtures_dir / "mags_workflow_state.json"))
    # successful job from the test fixtures
    job_state['cromwell_jobid'] = "cromwell-job-id-12345"
    job_metadata['id'] = "cromwell-job-id-12345"

    job_runner = CromwellRunner(site_config, job_state, job_metadata)
    job_runner.submit_job()


def test_workflow_job_as_workflow_execution_dict(site_config, fixtures_dir):
    workflow_state = json.load(open(fixtures_dir / "mags_workflow_state.json"))
    job_metadata = json.load(open(fixtures_dir / "mags_job_metadata.json"))

    wfj = WorkflowJob(site_config, workflow_state, job_metadata)

    wfe_dict = wfj.as_workflow_execution_dict
    assert wfe_dict


def test_workflow_state_manager(fixtures_dir):
    mags_job_state = json.load(open(fixtures_dir / "mags_workflow_state.json"))

    state = WorkflowStateManager(mags_job_state)
    assert state.workflow_execution_id == mags_job_state['activity_id']
    assert state.config == mags_job_state['conf']
    assert state.execution_template == mags_job_state['conf']['activity']
    assert state.was_informed_by == mags_job_state['conf']['was_informed_by']


# Mock response content
MOCK_FILE_CONTENT = b"Test file content"
MOCK_CHUNK_SIZE = 1024  # Assume the CHUNK_SIZE is 1024 in your class

@mock.patch('requests.get')
def test_workflow_manager_fetch_release_file_success(mock_get, fixtures_dir):
    # Mock the response
    mock_get.return_value.iter_content.return_value = [MOCK_FILE_CONTENT]
    mock_get.return_value.status_code = 200

    # Test the function
    initial_state = json.load(open(fixtures_dir / "mags_workflow_state.json"))
    state = WorkflowStateManager(initial_state)

    file_path = state.fetch_release_file("test_file", ".txt")
    print(f"File path: {file_path}")

    assert file_path
    # assert os.path.exists(file_path)




def test_workflow_job_data_objects_and_execution_record_mags(site_config, fixtures_dir, tmp_path):
    # Note: test working dir must be the root of the project for this to work
    job_metadata = json.load(open(fixtures_dir / "mags_job_metadata.json"))
    workflow_state = json.load(open(fixtures_dir / "mags_workflow_state.json"))
    job = WorkflowJob(site_config, workflow_state, job_metadata)
    data_objects = job.make_data_objects(output_dir=tmp_path)
    assert data_objects
    for data_object in data_objects:
        assert isinstance(data_object, DataObject)
    wfe_dict = job.make_workflow_execution_record(data_objects)
    wfe = workflow_process_factory(wfe_dict)
    assert isinstance(wfe, MagsAnalysis)
    # attributes from final_stats_json
    assert wfe.mags_list
    assert isinstance(wfe.mags_list, list)
    # check for eukaryotic evaluation in each mag
    for mag in wfe.mags_list:
        assert mag.eukaryotic_evaluation
        assert isinstance(mag.eukaryotic_evaluation, EukEval)
        assert mag.eukaryotic_evaluation.completeness
        assert mag.eukaryotic_evaluation.contamination
        assert mag.eukaryotic_evaluation.ncbi_lineage
        assert mag.eukaryotic_evaluation.ncbi_lineage
    # check that the other final_stats props are there
    assert isinstance(wfe.input_contig_num, int)
    assert isinstance(wfe.too_short_contig_num, int)
    assert isinstance(wfe.unbinned_contig_num, int)
    assert isinstance(wfe.binned_contig_num, int)


def test_workflow_job_from_database_job_record(site_config, fixtures_dir):
    job_rec = json.load(open(fixtures_dir / "nmdc_api/unsubmitted_job.json"))
    assert job_rec
    job = WorkflowJob(site_config, job_rec)
    assert job
    assert job.workflow.nmdc_jobid == job_rec['id']
