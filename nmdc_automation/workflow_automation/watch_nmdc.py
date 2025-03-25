#!/usr/bin/env python
import sys
from time import sleep
import json
import logging
from json import loads
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple
from linkml_runtime.dumpers import yaml_dumper
import yaml
import linkml.validator
import importlib.resources
from functools import lru_cache
import traceback
import os

from nmdc_schema.nmdc import Database
from nmdc_automation.api import NmdcRuntimeApi
from nmdc_automation.config import SiteConfig
from nmdc_automation.workflow_automation.wfutils import WorkflowJob

from jaws_client import api as jaws_api
from jaws_client.config import Configuration as jaws_Configuration

DEFAULT_STATE_DIR = Path(__file__).parent / "_state"
DEFAULT_STATE_FILE = DEFAULT_STATE_DIR / "state.json"
INITIAL_STATE = {"jobs": []}

logging_level = os.getenv("NMDC_LOG_LEVEL", logging.INFO)
logging.basicConfig(
    level=logging_level, format="%(asctime)s %(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)


class FileHandler:
    """ FileHandler class for managing state and metadata files """
    def __init__(self, config: SiteConfig, state_file: Union[str, Path] = None):
        """ Initialize the FileHandler, with a Config object and an optional state file path """
        self.config = config
        self._state_file = None
        # set state file
        if state_file:
            logger.info(f"Initializing FileHandler with state file: {state_file}")
            self._state_file = Path(state_file)
        elif self.config.agent_state:
            logger.info(f"Using state file from config: {self.config.agent_state}")
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
            logger.info(f"Using default state file: {DEFAULT_STATE_FILE}")
            self._state_file = DEFAULT_STATE_FILE

    @property
    def state_file(self) -> Path:
        """ Get the state file path """
        return self._state_file

    @state_file.setter
    def state_file(self, value) -> None:
        """ Set the state file path """
        self._state_file = value

    def read_state(self) -> Optional[Dict[str, Any]]:
        """ Read the state file and return the data """
        with open(self.state_file, "r") as f:
            state = loads(f.read())
        return state

    def write_state(self, data) -> None:
        """ Write data to the state file """
        # normalize "id" used in database job records to "nmdc_jobid"
        job_count = 0
        for job in data["jobs"]:
            job_count += 1
            if "id" in job:
                job["nmdc_jobid"] = job.pop("id")

        logger.debug(f"Writing state to {self.state_file} - updating {job_count} jobs")
        with open(self.state_file, "w") as f:
            json.dump(data, f, indent=2)

    def get_output_path(self, job: WorkflowJob) -> Path:
        """ Get the output path for a job """
        # construct path from string components
        output_path = Path(self.config.data_dir) / job.was_informed_by / job.workflow_execution_id
        return output_path

    def write_metadata_if_not_exists(self, job: WorkflowJob)->Path:
        """ Write metadata to a file if it doesn't exist """
        metadata_filepath = self.get_output_path(job) / "metadata.json"
        # make sure the parent directories exist
        metadata_filepath.parent.mkdir(parents=True, exist_ok=True)
        if not metadata_filepath.exists():
            logger.debug(f"Writing metadata to {metadata_filepath}")
            with open(metadata_filepath, "w") as f:
                json.dump(job.job.metadata, f)

        return metadata_filepath


class JobManager:
    """ JobManager class for managing WorkflowJob objects """
    def __init__(self, config: SiteConfig, file_handler: FileHandler, init_cache: bool = True, jaws_api=None):
        """ Initialize the JobManager with a Config object and a FileHandler object """
        self.config = config
        self.file_handler = file_handler
        self.jaws_api = jaws_api
        self._job_cache = []
        self._MAX_FAILS = 2
        if init_cache:
            self.restore_from_state()

    @property
    def job_cache(self)-> List[WorkflowJob]:
        """ Get the job cache """
        return self._job_cache

    @job_cache.setter
    def job_cache(self, value) -> None:
        """ Set the job cache """
        self._job_cache = value

    def job_checkpoint(self) -> Dict[str, Any]:
        """ Get the state data for all jobs """
        jobs = [wfjob.workflow.state for wfjob in self.job_cache]
        data = {"jobs": jobs}
        return data

    def save_checkpoint(self) -> None:
        """ Save jobs to state data """
        data = self.job_checkpoint()
        self.file_handler.write_state(data)

    def restore_from_state(self) -> None:
        """ Restore jobs from state data """
        new_jobs = self.get_new_workflow_jobs_from_state()
        # Summarize wf_job_list by last_status
        status_count = {}
        for job in new_jobs:
            status = job.workflow.last_status
            status_count[status] = status_count.get(status, 0) + 1
        for status, count in status_count.items():
            logger.info(f"Status '{status}': {count} job(s)")
            
        if new_jobs:
            logger.info(f"Adding {len(new_jobs)} new jobs from state file.")
            self.job_cache.extend(new_jobs)

    def get_new_workflow_jobs_from_state(self) -> List[WorkflowJob]:
        """ Find new jobs from state data that are not already in the job cache """
        wf_job_list = []
        job_cache_ids = [job.opid for job in self.job_cache]
        state = self.file_handler.read_state()

        for job in state["jobs"]:
            if job.get("opid") and job.get("opid") in job_cache_ids:
                # already in cache
                continue
            wf_job = WorkflowJob(self.config, workflow_state=job, jaws_api=self.jaws_api)
            logger.info(f"Job from State: {wf_job.was_informed_by} / {wf_job.workflow_execution_id}, Last Status: {wf_job.workflow.last_status} /{wf_job.opid} / {wf_job.workflow.nmdc_jobid}")
            job_cache_ids.append(wf_job.opid)
            wf_job_list.append(wf_job)

        return wf_job_list

    def find_job_by_opid(self, opid) -> Optional[WorkflowJob]:
        """ Find a job by operation id """
        return next((job for job in self.job_cache if job.opid == opid), None)

    def prepare_and_cache_new_job(self, new_job: WorkflowJob, opid: str, force=False)-> Optional[WorkflowJob]:
        """
        Prepare and cache a new job, if it doesn't already exist by opid.
        The job can be forced to replace an existing job.
        """
        if "object_id_latest" in new_job.workflow.config:
            logger.warning("Old record. Skipping.")
            return
        existing_job = self.find_job_by_opid(opid)
        if not existing_job:
            logger.info(f"Prepare and cache new job: {opid}")
            new_job.set_opid(opid, force=force)
            new_job.done = False
            self.job_cache.append(new_job)
            return new_job
        elif force:
            logger.info(f"Replacing existing job: {existing_job.opid} with new job: {opid}")
            self.job_cache.remove(existing_job)
            new_job.set_opid(opid, force=force)
            new_job.done = False
            self.job_cache.append(new_job)
            return new_job

    def get_finished_jobs(self)->Tuple[List[WorkflowJob], List[WorkflowJob]]:
        """
        Get finished jobs
        Returns a tuple of successful jobs and failed jobs.
        Jobs are considered finished if they have a last status of "Succeeded" or "Failed"
        or if they have reached the maximum number of failures

        Unfinished jobs are checked for status and updated if needed.
        A checkpoint is saved after checking for finished jobs.
        """
        successful_jobs = []
        failed_jobs = []
        for job in self.job_cache:
            if not job.done:
                if job.workflow.last_status.lower() == "succeeded" and job.opid:
                    successful_jobs.append(job)
                    continue
                if job.workflow.last_status.lower() == "failed" and job.workflow.failed_count >= self._MAX_FAILS:
                    failed_jobs.append(job)
                    continue
                # check status
                status = job.job.get_job_status()

                if status.lower() == "succeded":
                    job.workflow.last_status = status
                    successful_jobs.append(job)
                    continue
                elif status.lower() == "failed":
                    job.workflow.last_status = status
                    job.workflow.failed_count += 1
                    failed_jobs.append(job)
                    continue
                else:
                    job.workflow.last_status = status
                    logger.debug(f"Job {job.opid} status: {status}")
        self.save_checkpoint()

        if successful_jobs:
            logger.info(f"Found {len(successful_jobs)} successful jobs.")
        if failed_jobs:
            logger.info(f"Found {len(failed_jobs)} failed jobs.")
        return successful_jobs, failed_jobs

    def process_successful_job(self, job: WorkflowJob) -> Database:
        """ Process a successful job and return a Database object """
        output_path = self.file_handler.get_output_path(job)
        if not output_path.exists():
            output_path.mkdir(parents=True, exist_ok=True)

        database = Database()

        # Update the job metadata
        logger.info(f"Create Data Objects: for {job.was_informed_by} job{job.opid} : {job.workflow.job_runner_id}")
        job.job.job_id = job.workflow.job_runner_id
        metadata = job.job.get_job_metadata()
        job.job.metadata = metadata

        data_objects = job.make_data_objects(output_dir=output_path)
        if not data_objects:
            logger.error(f"No data objects found for job {job.opid}.")
            return database

        logger.info(f"Found {len(data_objects)} data objects for job {job.opid}")
        database.data_object_set = data_objects
        try:
            workflow_execution = job.make_workflow_execution(data_objects)
        except Exception as e:
            trace = traceback.format_exc()
            logger.error(f"Error creating workflow execution: {e} for job {job.opid}")
            logger.error(trace)
            # exit early if there is an error
            sys.exit(1)
        database.workflow_execution_set = [workflow_execution]
        logger.info(f"Created workflow execution record for job {job.opid}")

        job.done = True
        job.workflow.state["end"] = workflow_execution.ended_at_time
        self.file_handler.write_metadata_if_not_exists(job)
        self.save_checkpoint()
        return database

    def process_failed_job(self, job: WorkflowJob) -> Optional[str]:
        """ Process a failed job """
        if job.workflow.state.get("failed_count", 0) >= self._MAX_FAILS:
            logger.error(f"Job {job.opid} failed {self._MAX_FAILS} times. Skipping.")
            job.done = True
            self.save_checkpoint()
            return
        job.workflow.state["failed_count"] = job.workflow.state.get("failed_count", 0) + 1
        job.workflow.state["last_status"] = job.job_status
        self.save_checkpoint()
        logger.warning(f"Job {job.opid} failed {job.workflow.state['failed_count']} times. Retrying.")
        jobid = job.job.submit_job()
        return jobid


class RuntimeApiHandler:
    """ RuntimeApiHandler class for managing API calls to the runtime """
    def __init__(self, config, jaws_api=None):
        self.runtime_api = NmdcRuntimeApi(config)
        self.config = config
        self.jaws_api = jaws_api

    def claim_job(self, job_id):
        """ Claim a job by its ID """
        return self.runtime_api.claim_job(job_id)

    def get_unclaimed_jobs(self, allowed_workflows) -> List[WorkflowJob]:
        """ Get unclaimed jobs from the runtime """
        jobs = []
        filt = {
            "workflow.id": {"$in": allowed_workflows},
            "claims": {"$size": 0}
        }
        job_records = self.runtime_api.list_jobs(filt=filt)

        for job in job_records:
            jobs.append(WorkflowJob(self.config, workflow_state=job, jaws_api=self.jaws_api))

        return jobs

    def post_objects(self, database_obj):
        """ Post a Database with workflow executions and their data objects to the workflow_executions endpoint """
        return self.runtime_api.post_workflow_executions(database_obj)

    def update_operation(self, opid, done, meta):
        """ Update the state of an operation with new metadata, results, and done status """
        return self.runtime_api.update_op(opid, done=done, meta=meta)


class Watcher:
    """ Watcher class for monitoring and managing jobs """
    def __init__(self, site_configuration_file: Union[str, Path],  state_file: Union[str, Path] = None, use_jaws: bool = False):
        self._POLL_INTERVAL_SEC = 60
        self._MAX_FAILS = 2
        self.should_skip_claim = False
        self.config = SiteConfig(site_configuration_file)
        self.file_handler = FileHandler(self.config, state_file)

        if use_jaws:
            jaws_config = jaws_Configuration.from_files(self.config.jaws_config, self.config.jaws_token)
            self.jaws_api = jaws_api.JawsApi(jaws_config)
        else:
            self.jaws_api = None


        self.runtime_api_handler = RuntimeApiHandler(self.config, self.jaws_api)
        self.job_manager = JobManager(self.config, self.file_handler, jaws_api=self.jaws_api)
        self.nmdc_materialized = _get_nmdc_materialized()

    def restore_from_checkpoint(self, state_data: Dict[str, Any] = None)-> None:
        """
        Restore from checkpoint
        """
        if state_data:
            self.file_handler.write_state(state_data)
        self.job_manager.restore_from_state()


    def cycle(self):
        """ Perform a cycle of watching for unclaimed jobs, claiming jobs,  and processing finished jobs """
        self.restore_from_checkpoint()
        # if not self.should_skip_claim: - is this actually used?
        unclaimed_jobs = self.runtime_api_handler.get_unclaimed_jobs(self.config.allowed_workflows)
        if unclaimed_jobs:
            logger.info(f"Found {len(unclaimed_jobs)} unclaimed jobs.")
        self.claim_jobs(unclaimed_jobs)


        logger.debug(f"Checking for finished jobs.")
        successful_jobs, failed_jobs = self.job_manager.get_finished_jobs()
        if not successful_jobs and not failed_jobs:
            logger.debug("No finished jobs found.")
        for job in successful_jobs:
            logger.info(f"Processing successful job: {job.opid}, {job.was_informed_by} {job.workflow_execution_id}")
            job_database = self.job_manager.process_successful_job(job)
            # sanity checks
            if not job_database.data_object_set:
                logger.error(f"No data objects found for job {job.opid}.")
                continue

            job_dict = yaml.safe_load(yaml_dumper.dumps(job_database))
            # validate the database object against the schema
            validation_report = linkml.validator.validate(
                job_dict, self.nmdc_materialized, "Database"
            )
            if validation_report.results:
                logger.error(f"Validation error: {validation_report.results[0].message}")
                logger.error(f"job_dict: {job_dict}")
                continue
            else:
                logger.info(f"Database object validated for job {job.opid}")

            # post workflow execution and data objects to the runtime api
            resp = self.runtime_api_handler.post_objects(job_dict)
            logger.info(f"Posted Workflow Execution and Data Objects to database: {job.was_informed_by} "
                        f"{job.workflow_execution_id}")

            # update the operation record
            resp = self.runtime_api_handler.update_operation(
                job.opid, done=True, meta=job.job.metadata
            )
            logging.info(f"Updated operation {job.opid} response id: {resp['id']}")

        for job in failed_jobs:
            logger.info(f"Processing failed job: {job.opid}, {job.workflow_execution_id}")
            self.job_manager.process_failed_job(job)

    def watch(self):
        """ Maintain a polling loop to 'cycle' through job claims and processing """
        logger.info("Entering polling loop")
        while True:
            try:
                self.cycle()
            except (IOError, ValueError, TypeError, AttributeError) as e:
                logger.exception(f"Error occurred during cycle: {e}", exc_info=True)
            sleep(self._POLL_INTERVAL_SEC)

    def claim_jobs(self, unclaimed_jobs: List[WorkflowJob] = None) -> None:
        """ Claim unclaimed jobs, prepare them, and submit them. Write a checkpoint after claiming jobs. """
        for job in unclaimed_jobs:
            logger.info(f"Claiming job {job.workflow.nmdc_jobid}")
            claim = self.runtime_api_handler.claim_job(job.workflow.nmdc_jobid)
            opid = claim["id"]
            new_job = self.job_manager.prepare_and_cache_new_job(job, opid)
            if new_job:
                new_job.job.submit_job()
        self.file_handler.write_state(self.job_manager.job_checkpoint())

@lru_cache(maxsize=None)
def _get_nmdc_materialized():
    with importlib.resources.open_text("nmdc_schema", "nmdc_materialized_patterns.yaml") as f:
        return yaml.safe_load(f)