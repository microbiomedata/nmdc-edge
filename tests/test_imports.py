import os
import shutil
from nmdc_automation.import_automation.activity_mapper import GoldMapper
from nmdc_automation.models.nmdc import DataObject
from nmdc_schema.nmdc import Database
from pytest import fixture
import importlib.resources
import yaml
from functools import lru_cache
import linkml.validator
from linkml_runtime.dumpers import yaml_dumper
from linkml_runtime.loaders import json_loader
from time import time
from unittest.mock import patch



#TODO NOW: update to use real import.yaml file. Unclear if this is the right thing to do based on how the tests are set up. 
#ie we want to test that the binning packaging works even if we have this false by default for older projects where we want to annotate and re-bin.
#TODO NEXT: add test for import-mt.yaml similar to what is in test_workflow_process.py

@fixture
def gold_mapper(mock_nmdc_runtime_api, base_test_dir, gold_import_files, gold_import_dir):
    """
    Base test function for code related to importing JGI records.
    """
    yaml_file = base_test_dir / "import_test.yaml"
    nucleotide_sequencing_id = "nmdc:omprc-11-importT"
    root_dir = f"/tmp/{nucleotide_sequencing_id}"
    if os.path.exists(root_dir):
        shutil.rmtree(root_dir)
    gm = GoldMapper("1", gold_import_files, nucleotide_sequencing_id, yaml_file, gold_import_dir, mock_nmdc_runtime_api)
    gm.root_dir = root_dir
    return gm


@lru_cache(maxsize=None)
def get_nmdc_materialized():
    with importlib.resources.open_text("nmdc_schema", "nmdc_materialized_patterns.yaml") as f:
        return yaml.safe_load(f)


def test_gold_mapper_map_sequencing_data(gold_mapper):
    """
    Test that the gold mapper creates data objects for the sequencing data, and
    provides an update to be applied to the has_output list of the sequencing data generation
    """
    exp_num_data_objects = 1    # There is only one sequencing data file from the gold import files fixture
    exp_dobj_id = "nmdc:dobj-11-abcd1234"   # From the mock API minter response
    exp_dobj_type = "Metagenome Raw Reads"  # From the gold_import_files fixture
    exp_nucleotide_sequencing_id = "nmdc:omprc-11-importT"  # From the gold mapper fixture
    exp_update = {
        "collection": "data_generation_set",
        "filter": {"id": exp_nucleotide_sequencing_id},
        "update": {"$addToSet": {"has_output": [exp_dobj_id]}}
    }
    # Sequencing data does not get a URL
    exp_url = None
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
    assert str(dobj.data_object_type) == exp_dobj_type
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
        # two unique data files from the gold import files fixture get added to the database
    exp_data_object_types = [
        "Clusters of Orthologous Groups (COG) Annotation GFF",
        "Pfam Annotation GFF",
        "Metagenome Raw Reads",
        "Annotation Amino Acid FASTA",
        "Filtered Sequencing Reads",
        "Assembly Contigs",
    ]

    exp_nucleotide_sequencing_id = "nmdc:omprc-11-importT"  # From the gold mapper fixture

    db, do_map = gold_mapper.map_data(db)
    assert db
    assert len(db.data_object_set) == len(exp_data_object_types)
    data_objects = db.data_object_set
    for dobj in data_objects:
        assert str(dobj.data_object_type) in exp_data_object_types
        assert isinstance(dobj, DataObject)
        # sequencing data object should not have a URL
        if str(dobj.data_object_type) == "Metagenome Raw Reads":
            assert not dobj.url
        else:
            assert dobj.url
            assert exp_nucleotide_sequencing_id in dobj.url
            assert exp_nucleotide_sequencing_id in dobj.description


def test_gold_mapper_map_data_multiple(gold_mapper):
    """
    Test that the mapper is able to combine multiple data files into a single data object.
    """
    initial_num_data_objects = 1
    db, update = gold_mapper.map_sequencing_data()
    # sanity check
    assert len(db.data_object_set) == initial_num_data_objects
    exp_num_data_objects = 2    # two files are combined into a single data object

    db, do_map = gold_mapper.map_data(db, unique=False)
    assert db
    assert len(db.data_object_set) == exp_num_data_objects


def test_gold_mapper_map_workflow_executions(gold_mapper, ):
    """
    Test that the gold mapper creates workflow execution records and data objects that are has_output of those workflow execution subclasses.
    """

    # setup
    db, update = gold_mapper.map_sequencing_data()
    db, do_map = gold_mapper.map_data(db)
    db, do_map = gold_mapper.map_data(db, unique=False)

    # test
    db = gold_mapper.map_workflow_executions(db)
    assert db.workflow_execution_set


    # test that the db is valid according to the schema
    nmdc_materialized = get_nmdc_materialized()
    # db is a schema object, so we need to convert it to a dictionary

    db_dict = yaml.safe_load(yaml_dumper.dumps(db))

    validation_report = linkml.validator.validate(db_dict, nmdc_materialized, "Database")

    assert not validation_report.results, f"Validation error: {validation_report.results[0].message}"









