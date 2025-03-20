"""
Integration tests for the JAWS API.

These tests expect a real Jaws token file to be present in a `.local` directory at the root of the repository.
The token file should be named `jaws.conf`.
.local directory is in the .gitignore file so it will not be committed to the repository.

Additionally, for the tests to access any of the jaws client functionality, the tests must
be running behind the firewall in the NERSC environment.
"""

import json
import pytest

from jaws_client import api
from jaws_client.config import Configuration

from nmdc_automation.workflow_automation.wfutils import (
    WorkflowJob,
    WorkflowStateManager,
    JawsRunner,
)


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
@pytest.mark.parametrize("fixture", ["rqc_workflow_state.json"])
def test_jaws_job_runner_jaws_validate(site_config, fixtures_dir, jaws_token_file, jaws_config_file_integration,
                                      fixture):
    config = Configuration.from_files(jaws_config_file_integration, jaws_token_file)
    jaws_api = api.JawsApi(config)

    job_state = json.load(open(fixtures_dir / fixture))
    state_manager = WorkflowStateManager(job_state)

    runner = JawsRunner(site_config, state_manager, jaws_api)
    submission_files = runner.generate_submission_files()
    validation_resp = jaws_api.validate(shell_check=False, wdl_file=submission_files["wdl_file"],
                                        inputs_file=submission_files["inputs"])
    print(validation_resp)
    assert validation_resp["result"] == "succeeded"


