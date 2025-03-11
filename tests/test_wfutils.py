
from nmdc_automation.workflow_automation.wfutils import (
    CromwellRunner,
    WorkflowJob,
    WorkflowStateManager,
    JawsRunner,
)
from nmdc_automation.models.nmdc import DataObject
from nmdc_schema.nmdc import MagsAnalysis, EukEval
import io
import json
import os
import pytest
import requests
from unittest import mock
import importlib.resources
import yaml
from functools import lru_cache

from jaws_client.api import JawsApi
from jaws_client.config import Configuration


@lru_cache(maxsize=None)
def get_nmdc_materialized():
    with importlib.resources.open_text("nmdc_schema", "nmdc_materialized_patterns.yaml") as f:
        return yaml.safe_load(f)


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
    state_manager = WorkflowStateManager(job_state)
    job_runner = CromwellRunner(site_config, state_manager, job_metadata)
    assert job_runner


def test_cromwell_job_runner_get_job_status(site_config, fixtures_dir, mock_cromwell_api):
    # load cromwell metadata
    job_metadata = json.load(open(fixtures_dir / "mags_job_metadata.json"))
    job_state = json.load(open(fixtures_dir / "mags_workflow_state.json"))
    # successful job from the test fixtures
    job_state['cromwell_jobid'] = "cromwell-job-id-12345"
    job_metadata['id'] = "cromwell-job-id-12345"

    state_manager = WorkflowStateManager(job_state)
    job_runner = CromwellRunner(site_config, state_manager, job_metadata)
    status = job_runner.get_job_status()
    assert status
    assert status == "Succeeded"

    # failed job from the test fixtures
    job_state['cromwell_jobid'] = "cromwell-job-id-54321"
    job_metadata['id'] = "cromwell-job-id-54321"
    state_manager = WorkflowStateManager(job_state)
    job_runner = CromwellRunner(site_config, state_manager, job_metadata)
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

    state_manager = WorkflowStateManager(job_state)
    job_runner = CromwellRunner(site_config, state_manager, job_metadata)
    metadata = job_runner.get_job_metadata()
    assert metadata
    assert metadata['id'] == "cromwell-job-id-12345"
    # check that the metadata is cached
    assert job_runner.metadata == metadata


def test_jaws_job_runner(site_config, fixtures_dir, jaws_config_file_test, jaws_test_token_file):
    job_state = json.load(open(fixtures_dir / "mags_workflow_state.json"))
    state_manager = WorkflowStateManager(job_state)
    config = Configuration.from_files(jaws_config_file_test, jaws_test_token_file)
    api = JawsApi(config)
    job_runner = JawsRunner(site_config, state_manager, api)
    assert job_runner


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
    mock_response = mock.Mock()
    mock_response.iter_content = mock.Mock(
        return_value=[MOCK_FILE_CONTENT[i:i + MOCK_CHUNK_SIZE]
                      for i in range(0, len(MOCK_FILE_CONTENT), MOCK_CHUNK_SIZE)]
        )
    mock_response.status_code = 200
    mock_get.return_value = mock_response

    # Test the function
    initial_state = json.load(open(fixtures_dir / "mags_workflow_state.json"))
    state = WorkflowStateManager(initial_state)

    file_path = state.fetch_release_file("test_file", ".txt")
    print(f"File path: {file_path}")

    assert file_path
    assert os.path.exists(file_path), f"File not found at {file_path}"
    with open(file_path, 'rb') as f:
        assert f.read() == MOCK_FILE_CONTENT

    os.remove(file_path)


@mock.patch('requests.get')
def test_workflow_manager_fetch_release_file_failed_download(mock_get, fixtures_dir):
    # Mock a failed request
    mock_response = mock.Mock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Client Error: Not Found")
    mock_get.return_value = mock_response

    # Test the function
    initial_state = json.load(open(fixtures_dir / "mags_workflow_state.json"))
    state = WorkflowStateManager(initial_state)

    with pytest.raises(requests.exceptions.HTTPError):
        state.fetch_release_file("test_file", ".txt")

    # Check that the file was not created
    assert not os.path.exists("test_file.txt")


