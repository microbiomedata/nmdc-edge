from nmdc_automation.workflow_automation.config import config
import pytest


def test_config(monkeypatch):
    monkeypatch.setenv("WF_CONFIG_FILE", "./test_data/wf_config")
    conf = config()
    assert conf.conf
    assert conf.get_data_dir()
    assert conf.get_stage_dir()


def test_config_missing(monkeypatch):
    monkeypatch.setenv("WF_CONFIG_FILE", "/bogus")
    with pytest.raises(OSError):
        config()
