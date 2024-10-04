#!/usr/bin/env python

from time import sleep
import os
import json
import logging
import shutil
from json import loads
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple

from nmdc_schema.nmdc import Database
from nmdc_automation.api import NmdcRuntimeApi
from nmdc_automation.config import SiteConfig
from .wfutils import WorkflowJob
from .wfutils import  _md5


DEFAULT_STATE_DIR = Path(__file__).parent / "_state"
logger = logging.getLogger(__name__)


class FileHandler:
    def __init__(self, config: SiteConfig, state_file: Union[str, Path] = None):
        """ Initialize the FileHandler, with a Config object and an optional state file path """
        self.config = config
        self._state_file = None
        # set state file
        if state_file:
            self._state_file = Path(state_file)
        elif self.config.agent_state:
            self._state_file = Path(self.config.agent_state)
        else:
            # default state file - create if it doesn't exist
            self._state_file = DEFAULT_STATE_DIR / "state.json"
            if not self._state_file.exists():
                self._state_file.touch()

    @property
    def state_file(self):
        return self._state_file

    @state_file.setter
    def state_file(self, value):
        self._state_file = value

    def read_state(self)-> Optional[Dict[str, Any]]:
        with open(self.state_file, "r") as f:
            return loads(f.read())

    def write_state(self, data):
        # normalize "id" used in database job records to "nmdc_jobid"
        for job in data["jobs"]:
            if "id" in job:
                job["nmdc_jobid"] = job.pop("id")
        with open(self.state_file, "w") as f:
            json.dump(data, f, indent=2)

    def get_output_path(self, job) -> Path:
        # construct path from string components
        output_path = Path(self.config.data_dir) / job.was_informed_by / job.workflow_execution_id
        return output_path

    def write_metadata_if_not_exists(self, job: WorkflowJob, output_path: Path):
        metadata_filepath = output_path / "metadata.json"
        if not metadata_filepath.exists():
            with open(metadata_filepath, "w") as f:
                json.dump(job.job.metadata, f)


class JobManager:
    def __init__(self, config, file_handler, api_handler):
        self.config = config
        self.file_handler = file_handler
        self.api_handler = api_handler
        self.job_cache = []
        self._MAX_FAILS = 2

    def restore_jobs(self, state_data: Dict[str, Any], nocheck=False)-> None:
        """ Restore jobs from state data """
        self.job_cache = self._find_jobs(state_data, nocheck)

    def _find_jobs(self, state_data: dict, nocheck: bool)-> List[WorkflowJob]:
        """ Find jobs from state data """
        new_wf_job_list = []
        seen = {}
        for job in state_data["jobs"]:
            job_id = job["nmdc_jobid"]
            if job_id in seen:
                continue
            wf_job = WorkflowJob(self.config, workflow_state=job)
            new_wf_job_list.append(wf_job)
            seen[job_id] = True
        return new_wf_job_list

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
        return next((job for job in self.job_cache if job.opid == opid), None)

    def prepare_and_cache_new_job(self, new_job: WorkflowJob, opid: str, force=False)-> Optional[WorkflowJob]:

        if "object_id_latest" in new_job.workflow.config:
            logger.warning("Old record. Skipping.")
            return
        existing_job = self.find_job_by_opid(opid)
        if not existing_job:
            new_job.set_opid(opid, force=force)
            self.job_cache.append(new_job)
            return new_job
        elif force:
            self.job_cache.remove(existing_job)
            new_job.set_opid(opid, force=force)
            self.job_cache.append(new_job)
            return new_job

    def get_or_create_workflow_job(self, new_job, opid, common_workflow_id)-> WorkflowJob:
        wf_job = self.find_job_by_opid(opid)
        if not wf_job:
            wf_job = WorkflowJob()
        return wf_job

    def get_finished_jobs(self)->Tuple[List[WorkflowJob], List[WorkflowJob]]:
        successful_jobs = []
        failed_jobs = []
        for job in self.job_cache:
            if not job.done:
                status = job.job_status
                if status == "Succeeded" and job.opid:
                    successful_jobs.append(job)
                elif status == "Failed" and job.opid:
                    failed_jobs.append(job)
        return (successful_jobs, failed_jobs)

    def process_successful_job(self, job: WorkflowJob):
        logger.info(f"Running post for op {job.opid}")

        output_path = self.file_handler.get_output_path(job)
        if not output_path.exists():
            output_path.mkdir(parents=True, exist_ok=True)

        database = Database()

        data_objects = job.make_data_objects(output_dir=output_path)
        database.data_object_set = data_objects
        workflow_execution_record = job.make_workflow_execution_record(data_objects)
        database.workflow_execution_set = [workflow_execution_record]

        self.file_handler.write_metadata_if_not_exists(job, output_path)

        nmdc_database_obj_dict = json.loads(database.json(exclude_unset=True))
        resp = self.api_handler.post_objects(nmdc_database_obj_dict)
        logger.info(f"Response: {resp}")
        job.done = True
        resp = self.api_handler.update_op(
            job.opid, done=True, meta=job.job.metadata
        )
        return resp


    def process_failed_job(self, job):
        if job.failed_count < self._MAX_FAILS:
            job.failed_count += 1
            job.cromwell_submit()

    def job_checkpoint(self):
        jobs = [wfjob.workflow.state for wfjob in self.job_cache]
        data = {"jobs": jobs}
        return data


    def generate_data_objects_l(self, job, outdir, schema):
        output_ids = []
        prefix = job.workflow_config["input_prefix"]

        job_outs = job.get_cromwell_metadata()["outputs"]
        informed_by = job.workflow_config["was_informed_by"]

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
            file_url = self._get_url(
                job.workflow_config["was_informed_by"],
                job.activity_id,
                file_name
            )
            id = product_record["id"]
            schema.make_data_object(
                name=file_name,
                full_file_name=full_name,
                file_url=file_url,
                data_object_type=product_record["data_object_type"],
                dobj_id=product_record["id"],
                md5_sum=md5,
                description=product_record["description"],
                omics_id=job.activity_id,
            )

            output_ids.append(id)

        return output_ids

    def create_activity_record(self, job,  output_ids, schema):
        activity_type = job.execution_template["type"]
        name = job.execution_template["name"].replace("{id}", job.activity_id)
        omic_id = job.workflow_config["was_informed_by"]
        resource = self.config.resource
        schema.create_activity_record(
            activity_record=activity_type,
            activity_name=name,
            workflow=job.workflow_config,
            activity_id=job.activity_id,
            resource=resource,
            has_inputs_list=[dobj["id"] for dobj in job.input_data_objects],
            has_output_list=output_ids,
            omic_id=omic_id,
            start_time=job.start,
            end_time=job.end,
        )


