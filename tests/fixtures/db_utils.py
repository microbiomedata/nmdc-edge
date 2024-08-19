"""
Utilities for test database setup and teardown and loading fixtures
"""
import json
import logging
from pathlib import Path

FIXTURE_DIR = Path(__file__).parent
COLS = [
    'data_object_set',
    "omics_processing_set",
    'mags_activity_set',
    'metagenome_assembly_set',
    'jobs',
    'metagenome_annotation_activity_set',
    'read_qc_analysis_activity_set'
    ]


def read_json(fn):
    fp = FIXTURE_DIR / fn
    data = json.load(open(fp))
    return data


def load_fixture(test_db, fn, col=None, reset=False):
    if not col:
        col = fn.split("/")[-1].split(".")[0]
    if reset:
        test_db[col].delete_many({})
    data = read_json(fn)
    logging.debug("Loading %d recs into %s" % (len(data), col))
    if len(data) > 0:
        test_db[col].insert_many(data)


def reset_db(test_db):
    for c in COLS:
        test_db[c].delete_many({})


def init_test(test_db):
    for col in COLS:
        fn = '%s.json' % (col)
        load_fixture(test_db, fn, reset=True)
