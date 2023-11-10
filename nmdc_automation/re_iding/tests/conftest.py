import pytest
from pathlib import Path
import json

TEST_DATA_DIR = Path(__file__).parent / "test_data"

@pytest.fixture
def db_record():
    """Return a dict of a test Database instance"""
    with open(TEST_DATA_DIR / "db_record.json", "r") as f:
        return json.load(f)
