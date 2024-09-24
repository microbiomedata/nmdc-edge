from nmdc_automation.workflow_automation.sched import Scheduler
from pytest import fixture, mark
from pathlib import Path
from time import time
import os
import json
import logging

from tests.fixtures.db_utils import init_test, load_fixture, read_json, reset_db

TRIGGER_SET = 'metagenome_annotation_activity_set'
TRIGGER_ID = 'nmdc:55a79b5dd58771e28686665e3c3faa0c'
TRIGGER_DOID = 'nmdc:1d87115c442a1f83190ae47c7fe4011f'
trigger_set = 'metagenome_annotation_activity_set'
trigger_id = 'nmdc:55a79b5dd58771e28686665e3c3faa0c'
trigger_doid = 'nmdc:1d87115c442a1f83190ae47c7fe4011f'
cols = [
    'data_object_set',
    "data_generation_set",
    'mags_activity_set',
    'metagenome_assembly_set',
    'jobs',
    'metagenome_annotation_activity_set',
    'read_qc_analysis_activity_set'
    ]

FIXTURE_DIR = Path(__file__).parent / "fixtures"


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
    logging.debug("Loading %d recs into %s" % (len(data), col))
    if len(data) > 0:
        db[col].insert_many(data)


def reset_db(db):
    for c in cols:
        db[c].delete_many({})


def init_test(db):
    for col in cols:
        fn = '%s.json' % (col)
        load(db, fn, reset=True)


def mock_progress(test_db, wf, version=None, flush=True, idx=0):
    """
    This function will mock the progress of a workflow. It reads
    from a fixture file and inserts one record into the database.
    By default, the record will be taken from the first record
    in the fixture.  You can change the record by changing the
    idx parameter.
    """
    s = wf.collection
    data = read_json("%s.json" % (s))[idx]

    if version:
        data['version'] = version
    else:
        data['version'] = wf.version
    data['git_url'] = wf.git_repo
    if flush:
        test_db[s].delete_many({})
    test_db[s].insert_one(data)


@mark.parametrize("workflow_file", [
    "workflows.yaml",
    "workflows-mt.yaml"
])
def test_scheduler_cycle(test_db, mock_api, workflow_file, workflows_config_dir, site_config):
    """
    Test basic job creation.
    """
    exp_rqc_git_repos = [
        "https://github.com/microbiomedata/ReadsQC",
        "https://github.com/microbiomedata/metaT_ReadsQC"
    ]
    # init_test(test_db)
    reset_db(test_db)

    load_fixture(test_db, "data_object_set.json")
    load_fixture(test_db, "omics_processing_set.json")

    # Scheduler will find one job to create
    exp_num_jobs_initial = 1
    exp_num_jobs_cycle_1 = 0
    jm = Scheduler(test_db, wfn=workflows_config_dir / workflow_file,
                   site_conf=site_config)
    resp = jm.cycle()
    assert len(resp) == exp_num_jobs_initial
    assert resp[0]["config"]["git_repo"] in exp_rqc_git_repos

    # All jobs should now be in a submitted state
    resp = jm.cycle()
    assert len(resp) == exp_num_jobs_cycle_1

@mark.parametrize("workflow_file", [
    "workflows.yaml",
    "workflows-mt.yaml"
])
def test_progress(test_db, mock_api, workflow_file, workflows_config_dir, site_config):
    reset_db(test_db)
    metatranscriptome = False
    if workflow_file == "workflows-mt.yaml":
        metatranscriptome = True
    load_fixture(test_db, "data_object_set.json")
    load_fixture(test_db, "omics_processing_set.json")



    jm = Scheduler(test_db, wfn=workflows_config_dir / workflow_file,
                   site_conf= site_config)
    workflow_by_name = dict()
    for wf in jm.workflows:
        workflow_by_name[wf.name] = wf

    # There should be 1 RQC job for each omics_processing_set record
    resp = jm.cycle()
    assert len(resp) == 1

    if metatranscriptome:
        wf = workflow_by_name['Metatranscriptome Reads QC Interleave']
        mock_progress(test_db, wf, idx=1)
    else:
        wf = workflow_by_name['Reads QC Interleave']
        mock_progress(test_db, wf)

    resp = jm.cycle()
    if metatranscriptome:
        # assembly
        exp_num_post_rqc_jobs = 1
    else:
        # assembly, rba
        exp_num_post_rqc_jobs = 2
    assert len(resp) == exp_num_post_rqc_jobs

    if metatranscriptome:
        wf = workflow_by_name['Metatranscriptome Assembly']
        mock_progress(test_db, wf, version="v0.0.1")
        # We should see a metatranscriptome annotation job
        resp = jm.cycle()
        assert len(resp) == 1
        assert resp[0]["config"]["activity"]["type"] in [
            "nmdc:MetatranscriptomeAnnotation",
            "nmdc:MetatranscriptomeAnnotationActivity"
        ]
        # We should have a job record for this now
        resp = jm.cycle()
        assert len(resp) == 0

    else:
        # Let's override the version to simulate an older run
        # for this workflow that is stil within range of the
        # current workflow
        wf = workflow_by_name['Metagenome Assembly']
        # TODO: Need to make this test not depend on a hardcoded version
        mock_progress(test_db, wf, version="v1.0.2")
        # We should see a metagenome annotation job
        resp = jm.cycle()
        assert len(resp) == 1
        assert resp[0]["config"]["activity"]["type"] in [
            "nmdc:MetagenomeAnnotation",
            "nmdc:MetagenomeAnnotationActivity"
        ]
        # We should have a job record for this now
        resp = jm.cycle()
        assert len(resp) == 0
        # Simulate Annotation job finishing
        wf = workflow_by_name['Metagenome Annotation']
        mock_progress(test_db, wf)
        # We should see a MAGs job
        resp = jm.cycle()
        assert len(resp) == 1
        assert resp[0]["config"]["activity"]["type"] in [
            "nmdc:MagsAnalysis",
            "nmdc:MagsAnalysisActivity"
        ]
        # We should have job records for everything now
        resp = jm.cycle()
        assert len(resp) == 0

        # Let's remove the job records.
        # Since we don't have activity records for
        # MAGS or RBA, we should see two new jobs
        test_db.jobs.delete_many({})
        resp = jm.cycle()
        assert len(resp) == 2


