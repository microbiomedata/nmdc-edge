""" Test cases for the models module. """
import json
import pytest
from bson import ObjectId
from pathlib import Path
from pytest import mark, raises
from nmdc_automation.models.nmdc import DataObject, workflow_process_factory
from nmdc_automation.models.workflow import Job, JobOutput, JobWorkflow, WorkflowProcessNode
from nmdc_automation.workflow_automation.workflows import load_workflow_configs
from tests.fixtures import db_utils

from linkml_runtime.dumpers import yaml_dumper
import yaml


def test_workflow_process_factory(fixtures_dir):
    """ Test the workflow_process_factory function. """
    record_types = {
        "nmdc:MagsAnalysis": "mags_analysis_record.json",
        "nmdc:MetagenomeAnnotation": "metagenome_annotation_record.json",
        "nmdc:MetagenomeAssembly": "metagenome_assembly_record.json",
        "nmdc:MetatranscriptomeAnnotation": "metatranscriptome_annotation_record.json",
        "nmdc:MetatranscriptomeAssembly": "metatranscriptome_assembly_record.json",
        "nmdc:MetatranscriptomeExpressionAnalysis": "metatranscriptome_expression_analysis_record.json",
        "nmdc:NucleotideSequencing": "nucleotide_sequencing_record.json",
        "nmdc:ReadBasedTaxonomyAnalysis": "read_based_taxonomy_analysis_record.json",
        "nmdc:ReadQcAnalysis": "read_qc_analysis_record.json",
    }
    for record_type, record_file in record_types.items():
        record = json.load(open(fixtures_dir / f"models/{record_file}"))
        wfe = workflow_process_factory(record)
        assert wfe.type == record_type


def test_workflow_process_factory_incorrect_id(fixtures_dir):
    record = json.load(open(fixtures_dir / "models/metagenome_annotation_record.json"))
    # Change the id to an incorrect value - this would be an assembly id
    record["id"] = "nmdc:wfmgas-11-009f3582.1"
    with pytest.raises(ValueError) as excinfo:
        workflow_process_factory(record, validate=True)
    assert "'nmdc:wfmgas-11-009f3582.1' does not match" in str(excinfo.value)





def test_workflow_process_factory_data_generation_invalid_analyte_category(fixtures_dir):
    record = json.load(open(fixtures_dir / "models/nucleotide_sequencing_record.json"))
    record["analyte_category"] = "Something Invalid"

    with raises(ValueError) as excinfo:
        wfe = workflow_process_factory(record)



def test_workflow_process_factory_metagenome_assembly_with_invalid_execution_resource(fixtures_dir):
    record = json.load(open(fixtures_dir / "models/metagenome_assembly_record.json"))
    record["execution_resource"] = "Something Invalid"
    with raises(ValueError) as excinfo:
        wfe = workflow_process_factory(record)


def test_workflow_process_factory_mags_with_mags_list(fixtures_dir):
    record = json.load(open(fixtures_dir / "models/mags_analysis_record.json"))
    mga = workflow_process_factory(record)
    assert mga.type == "nmdc:MagsAnalysis"


def test_process_factory_with_db_record():
    record = {'_id': ObjectId('66f4d5f10de8ad0b72100069'), 'id': 'nmdc:omprc-11-metag1',
              'name': 'Test Metagenome Processing', 'has_input': ['nmdc:bsm-11-qezc0h51'],
              'has_output': ['nmdc:dobj-11-rawreads1', 'nmdc:dobj-11-rawreads2'], 'analyte_category': 'metagenome',
              'associated_studies': ['nmdc:sty-11-test001'], "processing_institution": "JGI",
              'principal_investigator': {'has_raw_value': 'PI Name', 'email': 'pi_name@example.com',
                                         'name': 'PI Name', "type": "nmdc:PersonValue"},
              'type': 'nmdc:NucleotideSequencing'}
    wfe = workflow_process_factory(record)
    assert wfe.type == "nmdc:NucleotideSequencing"


@mark.parametrize("record_file, record_type", [
    ("mags_analysis_record.json", "nmdc:MagsAnalysis"),
    ("metagenome_annotation_record.json", "nmdc:MetagenomeAnnotation"),
    ("metagenome_assembly_record.json", "nmdc:MetagenomeAssembly"),
    ("metatranscriptome_annotation_record.json", "nmdc:MetatranscriptomeAnnotation"),
    ("metatranscriptome_assembly_record.json", "nmdc:MetatranscriptomeAssembly"),
    ("metatranscriptome_expression_analysis_record.json", "nmdc:MetatranscriptomeExpressionAnalysis"),
    ("nucleotide_sequencing_record.json", "nmdc:NucleotideSequencing"),
    ("read_based_taxonomy_analysis_record.json", "nmdc:ReadBasedTaxonomyAnalysis"),
    ("read_qc_analysis_record.json", "nmdc:ReadQcAnalysis"),
])
def test_workflow_process_node(workflows_config_dir,record_file, record_type, fixtures_dir):
    """ Test the WorkflowProcessNode class. """
    # load all workflows for both metagenome and metatranscriptome
    wfs = load_workflow_configs(workflows_config_dir / "workflows.yaml")
    wfs += load_workflow_configs(workflows_config_dir / "workflows-mt.yaml")

    # NuclotideSequencing workflows have no type
    if record_type == "nmdc:NucleotideSequencing":
        wfs_for_type = [wf for wf in wfs if wf.collection == "data_generation_set"]
    else:
        wfs_for_type = [wf for wf in wfs if wf.type == record_type]
    assert wfs_for_type
    wf = wfs_for_type[0]

    record = json.load(open(fixtures_dir / f"models/{record_file}"))

    wfn = WorkflowProcessNode(record, wf)
    assert wfn.process.type == record_type


