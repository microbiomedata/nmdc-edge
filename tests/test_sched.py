from nmdc_automation.workflow_automation.sched import Scheduler, SchedulerJob
from pytest import mark


from tests.fixtures.db_utils import init_test, load_fixture, read_json, reset_db


@mark.parametrize("workflow_file", [
    "workflows.yaml",
    "workflows-mt.yaml"
])
def test_scheduler_cycle(test_db, mock_api, workflow_file, workflows_config_dir, site_config_file):
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
    load_fixture(test_db, "data_generation_set.json")

    # Scheduler will find one job to create
    exp_num_jobs_initial = 1
    exp_num_jobs_cycle_1 = 0
    jm = Scheduler(test_db, wfn=workflows_config_dir / workflow_file,
                   site_conf=site_config_file)
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
def test_progress(test_db, mock_api, workflow_file, workflows_config_dir, site_config_file):
    reset_db(test_db)
    metatranscriptome = False
    if workflow_file == "workflows-mt.yaml":
        metatranscriptome = True
    load_fixture(test_db, "data_object_set.json")
    load_fixture(test_db, "data_generation_set.json")



    jm = Scheduler(test_db, wfn=workflows_config_dir / workflow_file,
                   site_conf= site_config_file)
    workflow_by_name = dict()
    for wf in jm.workflows:
        workflow_by_name[wf.name] = wf

    # There should be 1 RQC job for each omics_processing_set record
    resp = jm.cycle()
    assert len(resp) == 1

    # We simulate the RQC job finishing
    load_fixture(test_db, "read_qc_analysis.json", col="workflow_execution_set")

    resp = jm.cycle()
    if metatranscriptome:
        # assembly
        exp_num_post_rqc_jobs = 1
        exp_num_post_annotation_jobs = 1
    else:
        # assembly, rba
        exp_num_post_rqc_jobs = 2
        exp_num_post_annotation_jobs = 2
    assert len(resp) == exp_num_post_rqc_jobs

    if metatranscriptome:
        # simulate assembly job finishing
        load_fixture(test_db, "metatranscriptome_assembly.json", col="workflow_execution_set")
        # We should see a metatranscriptome annotation job
        resp = jm.cycle()
        assert len(resp) == 1
        assert resp[0]["config"]["activity"]["type"] == "nmdc:MetatranscriptomeAnnotation"

        resp = jm.cycle()
        # all jobs should be in a submitted state
        assert len(resp) == 0

        # simulate annotation job finishing
        load_fixture(test_db, "metatranscriptome_annotation.json", col="workflow_execution_set")
        resp = jm.cycle()
        assert len(resp) == 1
        assert resp[0]["config"]["activity"]["type"] == "nmdc:MetatranscriptomeExpressionAnalysis"
    else:
        # simulate assembly job finishing
        load_fixture(test_db, "metagenome_assembly.json", col="workflow_execution_set")
        # We should see a metagenome annotation job
        resp = jm.cycle()
        assert len(resp) == 1
        assert resp[0]["config"]["activity"]["type"] == "nmdc:MetagenomeAnnotation"

        resp = jm.cycle()
        # all jobs should be in a submitted state
        assert len(resp) == 0

        # simulate annotation job finishing
        load_fixture(test_db, "metagenome_annotation.json", col="workflow_execution_set")
        resp = jm.cycle()
        assert len(resp) == 1
        assert resp[0]["config"]["activity"]["type"] == "nmdc:MagsAnalysis"

    resp = jm.cycle()
    # all jobs should be in a submitted state
    assert len(resp) == 0

    # Let's remove the job records.
    test_db.jobs.delete_many({})
    resp = jm.cycle()
    assert len(resp) == exp_num_post_annotation_jobs


def test_multiple_versions(test_db, mock_api, workflows_config_dir, site_config_file):
    init_test(test_db)
    reset_db(test_db)
    test_db.jobs.delete_many({})

    load_fixture(test_db, "data_object_set.json")
    load_fixture(test_db, "data_generation_set.json")

    jm = Scheduler(test_db, wfn=workflows_config_dir / "workflows.yaml",
                   site_conf=site_config_file)
    workflow_by_name = dict()
    for wf in jm.workflows:
        workflow_by_name[wf.name] = wf

    resp = jm.cycle()
    assert len(resp) == 1
    #

    # We simulate one of the jobs finishing
    load_fixture(test_db, "read_qc_analysis.json", col="workflow_execution_set")
    resp = jm.cycle()
    # We should see one asm and one rba job
    assert len(resp) == 2
    resp = jm.cycle()
    assert len(resp) == 0
    # Simulate the assembly job finishing with an older version
    load_fixture(test_db, "metagenome_assembly.json", col="workflow_execution_set", version="v1.0.2")

    resp = jm.cycle()
    # We should see one rba job
    assert len(resp) == 1
    resp = jm.cycle()
    assert len(resp) == 0


def test_out_of_range(test_db, mock_api, workflows_config_dir, site_config_file):
    init_test(test_db)
    reset_db(test_db)
    test_db.jobs.delete_many({})
    load_fixture(test_db, "data_object_set.json")
    load_fixture(test_db, "data_generation_set.json")
    jm = Scheduler(test_db, wfn=workflows_config_dir / "workflows.yaml",
                   site_conf=site_config_file)
    # Let's create two RQC records.  One will be in range
    # and the other will not.  We should only get new jobs
    # for the one in range.
    load_fixture(test_db, "read_qc_analysis.json", col="workflow_execution_set")
    load_fixture(test_db, "read_qc_analysis.json", col="workflow_execution_set", version="v0.0.1")

    resp = jm.cycle()
    # there is one additional metatronscriptome rqc job from the fixture
    assert len(resp) == 2
    resp = jm.cycle()
    assert len(resp) == 0

def test_type_resolving(test_db, mock_api, workflows_config_dir, site_config_file):
    """
    This tests the handling when the same type is used for
    different activity types.  The desired behavior is to
    use the first match.
    """
    reset_db(test_db)
    load_fixture(test_db, "data_object_set.json")
    load_fixture(test_db, "data_generation_set.json")
    load_fixture(test_db, "read_qc_analysis.json", col="workflow_execution_set")

    jm = Scheduler(test_db, wfn=workflows_config_dir / "workflows.yaml",
                   site_conf=site_config_file)
    workflow_by_name = dict()
    for wf in jm.workflows:
        workflow_by_name[wf.name] = wf

    # mock progress
    load_fixture(test_db, "metagenome_assembly.json", col="workflow_execution_set")
    load_fixture(test_db, "metagenome_annotation.json", col="workflow_execution_set")

    resp = jm.cycle()

    assert len(resp) == 2
    # assert 'annotation' in resp[1]['config']['inputs']['contig_file']


@mark.parametrize("workflow_file", [
    "workflows.yaml",
    "workflows-mt.yaml"
])
def test_scheduler_add_job_rec(test_db, mock_api, workflow_file, workflows_config_dir, site_config_file):
    """
    Test basic job creation.
    """
    reset_db(test_db)
    load_fixture(test_db, "data_object_set.json")
    load_fixture(test_db, "data_generation_set.json")

    jm = Scheduler(test_db, wfn=workflows_config_dir / workflow_file,
                   site_conf=site_config_file)
    # sanity check
    assert jm

