#!/usr/bin/env python

from time import sleep
import os
import json
import logging
import shutil
from json import loads
from os.path import exists
from nmdc_automation.api.nmdcapi import nmdcapi
from nmdc_automation.workflow_automation.config import config
from nmdc_automation.workflow_automation.wfutils import _md5
from nmdc_automation.workflow_automation.wfutils import WorkflowJob as wfjob
from nmdc_automation.workflow_automation.wfutils import NmdcSchema

logger = logging.getLogger(__name__)


class Watcher:
    def __init__(self, site_configuration_file):
        self._POLL = 20
        self._MAX_FAILS = 2
        self.should_skip_claim = False
        self.config = config(site_configuration_file)
        self.client_id = self.config.conf['credentials']['client_id']
        self.client_secret = self.config.conf['credentials']['client_secret']
        self.cromurl = self.config.conf['cromwell']['cromwell_url']
        self.state_file = self.config.conf['state']['agent_state']
        self.stage_dir = self.config.get_stage_dir()
        self.raw_dir = self.config.conf['directories']['raw_dir']
        self.jobs = []
        self.runtime_api = nmdcapi()
        self._ALLOWED = self.config._generate_allowed_workflows()

    def restore(self, nocheck: bool = False):
        """
        Restore from checkpoint
        """
        data = self._load_state_file()
        if not data:
            return

        self.jobs = self._find_jobs(data, nocheck)

    def _load_state_file(self):
        if not exists(self.state_file):
            return
        with open(self.state_file, 'r') as f:
            return loads(f.read())

    def _find_jobs(self, data: dict, nocheck: bool):
        new_job_list = []
        seen = {}
        for job in data['jobs']:
            job_id = job['nmdc_jobid']
            if job_id in seen:
                continue
            job_record = wfjob(self.config.conf, state=job, nocheck=nocheck)
            new_job_list.append(job_record)
            seen[job_id] = True

        return new_job_list
    #################################

    def job_checkpoint(self):
        jobs = [job.get_state() for job in self.jobs]
        data = {'jobs': jobs}
        with open(self.state_file, "w") as f:
            json.dump(data, f, indent=2)

    def cycle(self):
        self.restore()
        if not self.should_skip_claim:
            self.claim_jobs()
        self.check_status()

    def watch(self):
        logger.info("Entering polling loop")
        while True:
            try:
                self.cycle()
            except (IOError, ValueError, TypeError, AttributeError) as e:
                logger.exception(f"Error occurred during cycle: {e}",
                                 exc_info=True)
            sleep(self._POLL)

    def find_job_by_opid(self, opid):
        return next((job for job in self.jobs if job.opid == opid), None)

    def submit(self, new_job, opid, force=False):
        common_workflow_id = new_job['workflow']['id']
        if 'object_id_latest' in new_job['config']:
            logger.warning("Old record. Skipping.")
            return
        self.create_or_use_existing_job(new_job, opid, common_workflow_id)
        self.jobs[-1].cromwell_submit(force=force)

    def create_or_use_existing_job(self, new_job, opid, common_workflow_id):
        job = self.find_job_by_opid(opid)
        if job:
            logger.debug("Previously cached job")
            logger.info(f"Reusing activity {job.activity_id}")
            print("PREVIOUSLY USED JOB")
            self.jobs.append(job)
        else:
            print("NEW JOB")
            logging.debug(new_job)
            job = wfjob(site_config=self.config.conf,
                        typ=common_workflow_id,
                        nmdc_jobid=new_job['id'],
                        workflow_config=new_job['config'],
                        opid=opid,
                        activity_id=new_job['config']['activity_id'])
            self.jobs.append(job)

    def refresh_remote_jobs(self):
        """
        Return a filtered list of nmdc jobs.
        """
        filt = {"workflow.id": {"$in": self._ALLOWED}}
        print("Looking for jobs")
        jobs = self.runtime_api.list_jobs(filt=filt)
        print("Found jobs")
        known = set(job.nmdc_jobid for job in self.jobs)
        return [job for job in jobs if job['id'] not in known]

    def claim_jobs(self):
        for job in self.refresh_remote_jobs():
            job_id = job['id']
            if job.get('claims') and len(job.get('claims')) > 0:
                continue
            logger.debug(f"Trying to claim: {job_id}")

            # Claim job
            claim = self.runtime_api.claim_job(job_id)
            if not claim['claimed']:
                logger.debug(claim)
                self.submit_and_checkpoint_job(job, claim['id'])
            else:
                # Previously claimed
                opid = claim['detail']['id']
                logger.info("Previously claimed.")
                self.submit_and_checkpoint_job(job, opid)

    def submit_and_checkpoint_job(self, job, opid):
        self.submit(job, opid)
        self.job_checkpoint()

    def _load_json(self, file_name):
        return json.loads(open(file_name).read())

    def fix_urls(self, data_object_list, actid, subdir):
        root = self.config.conf['nmdc']['url_root']
        for data_object in data_object_list:
            file_name = data_object['url'].split('/')[-1]
            new_url = f"{root}/{actid}/{subdir}/{file_name}"
            data_object['url'] = new_url

    def _get_url(self, informed_by, act_id, fname):
        root = self.config.conf['nmdc']['url_root']
        return f"{root}/{informed_by}/{act_id}/{fname}"

    def _get_output_dir(self, informed_by, act_id):
        data_directory = self.config.get_data_dir()
        outdir = os.path.join(data_directory, informed_by, act_id)
        if not os.path.exists(outdir):
            os.makedirs(outdir)
        return outdir

    def post_job_done(self, job):
        logger.info(f"Running post for op {job.opid}")
        metadata = job.get_metadata()
        informed_by = job.workflow_config["was_informed_by"]
        act_id = job.activity_id
        outdir = self._get_output_dir(informed_by, act_id)
        schema = NmdcSchema()

        output_ids = self.generate_data_objects(job, metadata['outputs'],
                                                outdir, informed_by, act_id,
                                                schema)
        activity_inputs = [dobj['id'] for dobj in job.input_data_objects]

        self.create_activity_record(job, act_id, activity_inputs,
                                    output_ids, schema)

        self.write_metadata_if_not_exists(metadata, outdir)

        nmdc_database_obj = schema.get_database_object_dump()
        nmdc_database_obj_dict = json.loads(nmdc_database_obj)
        resp = self.runtime_api.post_objects(nmdc_database_obj_dict)
        logger.info(f"Response: {resp}")

        job.done = True
        resp = self.runtime_api.update_op(job.opid, done=True, meta=metadata)

        return resp

    def generate_data_objects(self, job, job_outs, outdir,
                              informed_by, act_id, schema):
        output_ids = []
        prefix = job.workflow_config['input_prefix']

        for product_record in job.outputs:
            outkey = f"{prefix}.{product_record['output']}"
            full_name = job_outs[outkey]
            file_name = os.path.basename(full_name)
            new_path = os.path.join(outdir, file_name)
            shutil.copyfile(full_name, new_path)

            md5 = _md5(full_name)
            file_url = self._get_url(informed_by, act_id, file_name)
            id = product_record["id"]
            schema.make_data_object(name=product_record['name'],
                                    full_file_name=full_name,
                                    file_url=file_url,
                                    data_object_type=product_record['data_object_type'],
                                    dobj_id=product_record['id'],
                                    md5_sum=md5,
                                    description=product_record['description'],
                                    omics_id=act_id)

            output_ids.append(id)

        return output_ids

    def create_activity_record(self, job, act_id, activity_inputs,
                               output_ids, schema):
        activity_type = job.activity_templ["type"]
        name = job.activity_templ["name"].replace("{id}", act_id)
        omic_id = job.workflow_config['was_informed_by']
        resource = self.config.conf['site']['resource']
        schema.create_activity_record(activity_record=activity_type,
                                      activity_name=name,
                                      workflow=job.workflow_config,
                                      activity_id=act_id,
                                      resource=resource,
                                      has_inputs_list=activity_inputs,
                                      has_output_list=output_ids,
                                      omic_id=omic_id,
                                      start_time=job.start,
                                      end_time=job.end)

    def process_job_outputs(self, job, metadata, outdir):
        obj = dict()
        for key, value in metadata['outputs'].items():
            new_path = os.path.join(outdir, os.path.basename(value))
            if key.endswith("objects"):
                with open(value) as f:
                    obj = json.load(f)

                self.fix_urls(obj['data_object_set'],
                              job.workflow_config["was_informed_by"],
                              job.activity_id)

                if not os.path.exists(new_path):
                    with open(new_path, "w") as f:
                        json.dump(obj, f)
            else:
                self.copy_output_if_not_exists(value, new_path)
        return obj

    def copy_output_if_not_exists(self, old_path, new_path):
        if os.path.exists(new_path):
            logger.warning(f"Skipping output {new_path} already exists")
        else:
            shutil.copyfile(old_path, new_path)

    def write_metadata_if_not_exists(self, metadata, outdir):
        metadata_filepath = os.path.join(outdir, "metadata.json")
        if not os.path.exists(metadata_filepath):
            with open(metadata_filepath, "w") as f:
                json.dump(metadata, f)

    def check_status(self):
        for job in self.jobs:
            if not job.done:
                status = job.check_status()
                if status == 'Succeeded' and job.opid:
                    self.process_successful_job(job)
                elif status == 'Failed' and job.opid:
                    self.process_failed_job(job)

        self.job_checkpoint()

    def process_successful_job(self, job):
        self.post_job_done(job)

    def process_failed_job(self, job):
        if job.failed_count < self._MAX_FAILS:
            job.failed_count += 1
            job.cromwell_submit()
