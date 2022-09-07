#!/usr/bin/env python

import sys
import os
import json
import tempfile
import requests
from .nmdcapi import nmdcapi
from yaml import load
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader


def not_implemented():
    raise OSError("Not Implemented")


class config():
    cf = os.path.join(os.environ['HOME'], '.wf_config')
    conf_file = os.environ.get('WF_CONFIG_FILE', cf)

    def __init__(self):
        self.conf = self._read_config()
        self.workflows = self._load_workflows()

    def _read_config(self):
        """
        Read config file for URL, WDL dir and template dir
        """
        conf = dict()
        if not os.path.exists(self.conf_file):
            sys.stderr.write("Missing %s.\n" % (self.conf_file))
            sys.stderr.write("Create or set WF_CONFIG_FILE\n")
            sys.exit(1)

        with open(self.conf_file) as f:
            for line in f:
                if line.startswith("#") or line == '\n':
                    continue
                (k, v) = line.rstrip().split('=')
                conf[k.lower()] = v
            if 'cromwell_url' not in conf:
                print("Missing URL")
                sys.exit(1)
            conf['url'] = conf['cromwell_url']
            if 'api' not in conf['url']:
                conf['url'] = conf['url'].rstrip('/') + "/api/workflows/v1"
        return conf

    def get_data_dir(self):
        return self.conf['data_dir']

    def get_stage_dir(self):
        return self.conf['stage_dir']

    def _load_workflows(self):
        """
        Read in the workflow attributes from a yaml file.
        """
        return load(open(self.conf['workflows']), Loader=Loader)


class wfsub:
    """
    Class to handle submissions to cromwell.
    """
    config = config()

    def __init__(self):
        pass

    def submit(self, job, options=None, dryrun=False, verbose=False):
        """
        Submit a job
        """
        # Write input file
        inputs = job['config']['inputs']
        labels = dict()
        params = dict()
        cleanup = []
        for p in ['release', 'wdl', 'git_repo']:
            params[p] = job['config'][p]
            labels[p] = job['config'][p]
        cf = self.config.conf
        labels["pipeline_version"] = params['release']
        labels["pipeline"] = "TODO"
        labels["activity_id"] = "TODO"
        labels["opid"] = "TODO"
        labels["submitter"] = "nmdcda"

        wdl_url = params['git_repo'].rstrip('/')
        wdl_url += "/releases/download/{release}/{wdl}".format(**params)
        wdl_file = fetch_file(wdl_url, suffix='.wdl')
        cleanup.append(wdl_file)
        bundle_url = params['git_repo'].rstrip('/')
        bundle_url += "/releases/download/"
        bundle_url += "{release}/bundle.zip".format(**params)
        bundle_file = fetch_file(bundle_url, suffix='.zip')
        cleanup.append(bundle_file)
        if verbose:
            jprint(inputs)
            jprint(labels)
        infname = _json_tmp(inputs)
        cleanup.append(infname)
        lblname = _json_tmp(labels)
        cleanup.append(lblname)

        files = {
            'workflowSource': open(wdl_file),
            'workflowDependencies': open(bundle_file, 'rb'),
            'workflowInputs': open(infname)
        }
        files['labels'] = open(lblname)

        # TODO: Add something to handle priority
        if options:
            files['workflowOptions'] = open(options)

        if not dryrun:
            resp = requests.post(cf['url'], data={}, files=files).json()
            job_id = resp['id']
        else:
            job_id = "dryrun"
        for fld in files:
            files[fld].close()

        for f in cleanup:
            os.unlink(f)

        return job_id


class job():
    nmdc = nmdcapi()
    config = config()
    conf = config.conf
    wfs = wfsub()
    cromurl = conf['url']
    data_dir = conf['data_dir']
    resource = conf['resource']
    url_root = conf['url_root']
    debug = False

    def __init__(self, fn=None, typ=None, nmdc_jobid=None, proj=None,
                 opid=None, activity_id=None, state=None, nocheck=False):
        if state:
            self.activity_id = state['activity_id']
            self.nmdc_jobid = state['nmdc_jobid']
            self.opid = state.get('opid', None)
            self.type = state['type']
            self.proj = state['proj']
            self.jobid = state['cromwell_jobid']
            self.last_status = state['last_status']
            self.fn = state['fn']
            self.failed_count = state.get('failed_count', 0)
            self.done = state.get('done', None)
        else:
            self.activity_id = activity_id
            self.type = typ
            self.proj = proj
            self.nmdc_jobid = nmdc_jobid
            self.opid = opid
            self.done = None
            self.fn = fn
            self.jobid = None
            self.failed_count = 0
            self.last_status = "Unsubmitted"
        # Set workflow parameters
        wf = self.config.workflows[self.type]
        self.workflow = self.config.workflows[self.type]
        self.version = self.workflow["version"]
        self.pipeline = self.workflow["pipeline"]
        self.git_url = self.workflow["git_url"]
        self.prefix = self.workflow["prefix"]

        if not self.activity_id:
            prefix = wf["prefix"]
            self.activity_id = self.nmdc.mint("nmdc", prefix, 1)[0]

        if self.jobid and not nocheck:
            self.check_status()

        if self.opid and not nocheck:
            opstat = self.nmdc.get_op(self.opid)
            self.done = opstat['done']

    def get_state(self):
        data = {
                "type": self.type,
                "cromwell_jobid": self.jobid,
                "nmdc_jobid": self.nmdc_jobid,
                "proj": self.proj,
                "activity_id": self.activity_id,
                "last_status": self.last_status,
                "done": self.done,
                "fn": self.fn,
                "failed_count": self.failed_count,
                "opid": self.opid
                }
        return data

    def log(self, msg):
        if self.debug:
            print(msg)

    def check_status(self):
        """
        Check the status in Cromwell
        """
        if not self.jobid:
            return "Unsubmitted"
        url = "%s/%s/status" % (self.cromurl, self.jobid)
        resp = requests.get(url)
        state = "Unknown"
        if resp.status_code == 200:
            data = resp.json()
            state = data['status']
        self.last_status = state
        return state

    def cromwell_submit(self, force=False):
        """
        Check if a task needs to be submitted.
        """

        # Refresh the log
        status = self.check_status()
        states = ['Failed', 'Aborted', 'Aborting', "Unsubmitted"]
        if not force and status not in states:
            self.log("Skipping: %s %s" % (self.fn, status))
            return
        # Reuse the ID from before
        self.log("Resubmit %s" % (self.activity_id))

        # TODO: This is not tested yet
        params = {
          "actid": self.activity_id,
          "inputfile": self.fn,
          "informed_by": self.proj,
          "opid": self.opid
        }

        jid = self.wfs.submit(self.type, params, dryrun=False, verbose=True)

        print("Submitted: %s" % (jid))
        self.jobid = jid
        self.done = False


def _json_tmp(data):
    fp, fname = tempfile.mkstemp(suffix='.json')
    with os.fdopen(fp, 'w') as fd:
        fd.write(json.dumps(data))
    return fname


def fetch_file(url, suffix=None):
    resp = requests.get(url, stream=True)
    if resp.status_code != 200:
        raise ValueError("Bad response")
    fp, fname = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(fp, 'wb') as fd:
        for chunk in resp.iter_content(chunk_size=1000000):
            fd.write(chunk)
    return fname


def jprint(data):
    print(json.dumps(data, indent=2))
