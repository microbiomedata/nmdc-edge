#!/usr/bin/env python

import os
import json
import tempfile
import requests
from .config import config
import logging
from time import time
import datetime
import pytz


class job():
    # nmdc = nmdcapi()
    config = config().conf
    cromurl = config['url']
    data_dir = config['data_dir']
    resource = config['resource']
    url_root = config['url_root']
    debug = False
    dryrun = False
    # Future
    options = None
    activity_templ = None
    outputs = None
    input_data_objects = []
    start = None
    end = None
    # TODO: Add these to the checkpoint

    def __init__(self, typ=None, nmdc_jobid=None, conf=None,
                 opid=None, activity_id="TODO", state=None, nocheck=False):
        if state:
            self.activity_id = state['activity_id']
            self.nmdc_jobid = state['nmdc_jobid']
            self.opid = state.get('opid', None)
            self.type = state['type']
            self.conf = state['conf']
            self.jobid = state['cromwell_jobid']
            self.last_status = state['last_status']
            self.failed_count = state.get('failed_count', 0)
            self.done = state.get('done', None)
            self.start = state.get('start')
            self.end = state.get('end')
        else:
            self.activity_id = activity_id
            self.type = typ
            self.conf = conf
            self.nmdc_jobid = nmdc_jobid
            self.opid = opid
            self.done = None
            self.jobid = None
            self.failed_count = 0
            self.last_status = "Unsubmitted"

        if 'outputs' in self.conf:
            self.outputs = self.conf['outputs']
        if 'activity' in self.conf:
            self.activity_templ = self.conf['activity']
        if 'input_data_objects' in self.conf:
            self.input_data_objects = self.conf['input_data_objects']

        if self.jobid and not nocheck:
            self.check_status()

    def get_state(self):
        data = {
                "type": self.type,
                "cromwell_jobid": self.jobid,
                "nmdc_jobid": self.nmdc_jobid,
                "conf": self.conf,
                "activity_id": self.activity_id,
                "last_status": self.last_status,
                "done": self.done,
                "failed_count": self.failed_count,
                "start": self.start,
                "end": self.end,
                "opid": self.opid
                }
        return data

    def json_log(self, data, title="json_log"):
        logging.debug(title)
        logging.debug(json.dumps(data, indent=2))

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
        if state == "Succeeded" and not self.end:
            self.end = datetime.datetime.now(pytz.utc).isoformat()
        return state

    def get_metadata(self):
        """
        Check the status in Cromwell
        """
        if not self.jobid:
            return "Unsubmitted"
        url = "%s/%s/metadata" % (self.cromurl, self.jobid)
        resp = requests.get(url)
        md = {}
        if resp.status_code == 200:
            md = resp.json()
        return md

    def _generate_inputs(self):
        inputs = dict()
        prefix = self.conf['input_prefix']
        for k, v in self.conf['inputs'].items():
            nk = f'{prefix}.{k}'
            # TODO: clean this up
            if v == "{resource}":
                v = self.config['resource']
            inputs[nk] = v
        return inputs

    def _generate_labels(self):
        labels = dict()
        for p in ['release', 'wdl', 'git_repo']:
            labels[p] = self.conf[p]
        labels["pipeline_version"] = labels['release']
        labels["pipeline"] = labels['wdl']
        labels["activity_id"] = self.activity_id
        labels["opid"] = self.opid
        labels["submitter"] = "nmdcda"
        return labels

    def fetch_release_file(self, fn, suffix=None):
        release = self.conf['release']
        url = self.conf['git_repo'].rstrip('/')
        url += f"/releases/download/{release}/{fn}"

        resp = requests.get(url, stream=True)
        if resp.status_code != 200:
            raise ValueError("Bad response")
        fp, fname = tempfile.mkstemp(suffix=suffix)
        with os.fdopen(fp, 'wb') as fd:
            for chunk in resp.iter_content(chunk_size=1000000):
                fd.write(chunk)
        return fname

    def cromwell_submit(self, force=False):
        """
        Check if a task needs to be submitted.
        """

        # Refresh the log
        status = self.check_status()
        states = ['Failed', 'Aborted', 'Aborting', "Unsubmitted"]
        if not force and status not in states:
            logging.info("Skipping: %s %s" % (self.activity_id, status))
            return
        # Reuse the ID from before
        # logging.info("Resubmit %s" % (self.activity_id))

        cleanup = []
        files = {}
        job_id = "unknown"
        conf = self.conf
        try:
            inputs = self._generate_inputs()
            labels = self._generate_labels()
            wdl_file = self.fetch_release_file(conf['wdl'], suffix='.wdl')
            cleanup.append(wdl_file)
            bundle_file = self.fetch_release_file("bundle.zip", suffix='.zip')
            cleanup.append(bundle_file)
            self.json_log(inputs, title="Inputs")
            self.json_log(labels, title="Labels")
            infname = _json_tmp(inputs)
            cleanup.append(infname)
            lblname = _json_tmp(labels)
            cleanup.append(lblname)

            files['workflowSource'] = open(wdl_file)
            files['workflowDependencies'] = open(bundle_file, 'rb')
            files['workflowInputs'] = open(infname)
            files['labels'] = open(lblname)

            # TODO: Add something to handle priority
            if self.options:
                files['workflowOptions'] = open(self.options)

            if not self.dryrun:
                resp = requests.post(self.cromurl, data={}, files=files)
                if resp.ok:
                    data = resp.json()
                    self.json_log(data, title="Response")
                    job_id = data['id']
            else:
                job_id = "dryrun"

            logging.info(f"Submitted: {job_id}")
            self.start = datetime.datetime.now(pytz.utc).isoformat()
            self.jobid = job_id
            self.done = False

        finally:
            for fld in files:
                files[fld].close()

            for f in cleanup:
                os.unlink(f)


def _json_tmp(data):
    fp, fname = tempfile.mkstemp(suffix='.json')
    with os.fdopen(fp, 'w') as fd:
        fd.write(json.dumps(data))
    return fname
