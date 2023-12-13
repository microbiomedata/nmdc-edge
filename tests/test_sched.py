from pymongo import MongoClient
import json
import os
from nmdc_automation.workflow_automation.sched import Scheduler
from pytest import fixture
from pathlib import Path
from time import time


TEST_DIR = os.path.dirname(__file__)
TEST_DATA = os.path.join(TEST_DIR, "..", "test_data")
trigger_set = 'metagenome_annotation_activity_set'
trigger_id = 'nmdc:55a79b5dd58771e28686665e3c3faa0c'
trigger_doid = 'nmdc:1d87115c442a1f83190ae47c7fe4011f'
cols = [
    'data_object_set',
    "omics_processing_set",
    'mags_activity_set',
    'metagenome_assembly_set',
    'jobs',
    'metagenome_annotation_activity_set',
    'read_qc_analysis_activity_set'
    ]

FIXTURE_DIR = Path(__file__).parent / "fixtures"

@fixture
def db():
    conn_str = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    return MongoClient(conn_str).test


@fixture
def mock_api(monkeypatch, requests_mock):
    monkeypatch.setenv("NMDC_API_URL", "http://localhost")
    monkeypatch.setenv("NMDC_CLIENT_ID", "anid")
    monkeypatch.setenv("NMDC_CLIENT_SECRET", "asecret")
    resp = {"expires": {"minutes": time()+60},
            "access_token": "abcd"
            }
    requests_mock.post("http://localhost/token", json=resp)
    resp = ["nmdc:abcd"]
    requests_mock.post("http://localhost/pids/mint", json=resp)
    resp = ["nmdc:abcd"]
    requests_mock.post("http://localhost/pids/bind", json=resp)


def read_json(fn):
    fp = os.path.join(FIXTURE_DIR, fn)
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
    for c in cols:
        db[c].delete_many({})


def init_test(db):
    for col in cols:
        fn = '%s.json' % (col)
        load(db, fn, reset=True)


def mock_progress(db, wf):
    s = wf.collection
    data = read_json("%s.json" % (s))[0]
    if 'version' not in data:
        data['git_url'] = wf.git_repo
        data['version'] = wf.version
    db[s].delete_many({})
    db[s].insert_one(data)


def test_submit(db, mock_api):
    """
    Test basic job creation
    """
    init_test(db)
    reset_db(db)
    load(db, "data_object_set.json")
    load(db, "omics_processing_set.json")

    jm = Scheduler(db, wfn="./tests/workflows_test.yaml",
                   site_conf="./tests/site_configuration_test.toml")

    # This should result in one RQC job
    resp = jm.cycle()
    assert len(resp) == 1

    # The job should now be in a submitted state
    # make this pass
    resp = jm.cycle()
    assert len(resp) == 0


def test_progress(db, mock_api):
    init_test(db)
    reset_db(db)
    db.jobs.delete_many({})
    load(db, "data_object_set.json")
    load(db, "omics_processing_set.json")
    jm = Scheduler(db, wfn="./tests/workflows_test.yaml",
                   site_conf="./tests/site_configuration_test.toml")
    workflow_by_name = dict()
    for wf in jm.workflows:
        workflow_by_name[wf.name] = wf

    # This should result in one RQC job
    resp = jm.cycle()
    assert len(resp) == 1

    wf = workflow_by_name['Reads QC']
    mock_progress(db, wf)
    resp = jm.cycle()
    assert len(resp) == 2
    resp = jm.cycle()
    assert len(resp) == 0

    wf = workflow_by_name['Metagenome Assembly']
    mock_progress(db, wf)
    resp = jm.cycle()
    assert len(resp) == 1

    wf = workflow_by_name['Metagenome Annotation']
    mock_progress(db, wf)
    resp = jm.cycle()
    assert len(resp) == 1

    # We should have job records for everything now
    resp = jm.cycle()
    assert len(resp) == 0

    # Let's remove the job records.
    # Since we don't have activity records for
    # MAGS or RBA, we should see two new jobs
    db.jobs.delete_many({})
    resp = jm.cycle()
    assert len(resp) == 2


def test_multiple_versions(db, mock_api):
    init_test(db)
    reset_db(db)
    db.jobs.delete_many({})
    load(db, "data_object_set.json")
    load(db, "omics_processing_set.json")
    jm = Scheduler(db, wfn="./tests/workflows_test2.yaml",
                   site_conf="./tests/site_configuration_test.toml")
    workflow_by_name = dict()
    for wf in jm.workflows:
        workflow_by_name[wf.name] = wf

    # This should result in two RQC jobs
    resp = jm.cycle()
    assert len(resp) == 2

    # We simulate one of the jobs finishing
    wf = workflow_by_name['Reads QC']
    mock_progress(db, wf)
    resp = jm.cycle()
    # We should see one asm and one rba job
    assert len(resp) == 2
    resp = jm.cycle()
    assert len(resp) == 0
    # Now simulate one of the other jobs finishing
    load(db, "data_object_set2.json", col="data_object_set")
    load(db, "read_qc_analysis_activity_set2.json",
         col="read_qc_analysis_activity_set")
    resp = jm.cycle()
    # We should see one asm and one rba job
    assert len(resp) == 2
    resp = jm.cycle()

    # Empty the job queue.  We should see 4 jobs
    db.jobs.delete_many({})
    resp = jm.cycle()
    assert len(resp) == 4
