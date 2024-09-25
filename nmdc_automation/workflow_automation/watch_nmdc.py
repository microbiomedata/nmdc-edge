#!/usr/bin/env python

from time import sleep
import os
import json
import logging
import shutil
from json import loads
from os.path import exists
from nmdc_automation.api import NmdcRuntimeApi
from nmdc_automation.config import Config
from .wfutils import WorkflowJob as wfjob
from .wfutils import NmdcSchema, _md5

logger = logging.getLogger(__name__)


class FileHandler:
    def __init__(self, state_file):
        self.state_file = state_file

    def load_state_file(self):
        if not exists(self.state_file):
            return None
        with open(self.state_file, "r") as f:
            return loads(f.read())

    def save_state_file(self, data):
        with open(self.state_file, "w") as f:
            json.dump(data, f, indent=2)

    def get_output_dir(self, informed_by, act_id, data_directory):
        outdir = os.path.join(data_directory, informed_by, act_id)
        if not os.path.exists(outdir):
            os.makedirs(outdir)
        return outdir

    def write_metadata_if_not_exists(self, metadata, outdir):
        metadata_filepath = os.path.join(outdir, "metadata.json")
        if not os.path.exists(metadata_filepath):
            with open(metadata_filepath, "w") as f:
                json.dump(metadata, f)


class JobManager:
    def __init__(self, config, file_handler, api_handler):
        self.config = config
        self.file_handler = file_handler
        self.api_handler = api_handler
        self.jobs = []
        self._MAX_FAILS = 2

    def restore_jobs(self, state_data, nocheck=False):
        self.jobs = self._find_jobs(state_data, nocheck)

    def _find_jobs(self, data: dict, nocheck: bool):
        new_job_list = []
        seen = {}
        for job in data["jobs"]:
            job_id = job["nmdc_jobid"]
            if job_id in seen:
                continue
            job_record = wfjob(self.config, state=job, nocheck=nocheck)
            new_job_list.append(job_record)
            seen[job_id] = True
        return new_job_list

    def _get_url(self, informed_by, act_id, fname):
        root = self.config.url_root
        return f"{root}/{informed_by}/{act_id}/{fname}"

    def _get_output_dir(self, informed_by, act_id):
        data_directory = self.config.data_dir
        outdir = os.path.join(data_directory, informed_by, act_id)
        if not os.path.exists(outdir):
            os.makedirs(outdir)
        return outdir

    def find_job_by_opid(self, opid):
        return next((job for job in self.jobs if job.opid == opid), None)

    def submit_job(self, new_job, opid, force=False):
        common_workflow_id = new_job["workflow"]["id"]
        if "object_id_latest" in new_job["config"]:
            logger.warning("Old record. Skipping.")
            return
        self.create_or_use_existing_job(new_job, opid, common_workflow_id)
        self.jobs[-1].cromwell_submit(force=force)

    def create_or_use_existing_job(self, new_job, opid, common_workflow_id):
        job = self.find_job_by_opid(opid)
        if job:
            logger.debug("Previously cached job")
            self.jobs.append(job)
        else:
            job = wfjob(
                site_config=self.config,
                typ=common_workflow_id,
                nmdc_jobid=new_job["id"],
                workflow_config=new_job["config"],
                opid=opid,
                activity_id=new_job["config"]["activity_id"],
            )
            self.jobs.append(job)

    def check_job_status(self):
        for job in self.jobs:
            if not job.done:
                status = job.check_status()
                if status == "Succeeded" and job.opid:
                    self.process_successful_job(job)
                elif status == "Failed" and job.opid:
                    self.process_failed_job(job)

    def process_successful_job(self, job):
        logger.info(f"Running post for op {job.opid}")
        metadata = job.get_metadata()
        informed_by = job.workflow_config["was_informed_by"]
        act_id = job.activity_id
        outdir = self.file_handler.get_output_dir(informed_by, act_id, self.config.data_dir)
        schema = NmdcSchema()
        output_ids = self.generate_data_objects(job, metadata["outputs"], outdir, informed_by, act_id, schema)
        activity_inputs = [dobj["id"] for dobj in job.input_data_objects]
        self.create_activity_record(job, act_id, activity_inputs, output_ids, schema)
        self.file_handler.write_metadata_if_not_exists(metadata, outdir)
        nmdc_database_obj = schema.get_database_object_dump()
        nmdc_database_obj_dict = json.loads(nmdc_database_obj)
        resp = self.api_handler.post_objects(nmdc_database_obj_dict)
        logger.info(f"Response: {resp}")
        job.done = True
        resp = self.api_handler.update_op(job.opid, done=True, meta=metadata)
        return resp


    def process_failed_job(self, job):
        if job.failed_count < self._MAX_FAILS:
            job.failed_count += 1
            job.cromwell_submit()

    def job_checkpoint(self):
        jobs = [job.get_state() for job in self.jobs]
        data = {"jobs": jobs}
        return data

    def generate_data_objects(self, job, job_outs, outdir, informed_by, act_id, schema):
        output_ids = []
        prefix = job.workflow_config["input_prefix"]

        for product_record in job.outputs:
            outkey = f"{prefix}.{product_record['output']}"
            if outkey not in job_outs and product_record.get("optional"):
                logging.debug(f"Ignoring optional missing output {outkey}")
                continue

            full_name = job_outs[outkey]
            file_name = os.path.basename(full_name)
            new_path = os.path.join(outdir, file_name)
            shutil.copyfile(full_name, new_path)

            md5 = _md5(full_name)
            file_url = self._get_url(informed_by, act_id, file_name)
            id = product_record["id"]
            schema.make_data_object(
                name=file_name,
                full_file_name=full_name,
                file_url=file_url,
                data_object_type=product_record["data_object_type"],
                dobj_id=product_record["id"],
                md5_sum=md5,
                description=product_record["description"],
                omics_id=act_id,
            )

            output_ids.append(id)

        return output_ids

    def create_activity_record(self, job, act_id, activity_inputs, output_ids, schema):
        activity_type = job.activity_templ["type"]
        name = job.activity_templ["name"].replace("{id}", act_id)
        omic_id = job.workflow_config["was_informed_by"]
        resource = self.config.resource
        schema.create_activity_record(
            activity_record=activity_type,
            activity_name=name,
            workflow=job.workflow_config,
            activity_id=act_id,
            resource=resource,
            has_inputs_list=activity_inputs,
            has_output_list=output_ids,
            omic_id=omic_id,
            start_time=job.start,
            end_time=job.end,
        )