def test_data_object_creation_from_records(fixtures_dir):
    """ Test the creation of DataObject objects from records. """
    records_path = fixtures_dir / Path('nmdc_db/data_object_set.json')
    records = json.load(open(records_path))
    for record in records:
        data_obj = DataObject(**record)
        assert data_obj.type == "nmdc:DataObject"
        assert data_obj.id == record["id"]
        assert data_obj.name == record["name"]
        # not all data objects have a data_object_type - e.g. Mass Spectrometry data
        if "data_object_type" in record:
            assert str(data_obj.data_object_type) == record["data_object_type"]

        data_obj_dict = yaml.safe_load(yaml_dumper.dumps(data_obj))
        assert data_obj_dict == record


def test_data_object_creation_from_db_records(test_db, fixtures_dir):
    db_utils.reset_db(test_db)
    db_utils.load_fixture(test_db, "data_object_set.json")

    db_records = test_db["data_object_set"].find()
    db_records = list(db_records)
    assert db_records
    for db_record in db_records:
        data_obj = DataObject(**db_record)
        assert data_obj.type == "nmdc:DataObject"
        assert data_obj.id == db_record["id"]
        assert data_obj.name == db_record["name"]
        # not all data objects have a data_object_type or url - e.g. Mass Spectrometry data
        if not db_record.get("data_object_type"):
            continue
        assert str(data_obj.data_object_type) == db_record["data_object_type"]
        assert data_obj.url == db_record["url"]
        assert data_obj.description == db_record["description"]
        assert data_obj.file_size_bytes == db_record.get("file_size_bytes")
        assert data_obj.md5_checksum == db_record["md5_checksum"]

        data_obj_dict = data_obj.as_dict()
        # The db record will have an _id field that is not in the data object
        _id = db_record.pop("_id")
        assert _id
        assert data_obj_dict == db_record


def test_data_object_creation_invalid_data_object_type():
    record = {
        "id": "nmdc:dobj-11-rawreads1",
        "name": "metaG_R1_001.fastq.gz",
        "description": "Sequencing results for metaG_R1",
        "md5_checksum": "ed9467e690babb683b024ed47dd97b85",
        "data_object_type": "Something Invalid",
        "type": "nmdc:DataObject",
        "url": "https://portal.nersc.gov"
    }
    with raises(ValueError) as excinfo:
        data_obj = DataObject(**record)

    # Test with a valid data object type
    record.update({"data_object_type": "Metagenome Raw Reads"})
    data_obj = DataObject(**record)
    assert str(data_obj.data_object_type) == "Metagenome Raw Reads"


def test_data_object_creation_invalid_data_category():
    record = {
        "id": "nmdc:dobj-11-qcstats",
        "name": "nmdc_wfrqc-11-metag.1_filterStats.txt",
        "description": "Reads QC summary for nmdc:wfrqc-11-metag1.1",
        "file_size_bytes": 123456,
        "md5_checksum": "7172cd332a734e002c88b35827acd991",
        "data_object_type": "QC Statistics",
        "data_category": "Something Invalid",
        "url": "https://data.microbiomedata.org",
        "type": "nmdc:DataObject"
    }
    with raises(ValueError) as excinfo:
        data_obj = DataObject(**record)

def test_job_output_creation():
    outputs = [
        {
            "output": "proteins_faa",
            "data_object_type": "Annotation Amino Acid FASTA",
            "description": "FASTA Amino Acid File for {id}",
            "name": "FASTA amino acid file for annotated proteins",
            "id": "nmdc:dobj-11-tt8ykk73"
        },
        {
            "output": "structural_gff",
            "data_object_type": "Structural Annotation GFF",
            "description": "Structural Annotation for {id}",
            "name": "GFF3 format file with structural annotations",
            "id": "nmdc:dobj-11-xh82sm39"
        }
    ]
    for output in outputs:
        job_output = JobOutput(**output)


def test_job_creation(fixtures_dir):
    job_record = json.load(open(fixtures_dir / "nmdc_api/unsubmitted_job.json"))
    job = Job(**job_record)
    assert job.id == job_record["id"]
    assert isinstance(job.workflow, JobWorkflow)
