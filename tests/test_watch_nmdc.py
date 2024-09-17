from nmdc_automation.workflow_automation.watch_nmdc import Watcher
import os
import json
import shutil
from pytest import fixture


@fixture
def site_conf():
    tdir = os.path.dirname(__file__)
    return os.path.join(tdir, "..", "tests",
                        "site_configuration_test.toml")


@fixture(autouse=True)
def cleanup():
    tdir = os.path.dirname(__file__)
    dd = os.path.join(tdir, "..", "test_data", "nmdc:mga0xxx")
    if os.path.exists(dd):
        shutil.rmtree(dd)
    omics_id = "nmdc:omprc-11-nhy4pz43/"
    if os.path.exists(f"/tmp/{omics_id}"):
        shutil.rmtree(f"/tmp/{omics_id}")
    if os.path.exists("/tmp/agent.state"):
        os.unlink("/tmp/agent.state")


@fixture
def mock_nmdc_api(requests_mock):
    tdir = os.path.dirname(__file__)
    rqcf = os.path.join(tdir, "..", "test_data", "rqc_response2.json")
    rqc = json.load(open(rqcf))
    resp = {"resources": [rqc]}
    requests_mock.get("http://localhost/jobs", json=resp)
    requests_mock.post("http://localhost/workflows/activities", json={})
    requests_mock.patch("http://localhost/operations/nmdc:1234", json={})
    requests_mock.get("http://localhost/operations/nmdc:1234",
                      json={'metadata': {}})


@fixture(autouse=True)
def mock_cromwell(requests_mock):
    requests_mock.real_http = True
    data = {"id": "1234"}
    cromwell_url = "http://localhost:8088/api/workflows/v1"
    requests_mock.post(cromwell_url, json=data)
    metadata = {'outputs': {
          "nmdc_rqcfilter.filtered_final": "./test_data/afile",
          "nmdc_rqcfilter.filtered_stats_final": "./test_data/bfile",
          "nmdc_rqcfilter.stats": {
            "input_read_count": 11431762,
            "input_read_bases": 1726196062,
            "output_read_bases": 1244017053,
            "output_read_count": 8312566
            },
        }}
    requests_mock.get(f"{cromwell_url}/1234/metadata", json=metadata)
    data = {"status": "Succeeded"}
    requests_mock.get(f"{cromwell_url}/1234/status", json=data)


def test_watcher(site_conf):
    w = Watcher(site_conf)
    w.restore()
    w.job_checkpoint()
    w.restore()


def test_claim_jobs(requests_mock, site_conf, mock_nmdc_api):
    requests_mock.real_http = True
    w = Watcher(site_conf)
    job_id = "nmdc:b7eb8cda-a6aa-11ed-b1cf-acde48001122"
    resp = {
            'id': 'nmdc:1234',
            'detail': {'id': 'nmdc:1234'}
            }
    requests_mock.post(f"http://localhost/jobs/{job_id}:claim", json=resp)
    w.claim_jobs()
    w.cycle()
    resp = w.find_job_by_opid("nmdc:1234")
    assert resp


def test_reclaim_job(requests_mock, site_conf, mock_nmdc_api):
    requests_mock.real_http = True

    w = Watcher(site_conf)
    job_id = "nmdc:b7eb8cda-a6aa-11ed-b1cf-acde48001122"
    resp = {
            'id': 'nmdc:1234',
            'detail': {'id': 'nmdc:1234'}
            }
    requests_mock.post(f"http://localhost/jobs/{job_id}:claim", json=resp,
                       status_code=409)
    w.claim_jobs()
    resp = w.find_job_by_opid("nmdc:1234")