def test_multiple_versions(test_db, mock_api, workflows_config_dir, site_config):
    init_test(test_db)
    reset_db(test_db)
    test_db.jobs.delete_many({})

    load_fixture(test_db, "data_object_set.json")
    load_fixture(test_db, "omics_processing_set.json")

    jm = Scheduler(test_db, wfn=workflows_config_dir / "workflows.yaml",
                   site_conf=site_config)
    workflow_by_name = dict()
    for wf in jm.workflows:
        workflow_by_name[wf.name] = wf

    resp = jm.cycle()
    assert len(resp) == 1
    #

    # We simulate one of the jobs finishing
    wf = workflow_by_name['Reads QC']
    mock_progress(test_db, wf)
    resp = jm.cycle()
    # We should see one asm and one rba job
    assert len(resp) == 2
    resp = jm.cycle()
    assert len(resp) == 0
    # Now simulate one of the other jobs finishing
    load_fixture(test_db, "data_object_set2.json", col="data_object_set")
    load_fixture(test_db, "read_qc_analysis_activity_set2.json",
                 col="read_qc_analysis_activity_set")
    resp = jm.cycle()
    # We should see one asm and one rba job
    exp_post_rqc_types = ["nmdc:MetagenomeAssembly", "nmdc:ReadBasedTaxonomyAnalysisActivity"]
    post_rqc_types = [j["config"]["activity"]["type"] for j in resp]
    assert sorted(post_rqc_types) == sorted(exp_post_rqc_types)
    assert len(resp) == 2
    resp = jm.cycle()

    # Empty the job queue.  We should see 4 jobs
    test_db.jobs.delete_many({})
    resp = jm.cycle()
    assert len(resp) == 4


def test_out_of_range(test_db, mock_api, workflows_config_dir, site_config):
    init_test(test_db)
    reset_db(test_db)
    test_db.jobs.delete_many({})
    load_fixture(test_db, "data_object_set.json")
    load_fixture(test_db, "omics_processing_set.json")
    jm = Scheduler(test_db, wfn=workflows_config_dir / "workflows.yaml",
                   site_conf=site_config)
    workflow_by_name = dict()
    for wf in jm.workflows:
        workflow_by_name[wf.name] = wf

    # Let's create two RQC records.  One will be in range
    # and the other will not.  We should only get new jobs
    # for the one in range.
    wf = workflow_by_name['Reads QC']
    mock_progress(test_db, wf)
    mock_progress(test_db, wf, version="v0.0.1", flush=False)

    resp = jm.cycle()
    # there is one additional metatronscriptome rqc job from the fixture
    assert len(resp) == 2
    resp = jm.cycle()
    assert len(resp) == 0

def test_type_resolving(test_db, mock_api, workflows_config_dir, site_config):
    """
    This tests the handling when the same type is used for
    different activity types.  The desired behavior is to
    use the first match.
    """
    init_test(test_db)
    reset_db(test_db)
    test_db.jobs.delete_many({})
    load_fixture(test_db, "data_object_set.json")
    load_fixture(test_db, "omics_processing_set.json")
    load_fixture(test_db, "read_qc_analysis_activity_set.json")

    jm = Scheduler(test_db, wfn=workflows_config_dir / "workflows.yaml",
                   site_conf=site_config)
    workflow_by_name = dict()
    for wf in jm.workflows:
        workflow_by_name[wf.name] = wf

    wf = workflow_by_name['Metagenome Assembly']
    mock_progress(test_db, wf)
    wf = workflow_by_name['Metagenome Annotation']
    mock_progress(test_db, wf)

    resp = jm.cycle()

    assert len(resp) == 2
    assert 'annotation' in resp[1]['config']['inputs']['contig_file']
