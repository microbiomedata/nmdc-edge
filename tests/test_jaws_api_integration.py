"""
Integration tests for the JAWS API.

These tests expect a real Jaws token file to be present in a `.local` directory at the root of the repository.
The token file should be named `jaws.conf`.
.local directory is in the .gitignore file so it will not be committed to the repository.

Additionally, for the tests to access any of the jaws client functionality, the tests must
be running behind the firewall in the NERSC environment.
"""

import json
import logging
import os
import pytest
import zipfile

from jaws_client import api
from jaws_client.config import Configuration

from nmdc_automation.workflow_automation.wfutils import (
    WorkflowJob,
    WorkflowStateManager,
    JawsRunner,
)

logging_level = os.getenv("NMDC_LOG_LEVEL", logging.INFO)
logging.basicConfig(
    level=logging_level, format="%(asctime)s %(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)


@pytest.mark.jaws
def test_jaws_api_init(jaws_token_file, jaws_config_file_integration):
    config = Configuration.from_files(jaws_config_file_integration, jaws_token_file)
    jaws = api.JawsApi(config)
    assert jaws is not None


@pytest.mark.jaws
def test_jaws_api_get_user(jaws_token_file, jaws_config_file_integration):
    config = Configuration.from_files(jaws_config_file_integration, jaws_token_file)
    jaws = api.JawsApi(config)
    user = jaws.get_user()
    assert user is not None


@pytest.mark.jaws
@pytest.mark.parametrize(
    "fixture", ["rqc_workflow_state.json", "meta_assembly_workflow_state.json",
                "read_based_analysis_workflow_state.json", "mags_workflow_state.json"]
    )
def test_jaws_job_runner_jaws_validate(site_config, fixtures_dir, jaws_token_file, jaws_config_file_integration,
                                       fixture):
    config = Configuration.from_files(jaws_config_file_integration, jaws_token_file)
    jaws_api = api.JawsApi(config)

    job_state = json.load(open(fixtures_dir / fixture))
    state_manager = WorkflowStateManager(job_state)

    runner = JawsRunner(site_config, state_manager, jaws_api)
    submission_files = runner.generate_submission_files()

    # For now, we have to manually unzip the sub workflow zip file
    if submission_files['sub']:
        extract_dir = os.path.dirname(submission_files["sub"])
        with zipfile.ZipFile(submission_files["sub"], 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

    validation_resp = jaws_api.validate(
        shell_check=False, wdl_file=submission_files["wdl_file"],
        inputs_file=submission_files["inputs"]
        )
    print(validation_resp)
    assert validation_resp["result"] == "succeeded"

# @pytest.mark.jaws
# @pytest.mark.parametrize("fixture", ["rqc_workflow_state.json", "meta_assembly_workflow_state.json"])
# def test_jaws_job_runner_jaws_submit(site_config, fixtures_dir, jaws_token_file, jaws_config_file_integration,
#                                      fixture):
#     config = Configuration.from_files(jaws_config_file_integration, jaws_token_file)
#     jaws_api = api.JawsApi(config)
#
#     job_state = json.load(open(fixtures_dir / fixture))
#     state_manager = WorkflowStateManager(job_state)
#
#     runner = JawsRunner(site_config, state_manager, jaws_api)
#     run_id = runner.submit_job()
#     assert run_id is not None
#     assert runner.job_id == run_id
