from pytest import mark

from nmdc_automation.workflow_automation.workflow_process import (
    get_required_data_objects_map,
    get_current_workflow_process_nodes,
    load_workflow_process_nodes,
    _resolve_relationships,
    _map_nodes_to_data_objects,
    _within_range
)
from nmdc_automation.workflow_automation.workflows import load_workflow_configs
from tests.fixtures.db_utils import  load_fixture, reset_db


@mark.parametrize(
    "workflow_file", ["workflows.yaml", "workflows-mt.yaml"]
)
def test_load_workflow_process_nodes(test_db, workflow_file, workflows_config_dir):
    """
    Test loading workflow process nodes from the database.
    """
    metatranscriptome = False
    if workflow_file == "workflows-mt.yaml":
        metatranscriptome = True

    reset_db(test_db)
    load_fixture(test_db, "data_object_set.json")
    load_fixture(test_db, "data_generation_set.json")
    load_fixture(test_db, "read_qc_analysis.json", "workflow_execution_set")

    workflow_configs = load_workflow_configs(workflows_config_dir / workflow_file)

   # sanity checking these - they are used in the next step
    data_objs_by_id = get_required_data_objects_map(test_db, workflow_configs)
    current_nodes = get_current_workflow_process_nodes(test_db, workflow_configs, data_objs_by_id)
    assert current_nodes
    assert len(current_nodes) == 2

    workflow_process_nodes = load_workflow_process_nodes(test_db, workflow_configs)
    # sanity check
    assert workflow_process_nodes
    assert len(workflow_process_nodes) == 2

    # Omics and RQC share data_object_type for metagenome and metatranscriptome
    # they can be distinguished by analyte category so we expect 1 of each
    # for metagenome and metatranscriptome
    data_generation_nodes = [node for node in workflow_process_nodes if node.type == "nmdc:NucleotideSequencing"][0]
    assert data_generation_nodes
    assert data_generation_nodes.children
    assert len(data_generation_nodes.children) == 1
    assert data_generation_nodes.children[0].type == "nmdc:ReadQcAnalysis"



def test_get_required_data_objects_map(test_db, workflows_config_dir):
    """
    Test get_required_data_objects_map
    """
    reset_db(test_db)
    load_fixture(test_db, "data_object_set.json")
    load_fixture(test_db, "lipidomics_data_objects.json")

    workflow_config = load_workflow_configs(workflows_config_dir / "workflows.yaml")
    required_data_object_map = get_required_data_objects_map(test_db, workflow_config)
    assert required_data_object_map
    for do in required_data_object_map.values():
        assert do.data_object_type
        assert do.data_object_type.code.text



def test_load_workflow_process_nodes_with_obsolete_versions(test_db, workflows_config_dir):
    """
    Test loading workflow process nodes for a case where there are obsolete versions of the same workflow
    """
    reset_db(test_db)
    load_fixture(test_db, "data_objects_2.json", "data_object_set")
    load_fixture(test_db, "data_generation_2.json", "data_generation_set")
    load_fixture(test_db, "workflow_execution_2.json", "workflow_execution_set")

    workflow_config = load_workflow_configs(workflows_config_dir / "workflows.yaml")
    data_objs_by_id = get_required_data_objects_map(test_db, workflow_config)

    # There are 8 workflow executions in the fixture, but only 4 are current:
    # 2 are obsolete  MAGs workflows,
    # 1 is an obsolete Annotation workflow, and 1 is a legacy MetagenomeSequencing workflow
    exp_num_db_workflow_execution_records = 8
    exp_num_current_nodes = 5 # 4 current workflows and 1 data generation
    exp_current_node_types = [
        "nmdc:MetagenomeAssembly", "nmdc:MetagenomeAnnotation", "nmdc:ReadQcAnalysis",
        "nmdc:NucleotideSequencing", "nmdc:ReadBasedTaxonomyAnalysis"]

    # Check that the workflow executions were loaded
    records = test_db["workflow_execution_set"].find()
    assert records
    records = list(records)
    assert len(records) == exp_num_db_workflow_execution_records

    # testing functions that are called by load_workflow_process_nodes
    # get_current_workflow_process_nodes
    current_nodes = get_current_workflow_process_nodes(test_db, workflow_config, data_objs_by_id)
    assert current_nodes
    assert len(current_nodes) == exp_num_current_nodes
    current_node_types = [node.type for node in current_nodes]
    assert sorted(current_node_types) == sorted(exp_current_node_types)

    # _map_nodes_to_data_objects
    node_dobj_map, current_nodes = _map_nodes_to_data_objects(current_nodes, data_objs_by_id)
    for node in current_nodes:
        # check that the data objects are mapped to the nodes - read-based taxonomy analysis has no data objects
        if node.type != "nmdc:ReadBasedTaxonomyAnalysis":
            assert node.data_objects_by_type
        # parent / children are not set
        assert node.parent is None
        assert not node.children

    # _resolve_relationships
    resolved_nodes = _resolve_relationships(current_nodes, node_dobj_map)
    for node in resolved_nodes:
        if node.type == "nmdc:NucleotideSequencing":
            assert node.children
        else:
            assert node.parent
    assert resolved_nodes


