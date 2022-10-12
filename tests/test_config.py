from src.config import config
import pytest

def test_config():
    conf = config()
    assert conf.conf
    assert conf.get_data_dir()
    assert conf.get_stage_dir()


def test_config_missing(monkeypatch):
    monkeypatch.setenv("WF_CONFIG_FILE", "/bogus")
    with pytest.raises(OSError):
        conf = config()
