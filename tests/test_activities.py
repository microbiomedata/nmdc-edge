import json
from pathlib import Path
from nmdc_automation.workflow_automation.activities import load_activities
from nmdc_automation.workflow_automation.workflows import load_workflows
from tests.fixtures.db_utils import load, read_json, reset_db


TEST_DIR = Path(__file__).parent
FIXTURE_DIR = TEST_DIR / "fixtures"
CONFIG_DIR = TEST_DIR.parent / "configs"


def fix_versions(test_db, wf):
    s = wf.collection
    # resp = read_json("%s.json" % (s))
    fixture_file = f"{s}.json"
    try:
        with open(FIXTURE_DIR / fixture_file) as f:
            resp = json.load(f)
    except FileNotFoundError:
        return

    data = resp[0]
    data['git_url'] = wf.git_repo
    data['version'] = wf.version
    test_db[s].delete_many({})
    test_db[s].insert_one(data)


def test_activies(test_db):
    """
    Test basic job creation
    """
    # init_test(db)
    reset_db(test_db)
    wfs = load_workflows(CONFIG_DIR / "workflows.yaml")
    load(test_db, "data_object_set.json", reset=True)
    for wf in wfs:
        if wf.name in ["Sequencing", "ReadsQC Interleave"]:
            continue
        fix_versions(test_db, wf)
    acts = load_activities(test_db, wfs)
    assert acts is not None
    # TODO find out why this fails - len(acts) = 4
    assert len(acts) == 5
    assert len(acts[0].children) == 1
    assert acts[0].children[0] == acts[1]

def test_workflows():
    """
    Test Workflow object creation
    """
    wfs = load_workflows(CONFIG_DIR / "workflows.yaml")
    assert wfs is not None
    wfm = {}
    assert len(wfs) == 8
    for wf in wfs:
        wfm[wf.name] = wf
    assert "MAGs" in wfm
