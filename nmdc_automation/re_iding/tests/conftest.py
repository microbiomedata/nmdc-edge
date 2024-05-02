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