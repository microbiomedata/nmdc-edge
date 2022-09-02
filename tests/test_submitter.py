from pymongo import MongoClient
import json
import os
from job_finder import JobMaker

test_dir = os.path.dirname(__file__)
test_data = os.path.join(test_dir, "..", "test_data")
trigger_set = 'metagenome_annotation_activity_set'
trigger_id = 'nmdc:55a79b5dd58771e28686665e3c3faa0c'
trigger_doid = 'nmdc:1d87115c442a1f83190ae47c7fe4011f'


def load(db, fn, col=None, reset=False):
    if not col:
        col = fn.split("/")[-1].split(".")[0]
    if reset:
        db[col].delete_many({})
    fp = os.path.join(test_data, fn)
    data = json.load(open(fp))
    print("Loading %d recs into %s" % (len(data), col))
    db[col].insert_many(data)


def init_test(db):
    for fn in os.listdir(test_data):
        load(db, fn, reset=True)


def test_submitter():
    client = MongoClient("mongodb://127.0.0.1:55000")
    db = client.test
    init_test(db)
    jm = JobMaker(db="test")

    # This should result in one RQC job
    resp = jm.cycle()
    print(resp)
    assert len(resp) == 1

    # The job should now be in a submitted state
    # TODO make this pass
    resp = jm.cycle()
    # assert len(resp) == 0
