import pytest
from nmdc_automation.re_iding.db_utils import get_collection_name_from_workflow_id

def test_get_collection_name_from_workflow_id():
    # Test for a known workflow ID
    workflow_id = "nmdc:wfrqc-11-zbyqeq59.1"
    assert get_collection_name_from_workflow_id(workflow_id) == "read_qc_analysis_activity_set"

    # Test for an unknown workflow ID
    workflow_id = "nmdc:unknown-11-zbyqeq59.1"
    assert get_collection_name_from_workflow_id(workflow_id) == "unknown"

    # Test for a known workflow ID
    workflow_id = "nmdc:wfmag-11-zbyqeq59.1"
    assert get_collection_name_from_workflow_id(workflow_id) == "mags_activity_set"

    # Test for a known workflow ID
    workflow_id = "nmdc:wfmb-11-zbyqeq59.1"
    assert get_collection_name_from_workflow_id(workflow_id) == "metabolomics_analysis_activity_set"

    # Test for a known workflow ID
    workflow_id = "nmdc:wfmgan-11-zbyqeq59.1"
    assert get_collection_name_from_workflow_id(workflow_id) == "metagenome_annotation_activity_set"

    # Test for a known workflow ID
    workflow_id = "nmdc:wfmgas-11-zbyqeq59.1"
    assert get_collection_name_from_workflow_id(workflow_id) == "metagenome_assembly_set"

    # Test for a known workflow ID
    workflow_id = "nmdc:wfrbt-11-zbyqeq59.1"
    assert get_collection_name_from_workflow_id(workflow_id) == "read_based_taxonomy_analysis_activity_set"
    