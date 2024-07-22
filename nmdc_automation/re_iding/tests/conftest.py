import os
import shutil
import tempfile

import pytest
from pathlib import Path
import json

TEST_DATA_DIR = Path(__file__).parent / "test_data"

@pytest.fixture
def db_record():
    """Return a dict of a test Database instance"""
    with open(TEST_DATA_DIR / "db_record.json", "r") as f:
        return json.load(f)

@pytest.fixture
def data_object_record():
    """Return a dict of a test DataObject instance"""
    return {
        "name": "Gp0115663_Filtered Reads",
        "description": "Filtered Reads for Gp0115663",
        "data_object_type": "Filtered Sequencing Reads",
        "url": "https://data.microbiomedata.org/data/nmdc:mga0h9dt75/qa/nmdc_mga0h9dt75_filtered.fastq.gz",
        "md5_checksum": "7bf778baef033d36f118f8591256d6ef",
        "id": "nmdc:7bf778baef033d36f118f8591256d6ef",
        "file_size_bytes": 2571324879,
        "type": "nmdc:DataObject"
    }

@pytest.fixture
def metagenome_omics_processing_record():
    """Return a dict of a test nmdc_metagenome_omics_processing instance"""
    with open(TEST_DATA_DIR / "metagenome_omics_processing_record.json", "r") as f:
        return json.load(f)

@pytest.fixture
def igsn_biosample_record():
    """Return a dict of a test IGSN Biosample instance"""
    with open(TEST_DATA_DIR / "igsn_biosample_record.json", "r") as f:
        return json.load(f)

@pytest.fixture
def metabolomics_analysis_activity_record():
    """Return a dict of a test nmdc_metabolomics_analysis_activity instance"""
    with open(TEST_DATA_DIR / "metabolomics_analysis_activity_record.json", "r") as f:
        return json.load(f)

@pytest.fixture
def metabolomics_input_data_object_record():
    """Return a dict of a test nmdc_metabolomics_input_data_object instance"""
    with open(TEST_DATA_DIR / "metabolomics_input_data_object_record.json", "r") as f:
        return json.load(f)

@pytest.fixture
def metabolomics_output_data_object_record():
    """Return a dict of a test nmdc_metabolomics_output_data_object instance"""
    with open(TEST_DATA_DIR / "metabolomics_output_data_object_record.json", "r") as f:
        return json.load(f)

@pytest.fixture
def nom_activity_record_ndmc():
    """Return a dict of a test nmdc_nom_activity instance"""
    with open(TEST_DATA_DIR / "nom_activity_record_ndmc.json", "r") as f:
        return json.load(f)


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

@pytest.fixture
def data_dir(tmp_path):
    omics_dir = tmp_path / "results"
    omics_dir.mkdir(parents=True)
    return tmp_path
