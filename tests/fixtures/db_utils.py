"""
Utilities for test database setup and teardown and loading fixtures
"""
import json
import logging
from pathlib import Path

# this file lives in tests/fixtures
FIXTURE_DIR = Path(__file__).parent
COLS = [
    'data_object_set',
    "omics_processing_set",
    'mags_activity_set',
    'metagenome_assembly_set',
    'metatranscriptome_assembly_set',
    'jobs',
    'metagenome_annotation_activity_set',
    'metatranscriptome_annotation_set',
    'metatranscriptome_expression_analysis_set',
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

def update_test_db_with_workflow_versions(test_db, workflows):
    """
    This function will update the loaded fixtures with the workflow versions
    and git urls from the workflow objects.  This is needed for the tests
    to work correctly.
    """
    for wf in workflows:
        db_records = test_db[wf.collection].find({"type": wf.type})
        for rec in db_records:
            rec["git_url"] = wf.git_repo
            rec["version"] = wf.version
            test_db[wf.collection].replace_one({"id": rec["id"]}, rec)
    return


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


def get_updated_fixture(wf):
    """
    Read the fixture file and update the version and git_url for the
    fixtures that of the same workflow type.
    """
    updated_fixtures = []
    fixture_file = f"{wf.collection}.json"
    try:
        with open(FIXTURE_DIR / fixture_file) as f:
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
