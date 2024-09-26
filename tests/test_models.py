""" Test cases for the models module. """
from pytest import mark
from nmdc_automation.workflow_automation.models import(
    WorkflowExecutionNode,
    workflow_execution_factory
)
from tests.fixtures import db_utils

def test_workflow_execution_factory():
    """ Test the workflow_execution_factory function. """
    record_types = {
        "nmdc:MagsAnalysis": "mags_record.json",
        "nmdc:MetagenomeAnnotation": "metagenome_annotation_record.json",
        "nmdc:MetagenomeAssembly": "metagenome_assembly_record.json",
        "nmdc:MetatranscriptomeAnnotation": "metatranscriptome_annotation_record.json",
        "nmdc:MetatranscriptomeAssembly": "metatranscriptome_assembly_record.json",
        "nmdc:MetatranscriptomeExpressionAnalysis": "metatranscriptome_expression_analysis_record.json",
        "nmdc:ReadBasedTaxonomyAnalysis": "read_based_taxonomy_analysis_record.json",
        "nmdc:ReadQcAnalysis": "read_qc_analysis_record.json",
    }
    for record_type, record_file in record_types.items():
        record = db_utils.read_json(record_file)
        wfe = workflow_execution_factory(record)
        assert wfe.type == record_type