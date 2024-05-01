import pysam
import pytest
import shutil
import tempfile
import os

from nmdc_automation.re_iding.file_utils import update_bam, md5_sum

@pytest.fixture
def sample_bam():
    # Path to the input BAM file in the test_data directory
    input_bam_path = "test_data/input.bam"

    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()

    # Copy the input BAM file to the temporary directory
    copied_bam_path = os.path.join(temp_dir, "input.bam")
    shutil.copy(input_bam_path, copied_bam_path)

    # Yield the path to the copied BAM file
    yield copied_bam_path

    # Teardown: Remove the temporary directory and its contents
    shutil.rmtree(temp_dir)


def test_sample_bam(sample_bam):
    # Check if the sample BAM file exists
    assert os.path.exists(sample_bam)

    # Check if the sample BAM file is not empty
    assert os.path.getsize(sample_bam) > 0


def test_modify_bam(sample_bam, tmpdir):
    # Define input and output BAM file paths
    input_bam = sample_bam
    output_bam = str(tmpdir.join("output.bam"))

    # Define old and new patterns for modification
    old_pattern = "nmdc:mga0zv48"
    new_pattern = "nmdc:updated_id"

    # Call the modify_bam function
    update_bam(input_bam, output_bam, old_pattern, new_pattern)

    # Check if the output BAM file exists
    assert os.path.exists(output_bam)

    # Check if the output BAM file is not empty
    assert os.path.getsize(output_bam) > 0

    # Check if the modification has been applied correctly
    with pysam.AlignmentFile(output_bam, "rb") as output_bam_file:
        for read in output_bam_file.fetch(until_eof=True):
            assert new_pattern in read.reference_name

    # Check if the MD5 checksum and file size are correct
    expected_md5 = md5_sum(output_bam)
    expected_size = os.path.getsize(output_bam)
    assert expected_md5, expected_size == update_bam(input_bam, output_bam, old_pattern, new_pattern)