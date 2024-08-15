from pymongo import MongoClient
import json
import os
from nmdc_automation.workflow_automation.activities import load_activities
from pytest import fixture
from nmdc_automation.workflow_automation.workflows import load_workflows


test_dir = os.path.dirname(__file__)
test_data = os.path.join(test_dir, "..", "test_data")
cols = [
    'data_object_set',
    'metagenome_sequencing_activity_set',
    'mags_activity_set',
    'metagenome_assembly_set',
    'metagenome_annotation_activity_set',
    'read_qc_analysis_activity_set'
    ]

def read_json(fn):
    fp = os.path.join(test_data, fn)
    if os.path.exists(fp):
        return json.load(open(fp))
    else:
        print(f"\nWarning: Missing {fn}")
        return None


def load(test_db, fn, col=None, reset=False):
    if not col:
        col = fn.split("/")[-1].split(".")[0]
    if reset:
        test_db[col].delete_many({})
    data = read_json(fn)
    if not data:
        return
    if len(data) > 0:
        test_db[col].insert_many(data)


def reset_test_db(test_db):
    cols = test_db.list_collection_names()
    for c in cols:
        if c in cols:
            test_db[c].delete_many({})


def fix_versions(test_db, wf):
    s = wf.collection
    resp = read_json("%s.json" % (s))
    if not resp:
        print(f"no data for {wf.name}")
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
    reset_test_db(test_db)
    wfs = load_workflows("./tests/workflows_test.yaml")
    load(test_db, "data_object_set.json", reset=True)
    for wf in wfs:
        if wf.name in ["Sequencing", "ReadsQC Interleave"]:
            continue
        fix_versions(test_db, wf)
    acts = load_activities(test_db, wfs)
    assert acts is not None
    # TODO find out why this fails - len(acts) = 4
    # assert len(acts) == 5
    # assert len(acts[0].children) == 1
    # assert acts[0].children[0] == acts[1]

def test_workflows():
    """
    Test Workflow object creation
    """
    wfs = load_workflows("./tests/workflows_test.yaml")
    assert wfs is not None
    wfm = {}
    assert len(wfs) == 9
    for wf in wfs:
        wfm[wf.name] = wf
    assert "MAGs" in wfm
    assert len(wfm["MAGs"].optional_inputs) == 1