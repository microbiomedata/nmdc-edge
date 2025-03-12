"""
Integration tests for the JAWS API.

These tests expect a real Jaws token file to be present in a `.local` directory at the root of the repository.
The token file should be named `jaws.conf`.
.local directory is in the .gitignore file so it will not be committed to the repository.

Additionally, for the tests to access any of the jaws client functionality, the tests must
be running behind thge firewall in the NERSC environment.
"""

import pytest

from jaws_client import api
from jaws_client.config import Configuration
@pytest.mark.integration
def test_jaws_api_init(jaws_token_file, jaws_config_file_integration):
    config = Configuration.from_files(jaws_config_file_integration, jaws_token_file)
    jaws = api.JawsApi(config)
    assert jaws is not None


@pytest.mark.integration
def test_jaws_api_get_user(jaws_token_file, jaws_config_file_integration):
    config = Configuration.from_files(jaws_config_file_integration, jaws_token_file)
    jaws = api.JawsApi(config)
    user = jaws.get_user()
    assert user is not None
