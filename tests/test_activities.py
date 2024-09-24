from pytest import mark

from nmdc_automation.workflow_automation.activities import (
    load_activities,
    get_required_data_objects_map
)
from nmdc_automation.workflow_automation.workflows import load_workflows
from tests.fixtures.db_utils import get_updated_fixture, load_fixture, reset_db



@mark.parametrize(
    "workflow_file", [
        "workflows.yaml",
        "workflows-mt.yaml"])
def test_activies(test_db, workflow_file, workflows_config_dir):
    """
    Test basic job creation
    """
    metatranscriptome = False
    if workflow_file == "workflows-mt.yaml":
        metatranscriptome = True

    reset_db(test_db)
    load_fixture(test_db, "data_object_set.json")
    load_fixture(test_db, "omics_processing_set.json")
    load_fixture(test_db, "read_qc_analysis_activity_set.json")

    wfs = load_workflows(workflows_config_dir / workflow_file)
    for wf in wfs:
        if not wf.type:
            continue
        # TODO: these tests are very sensitive to the exact content of the fixture files - need to be more robust
        updated_fixtures = get_updated_fixture(wf)
        if updated_fixtures:
            test_db[wf.collection].delete_many({})
            test_db[wf.collection].insert_many(updated_fixtures)

    acts = load_activities(test_db, wfs)
    # sanity check
    assert acts

    # Omics and RQC share data_object_type for metagenome and metatranscriptome
    # they can be distinguished by analyte category so we expect 1 of each
    # for metagenome and metatranscriptome
    omics = acts[0]
    assert omics.type == "nmdc:OmicsProcessing"
    assert len(omics.children) == 1
    assert omics.children[0].type.lower() == "nmdc:ReadQCAnalysisActivity".lower()
    rqc = acts[1]
    assert rqc.type == "nmdc:ReadQcAnalysisActivity"

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
        exp_num_wfs = 9
        exp_wf_names = ["Metatranscriptome Reads QC",
                                      "Metatranscriptome Reads QC Interleave",
                                      "Metatranscriptome Assembly",
                                      "Metatranscriptome Annotation",
                                      "Expression Analysis Antisense",
                                      "Expression Analysis Sense",
                                      "Expression Analysis Nonstranded",
                                      ]
    else:
        exp_num_wfs = 8
        exp_wf_names = ["Reads QC", "Reads QC Interleave", "Metagenome Assembly",
                        "Metagenome Annotation", "MAGs", "Readbased Analysis", ]


    wfs = load_workflows(workflows_config_dir / workflow_file)
    assert wfs
    wfm = {}
    assert len(wfs) == len(exp_wf_names) + len(shared_wf_names)
    for wf in wfs:
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
    "workflow_file", [
        "workflows.yaml",
        "workflows-mt.yaml"
    ]
    )
def test_get_required_data_objects_by_id(test_db, workflows_config_dir, workflow_file):
    """
    Test get_required_data_objects_by_id
    """
    metatranscriptome = False
    if workflow_file == "workflows-mt.yaml":
        metatranscriptome = True

    # non-comprehensive list of expected data object types
    exp_do_types = [
        "Metagenome Raw Read 1", "Metagenome Raw Read 2", "Filtered Sequencing Reads"
    ]
    # TODO: add workflow specific data objects

    reset_db(test_db)
    load_fixture(test_db, "data_object_set.json")

    wfs = load_workflows(workflows_config_dir / workflow_file)

    required_data_object_map = get_required_data_objects_map(test_db, wfs)
    assert required_data_object_map
    # get a unique list of the data object types
    do_types = set()
    for do in required_data_object_map.values():
        do_types.add(do.data_object_type)
    # check that the expected data object types are present
    for do_type in exp_do_types:
        assert do_type in do_types
