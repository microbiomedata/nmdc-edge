"""
Integration tests for the JAWS API.
"""

import pytest

from jaws_client import api
from jaws_client.config import Configuration

def test_jaws_api_init(jaws_token_file, jaws_config_file):
    config = Configuration.from_files(jaws_config_file, jaws_token_file)
    jaws = api.JawsApi(config)
    assert jaws is not None


@pytest.mark.integration
def test_jaws_api_health(jaws_token_file, jaws_config_file):
    config = Configuration.from_files(jaws_config_file, jaws_token_file)
    jaws = api.JawsApi(config)
    health = jaws.health()
    assert health is not None
    # 