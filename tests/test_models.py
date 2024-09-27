""" Test cases for the models module. """
from bson import ObjectId
from pytest import mark
from nmdc_automation.workflow_automation.models import(
    DataObject,
    Job,
    JobClaim,
    JobConfig,
    JobOutput,
    JobWorkflow,
    WorkflowProcessNode,
    workflow_process_factory,
)
from nmdc_automation.workflow_automation.workflows import load_workflow_configs
from tests.fixtures import db_utils

def test_workflow_process_factory():
    """ Test the workflow_process_factory function. """
    record_types = {
        "nmdc:MagsAnalysis": "mags_record.json",
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
        record = db_utils.read_json(record_file)
        wfe = workflow_process_factory(record)
        assert wfe.type == record_type


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
    ("mags_record.json", "nmdc:MagsAnalysis"),
    ("metagenome_annotation_record.json", "nmdc:MetagenomeAnnotation"),
    ("metagenome_assembly_record.json", "nmdc:MetagenomeAssembly"),
    ("metatranscriptome_annotation_record.json", "nmdc:MetatranscriptomeAnnotation"),
    ("metatranscriptome_assembly_record.json", "nmdc:MetatranscriptomeAssembly"),
    ("metatranscriptome_expression_analysis_record.json", "nmdc:MetatranscriptomeExpressionAnalysis"),
    ("nucleotide_sequencing_record.json", "nmdc:NucleotideSequencing"),
    ("read_based_taxonomy_analysis_record.json", "nmdc:ReadBasedTaxonomyAnalysis"),
    ("read_qc_analysis_record.json", "nmdc:ReadQcAnalysis"),
])
def test_workflow_process_node(workflows_config_dir,record_file, record_type):
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

    record = db_utils.read_json(record_file)

    wfn = WorkflowProcessNode(record, wf)
    assert wfn.process.type == record_type


def test_data_object_creation_from_records():
    """ Test the creation of DataObject objects from records. """
    records = db_utils.read_json("data_object_set.json")
    for record in records:
        data_obj = DataObject(**record)
        assert data_obj.type == "nmdc:DataObject"
        assert data_obj.id == record["id"]
        assert data_obj.name == record["name"]
        assert data_obj.data_object_type == record["data_object_type"]

        data_obj_dict = data_obj.as_dict()
        assert data_obj_dict == record

def test_data_object_creation_from_db_records(test_db):
    db_utils.reset_db(test_db)
    db_utils.read_json("data_object_set.json")

    db_records = test_db["data_object_set"].find()
    db_records = list(db_records)
    for db_record in db_records:
        data_obj = DataObject(**db_record)
        assert data_obj.type == "nmdc:DataObject"
        assert data_obj.id == db_record["id"]
        assert data_obj.name == db_record["name"]
        assert data_obj.data_object_type == db_record["data_object_type"]
        assert data_obj.data_object_format == db_record["data_object_format"]

        data_obj_dict = data_obj.as_dict()
        assert data_obj_dict == db_record


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

def test_job_creation():
    job_record = db_utils.read_json("job_record.json")
    job = Job(**job_record)
    assert job.id == job_record["id"]
    assert isinstance(job.workflow, JobWorkflow)