@mock.patch('requests.get')
def test_workflow_manager_fetch_release_file_failed_write(mock_get, fixtures_dir):
    # Mock the response
    mock_response = mock.Mock()
    mock_response.iter_content = mock.Mock(
        return_value=[MOCK_FILE_CONTENT[i:i + MOCK_CHUNK_SIZE]
                      for i in range(0, len(MOCK_FILE_CONTENT), MOCK_CHUNK_SIZE)]
        )
    mock_response.status_code = 200
    mock_get.return_value = mock_response

    # Patch the tempfile.mkstemp function to raise an exception during file creation
    with mock.patch('tempfile.NamedTemporaryFile', side_effect=OSError("Failed to create file")):
        # Test the function
        initial_state = json.load(open(fixtures_dir / "mags_workflow_state.json"))
        state = WorkflowStateManager(initial_state)

        with pytest.raises(OSError):
            state.fetch_release_file("test_file", ".txt")

        # Check that the file was not created
        assert not os.path.exists("test_file.txt")


def test_cromwell_runner_setup_inputs_and_labels(site_config, fixtures_dir):
    job_state = json.load(open(fixtures_dir / "mags_workflow_state.json"))
    workflow = WorkflowStateManager(job_state)
    runner = CromwellRunner(site_config, workflow)
    inputs = runner._generate_workflow_inputs()
    assert inputs
    # we expect the inputs to be a key-value dict with URLs as values
    for key, value in inputs.items():
        if key.endswith("file"):
            assert value.startswith("http")

    labels = runner._generate_workflow_labels()
    assert labels
    assert labels['submitter'] == "nmdcda"
    assert labels['git_repo'].startswith("https://github.com/microbiomedata")
    assert labels['pipeline'] == labels['wdl']


@mock.patch("nmdc_automation.workflow_automation.wfutils.WorkflowStateManager.fetch_release_file")
def test_cromwell_runner_generate_submission_files( mock_fetch_release_file, site_config, fixtures_dir):
    mock_fetch_release_file.side_effect = [
        '/tmp/test_workflow.wdl',
        '/tmp/test_bundle.zip',
    ]
    job_state = json.load(open(fixtures_dir / "mags_workflow_state.json"))
    assert job_state
    workflow = WorkflowStateManager(job_state)

    # Now mock 'open' for the workflow submission files
    with mock.patch("builtins.open", new_callable=mock.mock_open) as mock_open:
        # Create 6 BytesIO objects for each expected open() call.
        fake_file_1 = io.BytesIO(b"mock wdl file content")  # workflowSource
        fake_file_2 = io.BytesIO(b"mock bundle file content")  # workflowDependencies
        fake_file_3 = io.BytesIO(b'{"key": "value"}')  # workflowInputs (binary mode)
        fake_file_4 = io.BytesIO(b'{"label": "test"}')  # labels (binary mode)
        fake_file_5 = io.BytesIO(b'{"key": "value"}')  # workflowInputs (text mode read)
        fake_file_6 = io.BytesIO(b'{"label": "test"}')  # labels (text mode read)

        # Optionally, assign a fake name to each (see next section).
        fake_file_1.name = "/tmp/test_workflow.wdl"
        fake_file_2.name = "/tmp/test_bundle.zip"
        fake_file_3.name = "/tmp/test_workflow_inputs.json"
        fake_file_4.name = "/tmp/test_workflow_labels.json"
        fake_file_5.name = "/tmp/test_workflow_inputs.json"
        fake_file_6.name = "/tmp/test_workflow_labels.json"

        mock_open.side_effect = [
            fake_file_1,
            fake_file_2,
            fake_file_3,
            fake_file_4,
            fake_file_5,
            fake_file_6,
        ]

        runner = CromwellRunner(site_config, workflow)
        submission_files = runner.generate_submission_files()
        assert submission_files
        assert "workflowSource" in submission_files
        assert "workflowDependencies" in submission_files
        assert "workflowInputs" in submission_files
        assert "labels" in submission_files

        # check that the files were written
        assert mock_open.call_count == 6
        mock_open.assert_any_call("/tmp/test_workflow.wdl", 'rb')
        mock_open.assert_any_call("/tmp/test_bundle.zip", 'rb')


