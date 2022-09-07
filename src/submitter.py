#!/usr/bin/env python3

import os
import requests
import json
from .wfutils import wfsub

_STAGE_DIR = os.path.join(os.environ["SCRATCH"], "staging")


def mock_get_job():
    resp = json.load(open("response.json"))
    return resp


def download_file(url, dst):
    g = requests.get(url, stream=True)
    with open(dst, 'wb') as out:
        for chunk in g.iter_content(chunk_size=1000000):
            out.write(chunk)


def staging(inp):
    for k, v in inp.items():
        if v.startswith("http"):
            fn = v.split("/")[-1]
            dst = os.path.join(_STAGE_DIR, fn)
            inp[k] = dst
            if os.path.exists(dst):
                continue
            # TODO: use a temp file first
            download_file(v, dst)
    return inp


def submit(job):
    # print(job)
    conf = job['config']
    inp = staging(conf['inputs'])
    ninp = dict()
    for k, v in inp.items():
        nk = '%s.%s' % (conf['input_prefix'], k)
        ninp[nk] = v
    job['config']['inputs'] = ninp
    wfs = wfsub()
    resp = wfs.submit(job, verbose=True, dryrun=False)
    return resp


if __name__ == "__main__":
    wfs = wfsub()
    job = mock_get_job()
    inp = staging(job['job_info']['inputs'])
    job['job_info']['inputs'] = inp
    print(json.dumps(job, indent=2))
    resp = wfs.submit(job, verbose=True, dryrun=False)
    print(resp)