class RuntimeApiHandler:
    def __init__(self, config):
        self.runtime_api = NmdcRuntimeApi(config)
        self.config = config

    def claim_job(self, job_id):
        return self.runtime_api.claim_job(job_id)

    def get_unclaimed_jobs(self, allowed_workflows)-> List[WorkflowJob]:
        jobs = []
        filt = {
            "workflow.id": {"$in": allowed_workflows},
            "claims": {"$size": 0}
        }
        job_records =  self.runtime_api.list_jobs(filt=filt)

        for job in job_records:
            jobs.append(WorkflowJob(self.config, job))

        return jobs

    def post_objects(self, database_obj):
        return self.runtime_api.post_objects(database_obj)

    def update_op(self, opid, done, meta):
        return self.runtime_api.update_op(opid, done=done, meta=meta)


class Watcher:
    def __init__(self, site_configuration_file: Union[str, Path],  state_file: Union[str, Path] = None):
        self._POLL = 20
        self._MAX_FAILS = 2
        self.should_skip_claim = False
        self.config = SiteConfig(site_configuration_file)
        if not state_file:
            if self.config.agent_state:
                state_file = self.config.agent_state
            else:
                state_file = DEFAULT_STATE_DIR / "state.json"
        self.file_handler = FileHandler(self.config, state_file)
        self.runtime_api_handler = RuntimeApiHandler(self.config)
        self.job_manager = JobManager(self.config, self.file_handler, self.runtime_api_handler)

    def restore_from_checkpoint(self, nocheck: bool = False)-> None:
        """
        Restore from checkpoint
        """
        state_data = self.file_handler.read_state()
        if state_data:
            self.job_manager.restore_jobs(state_data, nocheck=nocheck)

    def cycle(self):
        self.restore_from_checkpoint()
        if not self.should_skip_claim:
            unclaimed_jobs = self.runtime_api_handler.get_unclaimed_jobs(self.config.allowed_workflows)
            self.claim_jobs(unclaimed_jobs)

        successful_jobs, failed_jobs = self.job_manager.get_finished_jobs()
        for job in successful_jobs:
            self.job_manager.process_successful_job(job)
        for job in failed_jobs:
            self.job_manager.process_failed_job(job)

    def watch(self):
        logger.info("Entering polling loop")
        while True:
            try:
                self.cycle()
            except (IOError, ValueError, TypeError, AttributeError) as e:
                logger.exception(f"Error occurred during cycle: {e}", exc_info=True)
            sleep(self._POLL)


    def claim_jobs(self, unclaimed_jobs: List[WorkflowJob] = None):
        # unclaimed_jobs = self.runtime_api_handler.get_unclaimed_jobs(self.config.allowed_workflows)
        for job in unclaimed_jobs:
            claim = self.runtime_api_handler.claim_job(job.workflow.nmdc_job_id)
            opid = claim["detail"]["id"]
            new_job = self.job_manager.prepare_and_cache_new_job(job, opid)
            if new_job:
                new_job.job.submit_job()
        self.file_handler.write_state(self.job_manager.job_checkpoint())