@mock.patch("nmdc_automation.workflow_automation.wfutils.WorkflowStateManager.fetch_release_file")
@mock.patch("nmdc_automation.workflow_automation.wfutils._cleanup_files")
def test_cromwell_runner_generate_submission_files_exception(mock_cleanup_files, mock_fetch_release_file,
                                                             site_config, fixtures_dir):
    # Mock file fetching
    mock_fetch_release_file.side_effect = [
        '/tmp/test_workflow.wdl',  # First file fetch is successful
        '/tmp/test_bundle.zip',  # Second file fetch is successful
    ]
    job_state = json.load(open(fixtures_dir / "mags_workflow_state.json"))
    assert job_state
    workflow = WorkflowStateManager(job_state)

    # Now mock 'open' for the workflow submission files
    with mock.patch("builtins.open", new_callable=mock.mock_open) as mock_open:
        mock_open.side_effect = [
            io.BytesIO(b"mock wdl file content"),  # workflowSource file
            io.BytesIO(b"mock bundle file content"),  # workflowDependencies file
            OSError("Failed to open file"),  # workflowInputs file
            io.BytesIO(b"mock labels")  # labels file
        ]
        runner = CromwellRunner(site_config, workflow)
        with pytest.raises(OSError):
            runner.generate_submission_files()
        # Check that the cleanup function was called
        mock_cleanup_files.assert_called_once()


@mock.patch("nmdc_automation.workflow_automation.wfutils.WorkflowStateManager.fetch_release_file")
def test_jaws_job_runner_generate_submission_files(mock_fetch_release_file, site_config, fixtures_dir, jaws_config_file_test, jaws_test_token_file):
    mock_fetch_release_file.side_effect = [
        '/tmp/test_workflow.wdl',
        '/tmp/test_bundle.zip',
    ]
    job_state = json.load(open(fixtures_dir / "mags_workflow_state.json"))
    state_manager = WorkflowStateManager(job_state)
    config = Configuration.from_files(jaws_config_file_test, jaws_test_token_file)
    api = JawsApi(config)
    job_runner = JawsRunner(site_config, state_manager, api)
    assert job_runner

    # Now mock 'open' for the workflow submission files
    with mock.patch("builtins.open", new_callable=mock.mock_open) as mock_open:
        # Create 4 BytesIO objects for each expected open() call.
        fake_file_1 = io.BytesIO(b"mock wdl file content")
        fake_file_2 = io.BytesIO(b"mock bundle file content")
        fake_file_3 = io.BytesIO(b'{"key": "value"}') # workflowInputs (binary mode)
        fake_file_4 = io.BytesIO(b'{"key": "value"}') # workflowInputs (text mode read)

        fake_file_1.name = "/tmp/test_workflow.wdl"
        fake_file_2.name = "/tmp/test_bundle.zip"
        fake_file_3.name = "/tmp/test_workflow_inputs.json"
        fake_file_4.name = "/tmp/test_workflow_inputs.json"

        mock_open.side_effect = [
            fake_file_1,
            fake_file_2,
            fake_file_3,
            fake_file_4
        ]

        submission_files = job_runner.generate_submission_files()
        assert submission_files
        assert "workflowSource" in submission_files
        assert "workflowDependencies" in submission_files
        assert "workflowInputs" in submission_files

        # check that the files were written
        assert mock_open.call_count == 4
        mock_open.assert_any_call("/tmp/test_workflow.wdl", 'rb')
        mock_open.assert_any_call("/tmp/test_bundle.zip", 'rb')




