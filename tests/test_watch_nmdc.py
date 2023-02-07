from src.watch_nmdc import watcher
import os
import json
import shutil


class mock_nmdc():
    def __init__(self, objs, claimed=False):
        self.objs = objs
        self.claimed = claimed

    def list_jobs(self, filt=None):
        return self.objs

    def refresh_token(self):
        return

    def post_objects(self, obj):
        return

    def update_op(self, opid, done=False, meta=None):
        return

    def claim_job(self, job):
        d = self.objs[0]
        d['claimed'] = self.claimed
        if self.claimed:
            d['detail'] = {'id': 'sys:xxx'}
        return d

    def get_op(self, opid):
        return {}


def cleanup():
    tdir = os.path.dirname(__file__)
    dd = os.path.join(tdir, "..", "test_data", "nmdc:mga0xxx")
    if os.path.exists(dd):
        shutil.rmtree(dd)


def test_watcher(monkeypatch):
    tdir = os.path.dirname(__file__)
    wfc = os.path.join(tdir, "..", "test_data", "wf_config")

    monkeypatch.setenv("WF_CONFIG_FILE", wfc)
    w = watcher()
    w.nmdc = mock_nmdc([])
    w.restore()
    w.ckpt()
    w.restore()


def test_claim_jobs(monkeypatch):
    tdir = os.path.dirname(__file__)
    wfc = os.path.join(tdir, "..", "test_data", "wf_config")
    rqcf = os.path.join(tdir, "..", "test_data", "rqc_response2.json")
    rqc = json.load(open(rqcf))

    def mock_status():
        return "Succeeded"

    def mock_restore():
        return

    def mock_get_metadata():
        return {'outputs': {
          "nmdc_rqcfilter.filtered_final": "./test_data/afile",
          "nmdc_rqcfilter.filtered_stats_final": "./test_data/bfile",
          "nmdc_rqcfilter.stats": {
            "input_read_count": 11431762,
            "input_read_bases": 1726196062,
            "output_read_bases": 1244017053,
            "output_read_count": 8312566
            },
        }}

    monkeypatch.setenv("WF_CONFIG_FILE", wfc)
    cleanup()
    w = watcher()
    w.nmdc = mock_nmdc([rqc])
    w.claim_jobs()
    w.jobs[0].jobid = "1234"
    w.jobs[0].check_status = mock_status
    w.jobs[0].get_metadata = mock_get_metadata
    w.jobs[0].opid = "sys:xxx"

    # Need to over-ride restore so the job isn't redone
    w.restore = mock_restore

    w.cycle()
    # TODO: Add some asserts
    w.cycles = 1
    w._POLL = 0
    w.watch()
    cleanup()


def test_reclaim_job(monkeypatch):
    tdir = os.path.dirname(__file__)
    wfc = os.path.join(tdir, "..", "test_data", "wf_config")
    rqcf = os.path.join(tdir, "..", "test_data", "rqc_response.json")
    rqc = json.load(open(rqcf))

    monkeypatch.setenv("WF_CONFIG_FILE", wfc)
    w = watcher()
    w.nmdc = mock_nmdc([rqc], claimed=True)
    w.claim_jobs()
    resp = w.find_job_by_opid("sys:xxx")
    assert resp