def test_resolve_relationships(test_db, workflows_config_dir):
    """
    Test that the relationships between workflow process nodes are resolved
    """
    allow_list = ["nmdc:omprc-11-metag1",]
    reset_db(test_db)
    load_fixture(test_db, "data_object_set.json")
    load_fixture(test_db, "data_generation_set.json")
    load_fixture(test_db, "read_qc_analysis.json", "workflow_execution_set")
    load_fixture(test_db, "metagenome_assembly.json", "workflow_execution_set")
    load_fixture(test_db, "metagenome_annotation.json", "workflow_execution_set")

    workflow_config = load_workflow_configs(workflows_config_dir / "workflows.yaml")
    data_objs_by_id = get_required_data_objects_map(test_db, workflow_config)
    current_nodes = get_current_workflow_process_nodes(test_db, workflow_config, data_objs_by_id)
    current_nodes_by_data_object_id, current_nodes = _map_nodes_to_data_objects(
        current_nodes, data_objs_by_id)
    assert current_nodes
    assert current_nodes_by_data_object_id
    for node in current_nodes:
        assert node.data_objects_by_type
        assert node.parent is None
        assert not node.children

    workflow_process_graph = _resolve_relationships(current_nodes, current_nodes_by_data_object_id)
    assert workflow_process_graph

    for node in workflow_process_graph:
        if node.type == 'nmdc:NucleotideSequencing':
            assert node.children
        else:
            assert node.parent


def test_load_workflow_process_nodes_does_not_load_metagenome_sequencing(test_db, workflows_config_dir):
    """
    Test that legacy nmdc:MetagenomeSequencing instances are not loaded
    """
    exp_omprc = "nmdc:omprc-11-cegmwy02"
    reset_db(test_db)
    load_fixture(test_db, "legacy_data_obj.json", "data_object_set")
    load_fixture(test_db, "legacy_data_generation.json", "data_generation_set")
    load_fixture(test_db, "metagenome_sequencing.json", "workflow_execution_set")

    workflow_config = load_workflow_configs(workflows_config_dir / "workflows.yaml")
    data_objs_by_id = get_required_data_objects_map(test_db, workflow_config)
    wf_execs = get_current_workflow_process_nodes(test_db, workflow_config, data_objs_by_id, allowlist=[exp_omprc,])
    # We only expect the data generation to be loaded
    assert wf_execs
    assert len(wf_execs) == 1
    wf = wf_execs[0]
    assert wf.type == "nmdc:NucleotideSequencing"
    assert wf.id == exp_omprc
    assert wf.was_informed_by == exp_omprc


@mark.parametrize(
    "workflow_file", ["workflows.yaml", "workflows-mt.yaml"]
)
def test_load_workflows(workflows_config_dir, workflow_file):
    """
    Test Workflow object creation
    """
    metatranscriptome = False
    if workflow_file == "workflows-mt.yaml":
        metatranscriptome = True

    shared_wf_names = ["Sequencing Noninterleaved", "Sequencing Interleaved"]
    if metatranscriptome:
        exp_num_workflow_config = 9
        exp_wf_names = ["Metatranscriptome Reads QC", "Metatranscriptome Reads QC Interleave",
                        "Metatranscriptome Assembly", "Metatranscriptome Annotation", "Expression Analysis Antisense",
                        "Expression Analysis Sense", "Expression Analysis Nonstranded", ]
    else:
        exp_num_workflow_config = 8
        exp_wf_names = ["Reads QC", "Reads QC Interleave", "Metagenome Assembly", "Metagenome Annotation", "MAGs",
                        "Readbased Analysis", ]

    workflow_config = load_workflow_configs(workflows_config_dir / workflow_file)
    assert workflow_config
    wfm = {}
    assert len(workflow_config) == len(exp_wf_names) + len(shared_wf_names)
    for wf in workflow_config:
        wfm[wf.name] = wf
    for wf_name in exp_wf_names:
        assert wf_name in wfm
        wf = wfm[wf_name]
        assert wf is not None
        assert wf.type is not None
        assert wf.name is not None
        assert wf.collection is not None
        assert wf.git_repo is not None
        assert wf.version is not None
        assert wf.analyte_category is not None


@mark.parametrize(
    "workflow_file", ["workflows.yaml", "workflows-mt.yaml"]
)
def test_get_required_data_objects_by_id(test_db, workflows_config_dir, workflow_file):
    """
    Test get_required_data_objects_by_id
    """
    # non-comprehensive list of expected data object types
    exp_do_types = ["Metagenome Raw Read 1", "Metagenome Raw Read 2", "Filtered Sequencing Reads"]
    # TODO: add workflow specific data objects
    reset_db(test_db)
    load_fixture(test_db, "data_object_set.json")

    workflow_config = load_workflow_configs(workflows_config_dir / workflow_file)

    required_data_object_map = get_required_data_objects_map(test_db, workflow_config)
    assert required_data_object_map
    # get a unique list of the data object types
    do_types = set()
    for do in required_data_object_map.values():
        do_types.add(do.data_object_type.code.text)
    # check that the expected data object types are present
    for do_type in exp_do_types:
        assert do_type in do_types

def test_within_range():
    assert _within_range('v1.0.8', 'v1.0.8')
    assert _within_range('v1.0.8', 'v1.0.9')