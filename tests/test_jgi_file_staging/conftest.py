import configparser
import pytest
from pathlib import Path

FIXTURE_DIR = Path(__file__).parent / "fixtures"

@pytest.fixture
def config():
    config = configparser.ConfigParser()
    config.read(FIXTURE_DIR / "test_config.ini")
    return config



