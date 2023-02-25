from pymongo import MongoClient
import json
import os
from src.activities import load_activities
from pytest import fixture
from src.workflows import load_workflows


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


@fixture
def db():
    return MongoClient("mongodb://admin:root@127.0.0.1:27018").test


def read_json(fn):
    fp = os.path.join(test_data, fn)
    if os.path.exists(fp):
        return json.load(open(fp))
    else:
        print(f"Missing {fn}")
        return None


def load(db, fn, col=None, reset=False):
    if not col:
        col = fn.split("/")[-1].split(".")[0]
    if reset:
        db[col].delete_many({})
    data = read_json(fn)
    if not data:
        return
    print("Loading %d recs into %s" % (len(data), col))
    if len(data) > 0:
        db[col].insert_many(data)


def reset_db(db):
    cols = db.list_collection_names()
    for c in cols:
        if c in cols:
            db[c].delete_many({})


def mock_progress(db, wf):
    s = wf.collection
    resp = read_json("%s.json" % (s))
    if not resp:
        print(f"no data for {wf.name}")
        return
    data = resp[0]
    data['git_url'] = wf.git_repo
    data['version'] = wf.version
    db[s].delete_many({})
    db[s].insert_one(data)


def test_activies(db):
    """
    Test basic job creation
    """
    # init_test(db)
    reset_db(db)
    wfs = load_workflows("workflows.yaml")
    load(db, "data_object_set.json", reset=True)
    for wf in wfs:
        mock_progress(db, wf)
    acts = load_activities(db, wfs)
    assert acts is not None
    assert len(acts) == 5
    acts_by_wf = dict()
    for act in acts:
        acts_by_wf[act.workflow] = act
        print(act.__dict__)
