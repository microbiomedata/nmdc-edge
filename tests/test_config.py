from nmdc_automation.config.config import Config
import pytest


def test_config(monkeypatch):
    monkeypatch.setenv("WF_CONFIG_FILE", "./test_data/wf_config")
    conf = Config("./configs/site_configuration.toml")
    assert conf.cromwell_api
    assert conf.cromwell_url
    assert conf.stage_dir
    assert conf.template_dir
    assert conf.data_dir
    assert conf.raw_dir
    assert conf.resource
    assert conf.site
    assert conf.url_root
    assert conf.api_url
    assert conf.watch_state
    assert conf.agent_state
    assert conf.activity_id_state
    assert conf.workflows_config
    assert conf.client_id
    assert conf.client_secret
    assert conf.allowed_workflows


def test_config_missing(monkeypatch):
    monkeypatch.setenv("WF_CONFIG_FILE", "/bogus")
    with pytest.raises(OSError):
        Config("/tmp/foo")
