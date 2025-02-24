"""
Integration tests for the NMDC API. These tests require the NMDC API to be running on localhost
"""

from time import time

import pytest
import requests

from nmdc_automation.api.nmdcapi import NmdcRuntimeApi as nmdcapi


@pytest.mark.integration_local
def test_integration_environment():
    """
    Test that the integration environment is set up correctly:
    - Runtime API server is running on localhost port 8000
    - The site 'NERSC' exists in the sites endpoint

    If any of these conditions are not met, the test will fail, and the remaining integration
    tests will be skipped.
    """
    response = requests.get("http://localhost:8000")
    assert response.status_code == 200

    response = requests.get("http://localhost:8000/sites/NERSC")
    assert response.status_code == 200
    response_body = response.json()
    assert response_body["id"] == "NERSC"


@pytest.mark.integration_local
def test_nmdcapi_get_token(site_config_file):
    n = nmdcapi(site_config_file)

    assert n.expires_at == 0
    token_resp = n.get_token()
    assert token_resp["expires"]["days"] == 1
    assert token_resp["access_token"] is not None
    # should be at least an hour in the future
    assert n.expires_at >= time() + 3600
    assert n.token is not None


@pytest.mark.integration_local
def test_nmdcapi_list_jobs_refreshes_token(site_config_file):
    # initial client state - no token
    n = nmdcapi(site_config_file)
    assert n.expires_at == 0
    assert n.token is None

    # list_jobs will invoke refresh_token
    jobs = n.list_jobs()
    assert jobs is not None
    assert n.token is not None
    # should be at least an hour in the future
    assert n.expires_at > time() + 3600

    # set the token to expire now
    n.expires_at = time()
    assert n.expires_at < time()
    jobs = n.list_jobs()
    assert jobs is not None
    assert n.token is not None
    # should be at least an hour in the future again
    assert n.expires_at > time() + 3600
