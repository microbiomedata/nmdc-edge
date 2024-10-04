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
DEFAULT_STATE_FILE = DEFAULT_STATE_DIR / "state.json"
INITIAL_STATE = {"jobs": []}
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
            # no state file provided or set in config set up a default
            # check for a default state directory and create if it doesn't exist
            DEFAULT_STATE_DIR.mkdir(parents=True, exist_ok=True)
            DEFAULT_STATE_FILE.touch(exist_ok=True)
            # if the file is empty write the initial state
            if DEFAULT_STATE_FILE.stat().st_size == 0:
                with open(DEFAULT_STATE_FILE, "w") as f:
                    json.dump(INITIAL_STATE, f, indent=2)
            self._state_file = DEFAULT_STATE_FILE

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

    def get_output_path(self, job: WorkflowJob) -> Path:
        # construct path from string components
        output_path = Path(self.config.data_dir) / job.was_informed_by / job.workflow_execution_id
        return output_path

    def write_metadata_if_not_exists(self, job: WorkflowJob)->Path:
        metadata_filepath = self.get_output_path(job) / "metadata.json"
        # make sure the parent directories exist
        metadata_filepath.parent.mkdir(parents=True, exist_ok=True)
        if not metadata_filepath.exists():
            with open(metadata_filepath, "w") as f:
                json.dump(job.job.metadata, f)
        return metadata_filepath


class JobManager:
    def __init__(self, config, file_handler):
        self.config = config
        self.file_handler = file_handler
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


    def process_successful_job(self, job: WorkflowJob) -> Database:
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
        return database


    def process_failed_job(self, job):
        if job.failed_count < self._MAX_FAILS:
            job.failed_count += 1
            job.cromwell_submit()


    def job_checkpoint(self):
        jobs = [wfjob.workflow.state for wfjob in self.job_cache]
        data = {"jobs": jobs}
        return data


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
        self.file_handler = FileHandler(self.config, state_file)
        self.runtime_api_handler = RuntimeApiHandler(self.config)
        self.job_manager = JobManager(self.config, self.file_handler)

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
            job_database = self.job_manager.process_successful_job(job)
            job_dict = json.loads(job_database.json(exclude_unset=True))

            # post workflow execution and data objects to the runtime api
            resp = self.runtime_api_handler.post_objects(job_dict)
            if not resp.ok:
                logger.error(f"Error posting objects: {resp}")
                continue
            job.done = True
            # update the operation record
            resp = self.runtime_api_handler.update_op(
                job.opid, done=True, meta=job.job.metadata
            )
            if not resp.ok:
                logger.error(f"Error updating operation: {resp}")
                continue

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