@mock.patch("nmdc_automation.workflow_automation.wfutils.CromwellRunner.generate_submission_files")
def test_cromwell_job_runner_submit_job_new_job(mock_generate_submission_files, site_config, fixtures_dir, mock_cromwell_api):
    mock_generate_submission_files.return_value = {
        "workflowSource": "workflowSource",
        "workflowDependencies": "workflowDependencies",
        "workflowInputs": "workflowInputs",
        "labels": "labels"
    }
    # A new workflow job that has not been submitted - it has a workflow state
    # but no job metadata
    wf_state = json.load(open(fixtures_dir / "mags_workflow_state.json"))
    wf_state['last_status'] = None # simulate a job that has not been submitted
    wf_state['cromwell_jobid'] = None # simulate a job that has not been submitted
    wf_state['done'] = False # simulate a job that has not been submitted

    wf_state_manager = WorkflowStateManager(wf_state)
    job_runner = CromwellRunner(site_config, wf_state_manager)
    jobid = job_runner.submit_job()
    assert jobid


def test_workflow_job_data_objects_and_execution_record_mags(site_config, fixtures_dir, tmp_path):
    job_metadata = json.load(open(fixtures_dir / "mags_job_metadata.json"))
    workflow_state = json.load(open(fixtures_dir / "mags_workflow_state.json"))
    job = WorkflowJob(site_config, workflow_state, job_metadata)
    data_objects = job.make_data_objects(output_dir=tmp_path)
    assert data_objects
    for data_object in data_objects:
        assert isinstance(data_object, DataObject)
    wfe = job.make_workflow_execution(data_objects)
    assert wfe.started_at_time
    assert wfe.ended_at_time
    assert isinstance(wfe, MagsAnalysis)
    # attributes from final_stats_json
    assert wfe.mags_list
    assert isinstance(wfe.mags_list, list)
    # check for eukaryotic evaluation in each mag
    for mag in wfe.mags_list:
        assert mag.eukaryotic_evaluation
        assert isinstance(mag.eukaryotic_evaluation, EukEval)
        assert mag.eukaryotic_evaluation.completeness
        assert isinstance(mag.eukaryotic_evaluation.completeness, float)
        assert mag.eukaryotic_evaluation.contamination
        assert isinstance(mag.eukaryotic_evaluation.contamination, float)
        assert mag.eukaryotic_evaluation.ncbi_lineage
        assert mag.eukaryotic_evaluation.ncbi_lineage
    # check that the other final_stats props are there
    assert isinstance(wfe.input_contig_num, int)
    assert isinstance(wfe.too_short_contig_num, int)
    assert isinstance(wfe.unbinned_contig_num, int)
    assert isinstance(wfe.binned_contig_num, int)


def test_workflow_execution_record_from_workflow_job(site_config, fixtures_dir, tmp_path):
    job_metadata = json.load(open(fixtures_dir / "mags_job_metadata.json"))
    workflow_state = json.load(open(fixtures_dir / "mags_workflow_state.json"))
    # remove 'end' from the workflow state to simulate a job that is still running
    workflow_state.pop('end')
    job = WorkflowJob(site_config, workflow_state, job_metadata)
    data_objects = job.make_data_objects(output_dir=tmp_path)

    wfe = job.make_workflow_execution(data_objects)
    assert wfe.started_at_time
    assert wfe.ended_at_time


def test_make_data_objects_includes_workflow_execution_id_and_file_size(site_config, fixtures_dir, tmp_path):
    job_metadata = json.load(open(fixtures_dir / "mags_job_metadata.json"))
    workflow_state = json.load(open(fixtures_dir / "mags_workflow_state.json"))
    job = WorkflowJob(site_config, workflow_state, job_metadata)
    data_objects = job.make_data_objects(output_dir=tmp_path)
    assert data_objects
    for data_object in data_objects:
        assert isinstance(data_object, DataObject)
        assert job.workflow_execution_id in data_object.description
        assert data_object.file_size_bytes


def test_workflow_job_from_database_job_record(site_config, fixtures_dir):
    job_rec = json.load(open(fixtures_dir / "nmdc_api/unsubmitted_job.json"))
    assert job_rec
    job = WorkflowJob(site_config, job_rec)
    assert job
    assert job.workflow.nmdc_jobid == job_rec['id']
