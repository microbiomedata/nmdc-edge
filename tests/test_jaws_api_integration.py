"""
Integration tests for the JAWS API.
"""

import pytest

from jaws_client import api
from jaws_client.config import Configuration

def test_jaws_api_init(jaws_token_file, jaws_config_file_test):
    config = Configuration.from_files(jaws_config_file_test, jaws_token_file)
    jaws = api.JawsApi(config)
    assert jaws is not None


@pytest.mark.integration
def test_jaws_api_get_user(jaws_token_file, jaws_config_file_test):
    config = Configuration.from_files(jaws_config_file_test, jaws_token_file)
    jaws = api.JawsApi(config)
    user = jaws.get_user()
    assert user is not None
