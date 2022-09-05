from pymongo import MongoClient
import json
import os
from src.job_finder import JobMaker
from pytest import fixture


test_dir = os.path.dirname(__file__)
test_data = os.path.join(test_dir, "..", "test_data")
trigger_set = 'metagenome_annotation_activity_set'
trigger_id = 'nmdc:55a79b5dd58771e28686665e3c3faa0c'
trigger_doid = 'nmdc:1d87115c442a1f83190ae47c7fe4011f'


@fixture
def db():
    return MongoClient("mongodb://127.0.0.1:55000").test


def read_json(fn):
    fp = os.path.join(test_data, fn)
    data = json.load(open(fp))
    return data


def load(db, fn, col=None, reset=False):
    if not col:
        col = fn.split("/")[-1].split(".")[0]
    if reset:
        db[col].delete_many({})
    data = read_json(fn)
    print("Loading %d recs into %s" % (len(data), col))
    if len(data) > 0:
        db[col].insert_many(data)


def reset_db(db):
    cols = [
        'data_object_set',
        'mags_activity_set',
        'metagenome_assembly_set',
        'jobs',
        'metagenome_annotation_activity_set'
        'read_QC_analysis_activity_set'
        ]
    for c in cols:
        db[c].delete_many({})


def init_test(db):
    for fn in os.listdir(test_data):
        load(db, fn, reset=True)


def mock_progress(db, wf):
    s = wf['Activity']
    data = read_json("%s.json" % (s))[0]
    data['git_repo'] = wf['Git_repo']
    data['version'] = wf['Version']
    db[s].delete_many({})
    db[s].insert_one(data)


def test_submit(db):
    """
    Test basic job creation
    """
    init_test(db)
    reset_db(db)
    load(db, "data_object_set.json")

    jm = JobMaker(db="test")

    # This should result in one RQC job
    resp = jm.cycle()
    assert len(resp) == 1

    # The job should now be in a submitted state
    # make this pass
    resp = jm.cycle()
    assert len(resp) == 0


def test_progress(db):
    init_test(db)
    jm = JobMaker(db="test")

    # This should result in one RQC job
    resp = jm.cycle()
    assert len(resp) == 1

    wf = jm.workflow_by_name['Reads QC']
    mock_progress(db, wf)
    resp = jm.cycle()
    assert len(resp) == 2
    resp = jm.cycle()
    assert len(resp) == 0

    wf = jm.workflow_by_name['Metagenome Assembly']
    mock_progress(db, wf)
    resp = jm.cycle()
    assert len(resp) == 1

    wf = jm.workflow_by_name['Metagenome Annotation']
    mock_progress(db, wf)
    resp = jm.cycle()
    assert len(resp) == 1
