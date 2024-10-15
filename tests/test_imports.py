import os
import shutil
from nmdc_automation.import_automation.activity_mapper import GoldMapper
from pytest import fixture
from time import time



#TODO NOW: update to use real import.yaml file. Unclear if this is the right thing to do based on how the tests are set up. 
#ie we want to test that the binning packaging works even if we have this false by default for older projects where we want to annotate and re-bin.
#TODO NEXT: add test for import-mt.yaml similar to what is in test_workflow_process.py

@fixture
def gold_mapper(mock_api, base_test_dir, gold_import_files, gold_import_dir):
    """
    Base test function for code related to importing JGI records.
    """
    yaml_file = base_test_dir / "import_test.yaml"
    site_conf = base_test_dir / "site_configuration_test.toml"
    nucleotide_sequencing_id = "nmdc:omprc-11-importT"
    root_dir = f"/tmp/{nucleotide_sequencing_id}"
    if os.path.exists(root_dir):
        shutil.rmtree(root_dir)
    gm = GoldMapper("1", gold_import_files, nucleotide_sequencing_id, yaml_file, gold_import_dir, site_conf)
    gm.root_dir = root_dir
    return gm


def test_workflow_execution_mapper(gold_mapper):
    """
    Test the creation of workflow execution records and data objects that are has_output of those workflow execution subclasses.
    """
    gold_mapper.unique_object_mapper()
    gold_mapper.multiple_objects_mapper()
    gold_mapper.workflow_execution_mapper()
    gold_mapper.post_nmdc_database_object()
    db = gold_mapper.get_database_object_dump()
    #This should return 4 workflow_execution_set records becuase that is the number of records with Import:true in the config file
    #note that if these records were tested against the actual schema they would fail b/c workflow executions can't have has_output be null.
    assert len(db.workflow_execution_set) == 4
    # gff files are 1:1 with data objects that are has_output of nmdc:MetagenomeAnnotation
    # *tar.gz files should be combined into a single data object that is has_output of nmdc:MagsAnalysis
    assert len(db.data_object_set) == 3


def test_unique_object_mapper(gold_mapper):
    """
    This test counts the number of files from gold_mapper where the data object creation should be 1:1.
    """
    gold_mapper.unique_object_mapper()
    assert len(gold_mapper.nmdc_db.data_object_set) == 2
    assert len(gold_mapper.objects) == 2


def test_multiple_object_mapper(gold_mapper):
    """
    This test counts the number of files from gold_mapper where the data object creation should be many:1.  JGI stores each binning file 
    individually whereas NMDC combines all the records into a single tar.gz file.
    """
    gold_mapper.multiple_objects_mapper()
    # Add assertions to check if the method works as expected
    assert len(gold_mapper.nmdc_db.data_object_set) == 1
    print(gold_mapper.nmdc_db.data_object_set)
    assert len(gold_mapper.objects) == 1
    #check that the data object url gets made correctly for the multiple object mapper function.
    assert "https://data.microbiomedata.org/data/nmdc:omprc-11-importT/nmdc:abcd.1/nmdc_abcd.1_hqmq_bin.zip" in (do["url"] for do in gold_mapper.nmdc_db.data_object_set) 
