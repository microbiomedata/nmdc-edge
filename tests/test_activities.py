import json

from pytest import mark

from nmdc_automation.workflow_automation.activities import load_activities
from nmdc_automation.workflow_automation.workflows import load_workflows
from tests.fixtures.db_utils import load_fixture, reset_db


def fix_versions(test_db, wf, fixtures_dir):
    s = wf.collection
    # resp = read_json("%s.json" % (s))
    fixture_file = f"{s}.json"
    try:
        with open(fixtures_dir / fixture_file) as f:
            resp = json.load(f)
    except FileNotFoundError:
        return

    data = resp[0]
    data['git_url'] = wf.git_repo
    data['version'] = wf.version
    test_db[s].delete_many({})
    test_db[s].insert_one(data)


def get_updated_fixture(wf, fixtures_dir):
    """
    Read the fixture file and update the version and git_url for the
    fixtures that of the same workflow type.
    """
    updated_fixtures = []
    fixture_file = f"{wf.collection}.json"
    try:
        with open(fixtures_dir / fixture_file) as f:
            fixtures = json.load(f)
    except FileNotFoundError as e:
        return []
    for fix in fixtures:
        if fix['type'].lower() != wf.type.lower():
            continue
        fix['git_url'] = wf.git_repo
        fix['version'] = wf.version
        updated_fixtures.append(fix)
    return updated_fixtures


@mark.parametrize(
    "workflow_file", ["workflows.yaml", "workflows-mt.yaml"]
    )
def test_activies(test_db, workflow_file, config_dir, fixtures_dir):
    """
    Test basic job creation
    """
    metatranscriptome = False
    if workflow_file == "workflows-mt.yaml":
        metatranscriptome = True

    reset_db(test_db)
    load_fixture(test_db, "data_object_set.json")
    if metatranscriptome:
        load_fixture(test_db, "omics_processing_set_mt.json", col="omics_processing_set")
    else:
        load_fixture(test_db, "omics_processing_set.json")

    wfs = load_workflows(config_dir / workflow_file)
    for wf in wfs:
        if not wf.type:
            continue
        # TODO: these tests are very sensitive to the exact content of the fixture files - need to be more robust
        updated_fixtures = get_updated_fixture(wf, fixtures_dir)
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


def test_workflows(config_dir):
    """
    Test Workflow object creation
    """
    wfs = load_workflows(config_dir / "workflows.yaml")
    assert wfs is not None
    wfm = {}
    assert len(wfs) == 8
    for wf in wfs:
        wfm[wf.name] = wf
    assert "MAGs" in wfm
