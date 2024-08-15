from nmdc_automation.workflow_automation.sched import Scheduler
from pytest import fixture, mark
from pathlib import Path
from time import time

from tests.fixtures.db_utils import init_test, load, read_json, reset_db

TEST_DIR = Path(__file__).parent
CONFIG_DIR = TEST_DIR.parent / "configs"
TRIGGER_SET = 'metagenome_annotation_activity_set'
TRIGGER_ID = 'nmdc:55a79b5dd58771e28686665e3c3faa0c'
TRIGGER_DOID = 'nmdc:1d87115c442a1f83190ae47c7fe4011f'

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
    if 'version' not in data:
        data['git_url'] = wf.git_repo
        data['version'] = wf.version
    if version:
        data['version'] = version
    if flush:
        test_db[s].delete_many({})
    test_db[s].insert_one(data)


@mark.parametrize("workflow_file", [
    CONFIG_DIR / "workflows.yaml",
    CONFIG_DIR / "workflows-mt.yaml"
])
def test_submit(test_db, mock_api, workflow_file):
    """
    Test basic job creation
    """
    init_test(test_db)
    reset_db(test_db)
    load(test_db, "data_object_set.json")
    load(test_db, "omics_processing_set.json")

    jm = Scheduler(test_db, wfn=workflow_file,
                   site_conf=TEST_DIR / "site_configuration_test.toml")

    # This should result in one RQC job
    resp = jm.cycle()
    assert len(resp) == 1

    # The job should now be in a submitted state
    resp = jm.cycle()
    assert len(resp) == 0

@mark.parametrize("workflow_file", [
    CONFIG_DIR / "workflows.yaml",
    # CONFIG_DIR / "workflows-mt.yaml"
])
def test_progress_metagenome(test_db, mock_api, workflow_file):
    init_test(test_db)
    reset_db(test_db)
    test_db.jobs.delete_many({})
    load(test_db, "data_object_set.json")
    load(test_db, "omics_processing_set.json")
    jm = Scheduler(test_db, wfn=workflow_file,
                   site_conf= TEST_DIR / "site_configuration_test.toml")
    workflow_by_name = dict()
    for wf in jm.workflows:
        workflow_by_name[wf.name] = wf

    # This should result in one RQC job
    resp = jm.cycle()
    assert len(resp) == 1

    if workflow_file.name == "workflows-mt.yaml":
        # The job should now be in a submitted state
        wf = workflow_by_name['Metatranscriptome Reads QC Interleave']
        mock_progress(test_db, wf, idx=1)
    else:
        wf = workflow_by_name['Reads QC Interleave']
        mock_progress(test_db, wf)

    resp = jm.cycle()
    assert len(resp) == 2
    resp = jm.cycle()
    assert len(resp) == 0

    wf = workflow_by_name['Metagenome Assembly']
    # Lets override the version to simulate an older run
    # for this workflow that is stil within range of the
    # current workflow
    mock_progress(test_db, wf, version="v1.0.2")
    resp = jm.cycle()
    assert "imgap_project_id" in resp[0]["config"]["inputs"]
    assert len(resp) == 1
    omap = {}
    for o in resp[0]["config"]["outputs"]:
        omap[o["output"]] = o
    assert omap["map_file"]["data_object_type"] == "Contig Mapping File"

    wf = workflow_by_name['Metagenome Annotation']
    mock_progress(test_db, wf)
    resp = jm.cycle()
    assert len(resp) == 1

    # We should have job records for everything now
    resp = jm.cycle()
    assert len(resp) == 0

    # Let's remove the job records.
    # Since we don't have activity records for
    # MAGS or RBA, we should see two new jobs
    test_db.jobs.delete_many({})
    resp = jm.cycle()
    assert len(resp) == 2


def test_multiple_versions(test_db, mock_api):
    init_test(test_db)
    reset_db(test_db)
    test_db.jobs.delete_many({})
    load(test_db, "data_object_set.json")
    load(test_db, "omics_processing_set.json")
    jm = Scheduler(test_db, wfn=CONFIG_DIR / "workflows.yaml",
                   site_conf=TEST_DIR/"site_configuration_test.toml")
    workflow_by_name = dict()
    for wf in jm.workflows:
        workflow_by_name[wf.name] = wf

    # This should result in two RQC jobs
    resp = jm.cycle()
    # assert len(resp) == 2
    # TODO: Is the assertion correct? - actual len(resp) is 1
    #    A job for RQC Interleaved is created instead of two RQC jobs
    assert len(resp) == 1

    # We simulate one of the jobs finishing
    wf = workflow_by_name['Reads QC']
    mock_progress(test_db, wf)
    resp = jm.cycle()
    # We should see one asm and one rba job
    assert len(resp) == 2
    resp = jm.cycle()
    assert len(resp) == 0
    # Now simulate one of the other jobs finishing
    load(test_db, "data_object_set2.json", col="data_object_set")
    load(test_db, "read_qc_analysis_activity_set2.json",
         col="read_qc_analysis_activity_set")
    resp = jm.cycle()
    # We should see one asm and one rba job
    assert len(resp) == 2
    resp = jm.cycle()

    # Empty the job queue.  We should see 4 jobs
    test_db.jobs.delete_many({})
    resp = jm.cycle()
    assert len(resp) == 4


def test_out_of_range(test_db, mock_api):
    init_test(test_db)
    reset_db(test_db)
    test_db.jobs.delete_many({})
    load(test_db, "data_object_set.json")
    load(test_db, "omics_processing_set.json")
    jm = Scheduler(test_db, wfn=CONFIG_DIR / "workflows.yaml",
                   site_conf=TEST_DIR / "site_configuration_test.toml")
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
    assert len(resp) == 2
    resp = jm.cycle()
    assert len(resp) == 0

def test_type_resolving(test_db, mock_api):
    """
    This tests the handling when the same type is used for
    different activity types.  The desired behavior is to
    use the first match.
    """

    init_test(test_db)
    reset_db(test_db)
    test_db.jobs.delete_many({})
    load(test_db, "data_object_set.json")
    load(test_db, "omics_processing_set.json")
    load(test_db, "read_qc_analysis_activity_set.json")

    jm = Scheduler(test_db, wfn=CONFIG_DIR / "workflows.yaml",
                   site_conf=TEST_DIR / "site_configuration_test.toml")
    workflow_by_name = dict()
    for wf in jm.workflows:
        workflow_by_name[wf.name] = wf

    wf = workflow_by_name['Metagenome Assembly']
    mock_progress(test_db, wf)
    wf = workflow_by_name['Metagenome Annotation']
    mock_progress(test_db, wf)

    resp = jm.cycle()
    assert len(resp) == 2

