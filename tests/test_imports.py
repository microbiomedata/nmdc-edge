import os
import shutil
from nmdc_automation.import_automation.activity_mapper import GoldMapper
from nmdc_automation.models.nmdc import DataObject
from nmdc_schema.nmdc import Database
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


# def test_workflow_execution_mapper(gold_mapper):
#     """
#     Test the creation of workflow execution records and data objects that are has_output of those workflow execution subclasses.
#     """
#     gold_mapper.unique_object_mapper()
#     gold_mapper.multiple_objects_mapper()
#     gold_mapper.workflow_execution_mapper()
#     gold_mapper.post_nmdc_database_object()
#     db = gold_mapper.get_database_object_dump()
#     #This should return 4 workflow_execution_set records becuase that is the number of records with Import:true in the config file
#     #note that if these records were tested against the actual schema they would fail b/c workflow executions can't have has_output be null.
#     assert len(db.workflow_execution_set) == 4
#     # gff files are 1:1 with data objects that are has_output of nmdc:MetagenomeAnnotation
#     # *tar.gz files should be combined into a single data object that is has_output of nmdc:MagsAnalysis
#     assert len(db.data_object_set) == 3


# def test_unique_object_mapper(gold_mapper):
#     """
#     This test counts the number of files from gold_mapper where the data object creation should be 1:1.
#     """
#     gold_mapper.unique_object_mapper()
#     assert len(gold_mapper.nmdc_db.data_object_set) == 2
#     assert len(gold_mapper.data_object_map) == 2


# def test_multiple_object_mapper(gold_mapper):
#     """
#     This test counts the number of files from gold_mapper where the data object creation should be many:1.  JGI stores each binning file
#     individually whereas NMDC combines all the records into a single tar.gz file.
#     """
#     gold_mapper.multiple_objects_mapper()
#     # Add assertions to check if the method works as expected
#     assert len(gold_mapper.nmdc_db.data_object_set) == 1
#     print(gold_mapper.nmdc_db.data_object_set)
#     assert len(gold_mapper.objects) == 1
#     #check that the data object url gets made correctly for the multiple object mapper function.
#     assert "https://data.microbiomedata.org/data/nmdc:omprc-11-importT/nmdc:abcd.1/nmdc_abcd.1_hqmq_bin.zip" in (do["url"] for do in gold_mapper.nmdc_db.data_object_set)

def test_gold_mapper_map_sequencing_data(gold_mapper):
    """
    Test that the gold mapper creates data objects for the sequencing data, and
    provides an update to be applied to the has_output list of the sequencing data generation
    """
    exp_num_data_objects = 1    # There is only one sequencing data file from the gold import files fixture
    exp_dobj_id = "nmdc:dobj-01-abcd1234"   # From the mock API minter response
    exp_dobj_type = "Metagenome Raw Reads"  # From the gold_import_files fixture
    exp_nucleotide_sequencing_id = "nmdc:omprc-11-importT"  # From the gold mapper fixture
    exp_update = {
        "collection": "data_generation_set",
        "filter": {"id": exp_nucleotide_sequencing_id},
        "update": {"has_output": [exp_dobj_id]}
    }
    # TODO verify that these are the correct values to expect based on the import logic for raw reads files
    exp_url = 'https://data.microbiomedata.org/data/nmdc:omprc-11-importT/52834.4.466476.GATCGAGT-GATCGAGT.fastq.gz'
    exp_name = '52834.4.466476.GATCGAGT-GATCGAGT.fastq.gz'
    exp_description = 'Metagenome Raw Reads for nmdc:omprc-11-importT'

    db, update = gold_mapper.map_sequencing_data()
    # Database assertions
    assert db
    assert isinstance(db, Database)
    assert db.data_object_set
    data_objects = db.data_object_set
    assert len(data_objects) == exp_num_data_objects
    # Data object assertions
    dobj = data_objects[0]
    assert isinstance(dobj, DataObject)
    assert dobj.data_object_type == exp_dobj_type
    assert dobj.id == exp_dobj_id
    assert dobj.name == exp_name
    assert dobj.description == exp_description
    assert dobj.url == exp_url
    assert dobj.file_size_bytes
    assert dobj.md5_checksum

    # Update assertions
    assert update
    assert update == exp_update


def test_gold_mapper_map_data_unique(gold_mapper):
    """
    Test that the gold mapper creates data objects for the data files other
    than the sequencing data
    """
    initial_num_data_objects = 1
    db, update = gold_mapper.map_sequencing_data()
    # sanity check
    assert len(db.data_object_set) == initial_num_data_objects
    exp_num_data_objects = 3    # two unique data files from the gold import files fixture get added to the database
    exp_data_object_types = [
        "Clusters of Orthologous Groups (COG) Annotation GFF", "Pfam Annotation GFF", "Metagenome Raw Reads"]
    exp_do_map = {'Clusters of Orthologous Groups (COG) Annotation GFF': (
    ['nmdc:MagsAnalysis'], ['nmdc:MetagenomeAnnotation'], 'nmdc:dobj-01-abcd1234'), 'Pfam Annotation GFF': (
    ['nmdc:MagsAnalysis'], ['nmdc:MetagenomeAnnotation'], 'nmdc:dobj-01-abcd1234')}
    exp_nucleotide_sequencing_id = "nmdc:omprc-11-importT"  # From the gold mapper fixture

    db, do_map = gold_mapper.map_data(db)
    assert db
    assert len(db.data_object_set) == exp_num_data_objects
    data_objects = db.data_object_set
    for dobj in data_objects:
        assert dobj.data_object_type in exp_data_object_types
        assert isinstance(dobj, DataObject)
        assert dobj.url
        assert exp_nucleotide_sequencing_id in dobj.url
        assert exp_nucleotide_sequencing_id in dobj.description
        assert exp_nucleotide_sequencing_id in dobj.name
    assert do_map == exp_do_map


def test_gold_mapper_map_data_multiple(gold_mapper):
    """
    Test that the gold mapper creates data objects for the data files other
    than the sequencing data
    """
    initial_num_data_objects = 1
    db, update = gold_mapper.map_sequencing_data()
    # sanity check
    assert len(db.data_object_set) == initial_num_data_objects
    exp_num_data_objects = 2    # two files are combined into a single data object

    db, do_map = gold_mapper.map_data(db, unique=False)
    assert db
    assert len(db.data_object_set) == exp_num_data_objects

