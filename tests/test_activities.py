from pytest import mark

from nmdc_automation.workflow_automation.activities import load_activities
from nmdc_automation.workflow_automation.workflows import load_workflows
from tests.fixtures.db_utils import get_updated_fixture, load_fixture, reset_db


@mark.parametrize(
    "workflow_file", [
        "workflows.yaml",
        # "workflows-mt.yaml"
    ]
    )
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
    assert acts is not None
    if metatranscriptome:
        # seq, rqc, assembly, annotation, expression
        exp_num_acts = 5
    else:
        # seq, rqc, assembly, annotation, MAGs, read-based taxonomic annotation
        exp_num_acts = 6
    assert len(acts) == exp_num_acts
    omics = acts[0]
    assert omics.type == "nmdc:OmicsProcessing"
    assert len(omics.children) == 1
    assert omics.children[0].type.lower() == "nmdc:ReadQCAnalysisActivity".lower()

@mark.parametrize(
    "workflow_file", ["workflows.yaml", "workflows-mt.yaml"]
    )
def test_workflows(workflows_config_dir, workflow_file):
    """
    Test Workflow object creation
    """
    metatranscriptome = False
    if workflow_file == "workflows-mt.yaml":
        metatranscriptome = True

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
    assert wfs is not None
    wfm = {}
    assert len(wfs) == exp_num_wfs
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


