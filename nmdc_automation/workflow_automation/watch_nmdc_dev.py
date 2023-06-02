#!/usr/bin/env python

from time import sleep
import os
import json
import sys
import logging
import shutil
from pymongo import MongoClient
from json import dumps, loads
from os.path import exists
from nmdc_automation.api.nmdcapi import nmdcapi
from nmdc_automation.workflow_automation.config import config
from nmdc_automation.workflow_automation.wfutils import _md5
from nmdc_automation.workflow_automation.wfutils import job as wfjob

logger = logging.getLogger(__name__)


class Watcher:
    def __init__(self, site_configuration_file):
        self._POLL = 20
        self._MAX_FAILS = 2
        self.config = config(site_configuration_file)
        self.client_id = self.config.conf['credentials']['client_id']
        self.client_secret = self.config.conf['credentials']['client_secret']
        self.cromurl = self.config.conf['cromwell']['cromwell_url']
        self.state_file = self.config.conf['state']['agent_state']
        self.stage_dir = self.config.get_stage_dir()
        self.raw_dir = self.config.conf['directories']['raw_dir']
        self.jobs = []
        self.nmdc = nmdcapi()
        
        self._ALLOWED = self.config._generate_allowed_workflows()

    def restore(self, nocheck=False):
        """
        Restore from chkpt
        """
        if not exists(self.state_file):
            return

        with open(self.state_file, 'r') as f:
            data = loads(f.read())

        new_job_list = []
        seen = dict()
        for job in data['jobs']:
            job_id = job['nmdc_jobid']
            if job_id in seen:
                continue
            job_record = wfjob(self.config.conf,state=job, nocheck=nocheck)
            new_job_list.append(job_record)
            seen[job_id] = True

        self.jobs = new_job_list

    def job_checkpoint(self):
        jobs = [job.get_state() for job in self.jobs]
        data = {'jobs': jobs}
        with open(self.state_file, "w") as f:
            f.write(dumps(data, indent=2))

    def cycle(self):
        self.restore()
        if not os.environ.get("SKIP_CLAIM"):
            self.claim_jobs()
        self.check_status()

    def watch(self):
        logger.info("Entering polling loop")
        while True:
            try:
                self.cycle()
            except Exception as e:
                logger.exception("Error occurred during cycle:", exc_info=True)
            sleep(self._POLL)

    def find_job_by_opid(self, opid):
        for job in self.jobs:
            if job.opid == opid:
                return
            
    def submit(self, njob, opid, force=False):
        wfid = njob['workflow']['id']
        if 'object_id_latest' in njob['config']:
            logger.warning("Old record. Skipping.")
            return

        job = self.find_job_by_opid(opid)
        if job:
            logger.debug("Previously cached job")
            logger.info(f"Reusing activity {job.activity_id}")
        else:
            job = wfjob(config=self.config.conf,typ = wfid, nmdc_jobid = njob['id'], conf = njob['config'],opid = opid, activity_id=njob['config']['activity_id'])
            self.jobs.append(job)

        job.cromwell_submit(force=force)

    def refresh_remote_jobs(self):
        """
        Return a filtered list of nmdc jobs.
        """
        filt = {"workflow.id": {"$in": self._ALLOWED}}
        jobs = self.nmdc.list_jobs(filt=filt)
        # Get the jobs we know about
        known = {}
        for j in self.jobs:
            known[j.nmdc_jobid] = 1
        resp = []
        for job in jobs:
            job_id = job['id']
            if job_id in known:
                continue
            resp.append(job)
        return resp

    def claim_jobs(self):
        for job in self.refresh_remote_jobs():
            job_id = job['id']
            if job.get('claims') and len(job.get('claims')) > 0:
                continue
            logger.debug(f"try to claim: {job_id}")

            # claim job
            claim = self.nmdc.claim_job(job_id)
            if not claim['claimed']:
                logger.debug(claim)
                self.submit(job, claim['id'])
                self.job_checkpoint()
            else:
                # Previously claimed
                opid = claim['detail']['id']
                # op = self.nmdc.get_op(opid)
                logger.info("Previously claimed.")
                self.submit(job, opid)
                self.job_checkpoint()

    def _load_json(self, file_name):
        return json.loads(open(file_name).read())

    
    def fix_urls(self, data_object_list, actid, subdir):
        root = self.config.conf['url_root'].rstrip('/')
        for data_object in data_object_list:
            file_name = data_object['url'].split('/')[-1]
            new_url = f"{root}/{actid}/{subdir}/{file_name}"
            data_object['url'] = new_url

    def _get_url(self, informed_by, act_id, fname):
        root = self.config.conf['url_root'].rstrip('/')
        return f"{root}/{informed_by}/{act_id}/{fname}"

    def _get_output_dir(self, informed_by, act_id):
        data_directory = self.config.get_data_dir()
        outdir = os.path.join(data_directory, informed_by, act_id)
        if not os.path.exists(outdir):
            os.makedirs(outdir)
        return outdir

    def post_job_done_new(self, job):
        # Prepare the result record
        logger.info("Running post for op %s" % (job.opid))
        metadata = job.get_metadata()
        job_outs = metadata['outputs']
        informed_by = job.conf["was_informed_by"]
        act_id = job.activity_id
        outdir = self._get_output_dir(informed_by, act_id)

        obj = {}
        output_ids = []
        output_dos = []
        # Generate DOs
        prefix = job.conf['input_prefix']
        for product_record in job.outputs:
            outkey = f"{prefix}.{product_record['output']}"
            full_name = job_outs[outkey]
            print(outkey, full_name)
            fname = os.path.basename(full_name)
            np = os.path.join(outdir, fname)
            shutil.copyfile(full_name, np)
            md5 = _md5(full_name)
            id = product_record["id"]
            desc = product_record['description'].replace('{id}', act_id)
            do = {
                "id": product_record["id"],
                "name": product_record['name'],
                "description": desc,
                "file_size_bytes": os.stat(full_name).st_size,
                "type": "nmdc:DataObject",
                "data_object_type": product_record['data_object_type'],
                "md5_checksum": md5,
                "url": self._get_url(informed_by, act_id, fname)
            }
            output_dos.append(do)
            output_ids.append(id)

        # Generate Activity
        name = job.activity_templ["name"].replace("{id}", act_id)
        act = {
            "has_input": [],
            "git_url": job.conf['git_repo'],
            "version": job.conf['release'],
            "has_output": output_ids,
            "was_informed_by": informed_by,
            "id": act_id,
            "execution_resource": self.config.conf['resource'],
            "name": name,
            "started_at_time": job.start,
            "type": job.activity_templ["type"],
            "ended_at_time": job.end
        }
        for k, v in job.activity_templ.items():
            if v.startswith('{outputs.'):
                out_key = f"{prefix}.{v[9:-1]}"
                if out_key not in job_outs:
                    ele = out_key.split(".")
                    map_name = ".".join(ele[0:-1])
                    key_name = ele[-1]
                    act[k] = job_outs[map_name][key_name]
                else:
                    act[k] = job_outs[out_key]

        # Add input object IDs
        for dobj in job.input_data_objects:
            act["has_input"].append(dobj['id'])

        metadata_file = os.path.join(outdir, "metadata.json")
        if not os.path.exists(metadata_file):
            json.dump(metadata, open(metadata_file, "w"))

        obj['data_object_set'] = output_dos
        act_set = job.conf['activity_set']
        obj[act_set] = [act]
        objf = os.path.join(outdir, "object.json")
        json.dump(obj, open(objf, "w"))
        resp = self.nmdc.post_objects(obj)
        logger.info("response: " + str(resp))
        job.done = True
        resp = self.nmdc.update_op(job.opid, done=True,
                                   meta=metadata)
        return resp

    def post_job_done(self, job):
        # Prepare the result record
        logger.info("Running post for op %s" % (job.opid))
        md = job.get_metadata()
        dd = self.config.get_data_dir()
        obj = dict()
        informed_by = job.conf["was_informed_by"]
        subdir = os.path.join(informed_by, job.activity_id)
        outdir = os.path.join(dd, subdir)
        if not os.path.exists(outdir):
            os.makedirs(outdir)
        for k, v in md['outputs'].items():
            np = os.path.join(outdir, os.path.basename(v))
            if k.endswith("objects"):
                obj = json.load(open(v))
                # TODO Move this into the workflow
                self.fix_urls(obj['data_object_set'], informed_by,
                              job.activity_id)
                if not os.path.exists(np):
                    json.dump(obj, open(np, "w"))
            else:
                if os.path.exists(np):
                    logger.warning(f"Skipping output {np} already exist")
                    continue
                shutil.copyfile(v, np)
        mdf = os.path.join(outdir, "metadata.json")
        if not os.path.exists(mdf):
            json.dump(md, open(mdf, "w"))
        resp = self.nmdc.post_objects(obj)
        logger.info("response: " + str(resp))
        job.done = True
        resp = self.nmdc.update_op(job.opid, done=True,
                                   meta=md)
        return resp

    def check_status(self):
        for job in self.jobs:
            if job.done:
                continue
            status = job.check_status()
            if status == 'Succeeded' and job.opid and not job.done:
                if job.outputs:
                    self.post_job_done_new(job)
                else:
                    self.post_job_done(job)
                self.job_checkpoint()
            elif status == 'Failed' and job.opid:
                if job.failed_count < self._MAX_FAILS:
                    job.failed_count += 1
                    job.cromwell_submit()
                self.job_checkpoint()
            elif job.opid and not job.done:
                continue
            
        