class RuntimeApiHandler:
    def __init__(self, config):
        self.runtime_api = NmdcRuntimeApi(config)

    def claim_job(self, job_id):
        return self.runtime_api.claim_job(job_id)

    def list_jobs(self, allowed_workflows):
        filt = {
            "workflow.id": {"$in": allowed_workflows},
            "claims": {"$size": 0}
        }
        return self.runtime_api.list_jobs(filt=filt)

    def post_objects(self, database_obj):
        return self.runtime_api.post_objects(database_obj)

    def update_op(self, opid, done, meta):
        return self.runtime_api.update_op(opid, done=done, meta=meta)



class Watcher:
    def __init__(self, site_configuration_file):
        self._POLL = 20
        self._MAX_FAILS = 2
        self.should_skip_claim = False
        self.config = Config(site_configuration_file)
        self.file_handler = FileHandler(self.config.agent_state)
        self.api_handler = RuntimeApiHandler(self.config)
        self.job_manager = JobManager(self.config, self.file_handler, self.api_handler)

        # TODO: make it clear that this is a list of WorkflowJob instances
        self.jobs = []
        self._ALLOWED = self.config.allowed_workflows

    def restore_from_checkpoint(self, nocheck: bool = False):
        """
        Restore from checkpoint
        """
        state_data = self.file_handler.load_state_file()
        if state_data:
            self.job_manager.restore_jobs(state_data, nocheck=nocheck)

    def cycle(self):
        self.restore_from_checkpoint()
        if not self.should_skip_claim:
            self.claim_jobs()
        self.job_manager.check_job_status()

    def watch(self):
        logger.info("Entering polling loop")
        while True:
            try:
                self.cycle()
            except (IOError, ValueError, TypeError, AttributeError) as e:
                logger.exception(f"Error occurred during cycle: {e}", exc_info=True)
            sleep(self._POLL)


    def claim_jobs(self):
        jobs = self.api_handler.list_jobs(self._ALLOWED)
        for job in jobs:
            claim = self.api_handler.claim_job(job["id"])
            opid = claim["detail"]["id"]
            self.job_manager.submit_job(job, opid)
        self.file_handler.save_state_file(self.job_manager.job_checkpoint())
