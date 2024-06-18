import pytest
from nmdc_automation.re_iding.db_utils import (
    get_collection_name_from_workflow_id,
    fix_malformed_workflow_id_version,
    fix_malformed_data_object_name,
    fix_malformed_data_object_url
)

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


def test_fix_malformed_workflow_id_version():

    # Test for a workflow ID with a correct version
    workflow_id = "nmdc:wfrqc-11-zbyqeq59.1"
    fixed_workflow_id = fix_malformed_workflow_id_version(workflow_id)
    assert fixed_workflow_id == "nmdc:wfrqc-11-zbyqeq59.1"

    # Test for a workflow ID with an extra .1(s) at the end of the version
    workflow_id = "nmdc:wfrqc-11-zbyqeq59.1.1"
    assert fix_malformed_workflow_id_version(workflow_id) == "nmdc:wfrqc-11-zbyqeq59.1"

    # Test for a workflow ID with a missing version
    workflow_id = "nmdc:wfrqc-11-zbyqeq59"
    assert fix_malformed_workflow_id_version(workflow_id) == "nmdc:wfrqc-11-zbyqeq59.1"

    # Test for a workflow ID with extra .1(s) at the end of the version
    workflow_id = "nmdc:wfrqc-11-zbyqeq59.1.1.1"
    assert fix_malformed_workflow_id_version(workflow_id) == "nmdc:wfrqc-11-zbyqeq59.1"


def test_fix_malformed_data_object_name():
    expected_name = "nmdc_wfrqc-11-pbxpdr12.1_filterStats.txt"

    # test a name with extra version digits
    name = "nmdc_wfrqc-11-pbxpdr12.1.1_filterStats.txt"
    fixed_name = fix_malformed_data_object_name(name)
    assert fixed_name == expected_name

    # test a name with missing version digits
    name = "nmdc_wfrqc-11-pbxpdr12_filterStats.txt"
    fixed_name = fix_malformed_data_object_name(name)
    assert fixed_name == expected_name

    # test a name with correct version digits
    name = "nmdc_wfrqc-11-pbxpdr12.1_filterStats.txt"
    fixed_name = fix_malformed_data_object_name(name)
    assert fixed_name == expected_name


def test_fix_malformed_data_object_url():
    expected_url = "https://data.microbiomedata.org/data/nmdc:omprc-11-wmzpa354/nmdc:wfrqc-11-pbxpdr12.1/nmdc_wfrqc-11-pbxpdr12.1_filtered.fastq.gz"

    # test a url with extra version digits
    url = "https://data.microbiomedata.org/data/nmdc:omprc-11-wmzpa354/nmdc:wfrqc-11-pbxpdr12.1.1/nmdc_wfrqc-11-pbxpdr12.1.1_filtered.fastq.gz"
    fixed_url = fix_malformed_data_object_url(url)
    assert fixed_url == expected_url

    # test a url with missing version digits
    url = "https://data.microbiomedata.org/data/nmdc:omprc-11-wmzpa354/nmdc:wfrqc-11-pbxpdr12/nmdc_wfrqc-11-pbxpdr12_filtered.fastq.gz"
    fixed_url = fix_malformed_data_object_url(url)
    assert fixed_url == expected_url

    # test a url with correct version digits
    url = "https://data.microbiomedata.org/data/nmdc:omprc-11-wmzpa354/nmdc:wfrqc-11-pbxpdr12.1/nmdc_wfrqc-11-pbxpdr12.1_filtered.fastq.gz"
    fixed_url = fix_malformed_data_object_url(url)