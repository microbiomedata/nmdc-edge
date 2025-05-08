import os
import hashlib
import tempfile
import pytest

from nmdc_automation.import_automation.utils import get_or_create_md5  # replace with actual import


@pytest.fixture
def temp_file(tmp_path):
    file = tmp_path / "testfile.txt"
    file.write_text("hello world")
    return file


def compute_md5(content: bytes) -> str:
    return hashlib.md5(content).hexdigest()


def test_creates_md5_if_not_exists(temp_file):
    md5_file = temp_file.with_suffix(".txt.md5")
    assert not md5_file.exists()

    result = get_or_create_md5(str(temp_file))
    expected_md5 = compute_md5(b"hello world")

    assert result == expected_md5
    assert md5_file.exists()
    assert md5_file.read_text().strip() == expected_md5


def test_reads_md5_if_exists(temp_file):
    md5_file = temp_file.with_suffix(".txt.md5")
    md5_file.write_text("precomputedmd5\n")

    result = get_or_create_md5(str(temp_file))
    assert result == "precomputedmd5"
    # make sure it doesn’t overwrite existing md5
    assert md5_file.read_text().strip() == "precomputedmd5"


def test_md5_changes_with_file_content(tmp_path):
    file = tmp_path / "testfile.txt"
    file.write_text("foo")
    md5_file = file.with_suffix(".txt.md5")

    first_md5 = get_or_create_md5(str(file))
    assert md5_file.read_text().strip() == first_md5

    # change file content, delete md5 file
    file.write_text("bar")
    md5_file.unlink()

    second_md5 = get_or_create_md5(str(file))
    assert second_md5 != first_md5
    assert md5_file.read_text().strip() == second_md5


def test_empty_file_md5(tmp_path):
    file = tmp_path / "empty.txt"
    file.write_text("")
    expected_md5 = compute_md5(b"")

    result = get_or_create_md5(str(file))
    assert result == expected_md5

    md5_file = file.with_suffix(".txt.md5")
    assert md5_file.read_text().strip() == expected_md5
