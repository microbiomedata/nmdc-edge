""" Integration tests for the NMDC API. """

import pytest
import requests

from nmdc_automation.api.nmdcapi import NmdcRuntimeApi as nmdcapi



@pytest.mark.integration
def test_integration_environment():
    """
    Test that the integration environment is set up correctly:
    - Runtime API server is running on localhost port 8000
    - MongoDB is running on localhost port 27017
    - The site 'NERSC' exists in the API

    If any of these conditions are not met, the test will fail, and the remaining integration
    tests will be skipped.
    """
    # response = requests.get("http://localhost:8000")
    # assert response.status_code == 200
    assert False, "Unimplemented"




@pytest.mark.integration
def test_nmdcapi_basics(requests_mock, site_config_file):
    assert False, "Unimplemented"

