#!/usr/bin/env python

import hashlib
import json
import logging
import os
import re
import shutil
import tempfile
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from linkml_runtime.dumpers import yaml_dumper
import yaml

import pytz
import requests

from nmdc_automation.config import SiteConfig
from nmdc_automation.models.nmdc import DataObject, WorkflowExecution, workflow_process_factory

DEFAULT_MAX_RETRIES = 2


class JobRunnerABC(ABC):
    """Abstract base class for job runners"""

    @abstractmethod
    def submit_job(self) -> str:
        """ Submit a job """
        pass

    @abstractmethod
    def get_job_status(self) -> str:
        """ Get the status of a job """
        pass

    @abstractmethod
    def get_job_metadata(self) -> Dict[str, Any]:
        """ Get metadata for a job """
        pass

    @property
    @abstractmethod
    def job_id(self) -> Optional[str]:
        """ Get the job id """
        pass

    @property
    @abstractmethod
    def outputs(self) -> Dict[str, str]:
        """ Get the outputs """
        pass

    @property
    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        """ Get the metadata """
        pass

    @property
    @abstractmethod
    def max_retries(self) -> int:
        """ Get the maximum number of retries """
        pass


class CromwellRunner(JobRunnerABC):
    """Job runner for Cromwell"""
    LABEL_SUBMITTER_VALUE = "nmdcda"
    LABEL_PARAMETERS = ["release", "wdl", "git_repo"]
    # States that indicate a job is in some active state and does not need to be submitted
    NO_SUBMIT_STATES = [
        "Submitted",  # job is already submitted but not running
        "Running",  # job is already running
        "Succeeded",  # job succeeded
        "Aborting"  # job is in the process of being aborted
        "On Hold",  # job is on hold and not running. It can be manually resumed later
    ]

    def __init__(self, site_config: SiteConfig, workflow: "WorkflowStateManager", job_metadata: Dict[str, Any] = None,
                 max_retries: int = DEFAULT_MAX_RETRIES, dry_run: bool = False) -> None:
        """
        Create a Cromwell job runner.
        :param site_config: SiteConfig object
        :param workflow: WorkflowStateManager object
        :param job_metadata: metadata for the job
        :param max_retries: maximum number of retries for a job
        :param dry_run: if True, do not submit the job
        """
        self.config = site_config
        if not isinstance(workflow, WorkflowStateManager):
            raise ValueError("workflow must be a WorkflowStateManager object")
        self.workflow = workflow
        self.service_url = self.config.cromwell_url
        self._metadata = {}
        if job_metadata:
            self._metadata = job_metadata
        self._max_retries = max_retries
        self.dry_run = dry_run

    def _generate_workflow_inputs(self) -> Dict[str, str]:
        """ Generate inputs for the job runner from the workflow state """
        inputs = {}
        prefix = self.workflow.input_prefix
        for input_key, input_val in self.workflow.inputs.items():
            # special case for resource
            if input_val == "{resource}":
                input_val = self.config.resource
            inputs[f"{prefix}.{input_key}"] = input_val
        return inputs

    def _generate_workflow_labels(self) -> Dict[str, str]:
        """ Generate labels for the job runner from the workflow state """
        labels = {param: self.workflow.config[param] for param in self.LABEL_PARAMETERS}
        labels["submitter"] = self.LABEL_SUBMITTER_VALUE
        # some Cromwell-specific labels
        labels["pipeline_version"] = self.workflow.config["release"]
        labels["pipeline"] = self.workflow.config["wdl"]
        labels["activity_id"] = self.workflow.workflow_execution_id
        labels["opid"] = self.workflow.opid
        return labels

    def generate_submission_files(self) -> Dict[str, Any]:
        """ Generate the files needed for a Cromwell job submission """
        files = {}
        try:
            wdl_file = self.workflow.fetch_release_file(self.workflow.config["wdl"], suffix=".wdl")
            bundle_file = self.workflow.fetch_release_file("bundle.zip", suffix=".zip")
            files = {"workflowSource": open(wdl_file, "rb"), "workflowDependencies": open(bundle_file, "rb"),
                "workflowInputs": open(_json_tmp(self._generate_workflow_inputs()), "rb"),
                "labels": open(_json_tmp(self._generate_workflow_labels()), "rb"), }
        except Exception as e:
            logging.error(f"Failed to generate submission files: {e}")
            self._cleanup_files(list(files.values()))
            raise e
        return files

    def _cleanup_files(self, files: List[Union[tempfile.NamedTemporaryFile, tempfile.SpooledTemporaryFile]]):
        """Safely closes and removes files."""
        for file in files:
            try:
                file.close()
                os.unlink(file.name)
            except Exception as e:
                logging.error(f"Failed to cleanup file: {e}")

    def submit_job(self, force: bool = False) -> Optional[str]:
        """
        Submit a job to Cromwell. Update the workflow state with the job id and status.
        :param force: if True, submit the job even if it is in a state that does not require submission
        :return: the job id
        """
        status = self.workflow.last_status
        if status in self.NO_SUBMIT_STATES and not force:
            logging.info(f"Job {self.job_id} in state {status}, skipping submission")
            return
        cleanup_files = []
        try:
            files = self.generate_submission_files()
            cleanup_files = list(files.values())
            if not self.dry_run:
                response = requests.post(self.service_url, files=files)
                response.raise_for_status()
                self.metadata = response.json()
                self.job_id = self.metadata["id"]
                logging.info(f"Submitted job {self.job_id}")
            else:
                logging.info(f"Dry run: skipping job submission")
                self.job_id = "dry_run"

            logging.info(f"Job {self.job_id} submitted")
            start_time = datetime.now(pytz.utc).isoformat()
            # update workflow state
            self.workflow.done = False
            self.workflow.update_state({"start": start_time})
            self.workflow.update_state({"cromwell_jobid": self.job_id})
            self.workflow.update_state({"last_status": "Submitted"})
            return self.job_id
        except Exception as e:
            logging.error(f"Failed to submit job: {e}")
            raise e
        finally:
            self._cleanup_files(cleanup_files)

    def get_job_status(self) -> str:
        """ Get the status of a job from Cromwell """
        if not self.workflow.cromwell_jobid:
            return "Unknown"
        status_url = f"{self.service_url}/{self.workflow.cromwell_jobid}/status"
        # There can be a delay between submitting a job and it
        # being available in Cromwell so handle 404 errors
        logging.debug(f"Getting job status from {status_url}")
        try:
            response = requests.get(status_url)
            response.raise_for_status()
            return response.json().get("status", "Unknown")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return "Unknown"
            raise e

    def get_job_metadata(self) -> Dict[str, Any]:
        """ Get metadata for a job from Cromwell """
        metadata_url = f"{self.service_url}/{self.job_id}/metadata"
        response = requests.get(metadata_url)
        response.raise_for_status()
        metadata = response.json()
        # update cached metadata
        self.metadata = metadata
        return metadata

    @property
    def job_id(self) -> Optional[str]:
        """ Get the job id from the metadata """
        return self.metadata.get("id", None)

    @job_id.setter
    def job_id(self, job_id: str):
        """ Set the job id in the metadata """
        self.metadata["id"] = job_id

    @property
    def outputs(self) -> Dict[str, str]:
        """ Get the outputs from the metadata """
        return self.metadata.get("outputs", {})

    @property
    def metadata(self) -> Dict[str, Any]:
        """ Get the metadata """
        return self._metadata

    @metadata.setter
    def metadata(self, metadata: Dict[str, Any]):
        """ Set the metadata """
        self._metadata = metadata

    @property
    def max_retries(self) -> int:
        return self._max_retries


class WorkflowStateManager:
    CHUNK_SIZE = 1000000  # 1 MB
    GIT_RELEASES_PATH = "/releases/download"

    def __init__(self, state: Dict[str, Any] = None, opid: str = None):
        if state is None:
            state = {}
        self.cached_state = state
        if opid and "opid" in self.cached_state:
            raise ValueError("opid already set in job state")
        if opid:
            self.cached_state["opid"] = opid

    def update_state(self, state: Dict[str, Any]):
        self.cached_state.update(state)

    @property
    def state(self) -> Dict[str, Any]:
        return self.cached_state

    @property
    def config(self) -> Dict[str, Any]:
        # for backward compatibility we need to check for both keys
        return self.cached_state.get("conf", self.cached_state.get("config", {}))

    @property
    def last_status(self) -> Optional[str]:
        return self.cached_state.get("last_status", None)

    @last_status.setter
    def last_status(self, status: str):
        self.cached_state["last_status"] = status

    @property
    def failed_count(self) -> int:
        return self.cached_state.get("failed_count", 0)

    @failed_count.setter
    def failed_count(self, count: int):
        self.cached_state["failed_count"] = count

    @property
    def nmdc_jobid(self) -> Optional[str]:
        return self.cached_state.get("nmdc_jobid", None)

    @property
    def cromwell_jobid(self) -> Optional[str]:
        return self.cached_state.get("cromwell_jobid", None)

    @property
    def execution_template(self) -> Dict[str, str]:
        # for backward compatibility we need to check for both keys
        return self.config.get("workflow_execution", self.config.get("activity", {}))

    @property
    def workflow_execution_id(self) -> Optional[str]:
        # for backward compatibility we need to check for both keys
        return self.config.get("activity_id", self.config.get("workflow_execution_id", None))

    @property
    def was_informed_by(self) -> Optional[str]:
        return self.config.get("was_informed_by", None)

    @property
    def workflow_execution_type(self) -> Optional[str]:
        return self.execution_template.get("type", None)

    @property
    def workflow_execution_name(self) -> Optional[str]:
        name_base = self.execution_template.get("name", None)
        if name_base:
            return name_base.replace("{id}", self.workflow_execution_id)
        return None

    @property
    def data_outputs(self) -> List[Dict[str, str]]:
        return self.config.get("outputs", [])

    @property
    def input_prefix(self) -> Optional[str]:
        return self.config.get("input_prefix", None)

    @property
    def inputs(self) -> Dict[str, str]:
        return self.config.get("inputs", {})

    @property
    def nmdc_jobid(self) -> Optional[str]:
        # different keys in state file vs database record
        return self.cached_state.get("nmdc_jobid", self.cached_state.get("id", None))

    @property
    def job_runner_id(self) -> Optional[str]:
        # for now we only have cromwell as a job runner
        job_runner_ids = ["cromwell_jobid", ]
        for job_runner_id in job_runner_ids:
            if job_runner_id in self.cached_state:
                return self.cached_state[job_runner_id]

    @property
    def opid(self) -> Optional[str]:
        return self.cached_state.get("opid", None)

    @opid.setter
    def opid(self, opid: str):
        if self.opid:
            raise ValueError("opid already set in job state")
        self.cached_state["opid"] = opid

    def fetch_release_file(self, filename: str, suffix: str = None) -> str:
        """
        Download a release file from the Git repository and save it as a temporary file.
        Note: the temporary file is not deleted automatically.
        """
        logging.debug(f"Fetching release file: {filename}")
        url = self._build_release_url(filename)
        logging.debug(f"Fetching release file from URL: {url}")
        # download the file as a stream to handle large files
        response = requests.get(url, stream=True)
        try:
            response.raise_for_status()
            # create a named temporary file
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp_file:
                self._write_stream_to_file(response, tmp_file)
                return tmp_file.name
        finally:
            response.close()

    def _build_release_url(self, filename: str) -> str:
        """Build the URL for a release file in the Git repository."""
        logging.debug(f"Building release URL for {filename}")
        release = self.config["release"]
        logging.debug(f"Release: {release}")
        base_url = self.config["git_repo"].rstrip("/")
        url = f"{base_url}{self.GIT_RELEASES_PATH}/{release}/{filename}"
        return url

    def _write_stream_to_file(self, response: requests.Response, file: tempfile.NamedTemporaryFile) -> None:
        """Write a stream from a requests response to a file."""
        try:
            for chunk in response.iter_content(chunk_size=self.CHUNK_SIZE):
                if chunk:
                    file.write(chunk)
            file.flush()
        except Exception as e:
            # clean up the temporary file
            Path(file.name).unlink(missing_ok=True)
            logging.error(f"Error writing stream to file: {e}")
            raise e


class WorkflowJob:
    """
    A class to manage a Workflow's job state and execution, including submission, status, and output. A WorkflowJob
    combines a SiteConfig object, a WorkflowStateManager object, and a JobRunner object to manage the job state and
    execution, and to propagate job results back to the workflow state and ultimately to the database.
    A WorkflowJob object is created with:
    - a SiteConfig object
    - a workflow state dictionary
    - a job metadata dictionary
    - an optional operation id (opid)
    - an optional JobRunnerABC object (default is CromwellRunner)


    """
    def __init__(self, site_config: SiteConfig, workflow_state: Dict[str, Any] = None,
                 job_metadata: Dict['str', Any] = None, opid: str = None, job_runner: JobRunnerABC = None) -> None:
        self.site_config = site_config
        self.workflow = WorkflowStateManager(workflow_state, opid)
        # default to CromwellRunner if no job_runner is provided
        if job_runner is None:
            job_runner = CromwellRunner(site_config, self.workflow, job_metadata)
        self.job = job_runner

    # Properties to access the site config, job state, and job runner attributes
    @property
    def opid(self) -> Optional[str]:
        """ Get the operation id """
        return self.workflow.state.get("opid", None)

    def set_opid(self, opid: str, force: bool = False):
        """ Set the operation id """
        if self.opid and not force:
            raise ValueError("opid already set in job state")
        self.workflow.update_state({"opid": opid})

    @property
    def done(self) -> Optional[bool]:
        """ Get the done state of the job """
        return self.workflow.state.get("done", None)

    @done.setter
    def done(self, done: bool):
        """ Set the done state of the job """
        self.workflow.update_state({"done": done})

    @property
    def job_status(self) -> str:
        """
        Get the status of the job. If the job has not been submitted, return "Unsubmitted".
        If the job has failed and the number of retries has been exceeded, return "Failed".
        Otherwise, return the status from the job runner.
        """
        status = None
        # extend this list as needed for other job runners
        job_id_keys = ["cromwell_jobid"]
        failed_count = self.workflow.state.get("failed_count", 0)
        # if none of the job id keys are in the workflow state, it is unsubmitted
        if not any(key in self.workflow.state for key in job_id_keys):
            status = "Unsubmitted"
            self.workflow.update_state({"last_status": status})
        elif self.workflow.state.get("last_status") == "Succeeded":
            status = "Succeeded"
        elif self.workflow.state.get("last_status") == "Failed" and failed_count >= self.job.max_retries:
            status = "Failed"
        else:
            status = self.job.get_job_status()
            self.workflow.update_state({"last_status": status})
        return status

    @property
    def workflow_execution_id(self) -> Optional[str]:
        """ Get the workflow execution id """
        return self.workflow.workflow_execution_id

    @property
    def data_dir(self) -> str:
        """ Get the data directory """
        return self.site_config.data_dir

    @property
    def execution_resource(self) -> str:
        """ Get the execution resource (e.g., NERSC-Perlmutter) """
        return self.site_config.resource

    @property
    def url_root(self) -> str:
        """ Get the URL root """
        return self.site_config.url_root

    @property
    def was_informed_by(self) -> str:
        """ get the was_informed_by ID value """
        return self.workflow.was_informed_by

    @property
    def as_workflow_execution_dict(self) -> Dict[str, Any]:
        """
        Create a dictionary representation of the basic workflow execution attributes for a WorkflowJob.
        """
        base_dict = {"id": self.workflow_execution_id, "type": self.workflow.workflow_execution_type,
            "name": self.workflow.workflow_execution_name, "git_url": self.workflow.config["git_repo"],
            "execution_resource": self.execution_resource, "was_informed_by": self.was_informed_by,
            "has_input": [dobj["id"] for dobj in self.workflow.config["input_data_objects"]],
            "started_at_time": self.workflow.state.get("start"), "ended_at_time": self.workflow.state.get("end"),
            "version": self.workflow.config["release"], }
        return base_dict

    def make_data_objects(self, output_dir: Union[str, Path] = None) -> List[DataObject]:
        """
        Create DataObject objects for each output of the job.
        """

        data_objects = []

        for output_spec in self.workflow.data_outputs:  # specs are defined in the workflow.yaml file under Outputs
            output_key = f"{self.workflow.input_prefix}.{output_spec['output']}"
            logging.info(f"Processing output {output_key}")
            # get the full path to the output file from the job_runner
            output_file_path = Path(self.job.outputs[output_key])
            logging.info(f"Output file path: {output_file_path}")
            if output_key not in self.job.outputs:
                if output_spec.get("optional"):
                    logging.debug(f"Optional output {output_key} not found in job outputs")
                    continue
                else:
                    logging.warning(f"Required output {output_key} not found in job outputs")
                    continue


            md5_sum = _md5(output_file_path)
            file_url = f"{self.url_root}/{self.was_informed_by}/{self.workflow_execution_id}/{output_file_path.name}"

            # copy the file to the output directory if provided
            new_output_file_path = None
            if output_dir:
                new_output_file_path = Path(output_dir) / output_file_path.name
                # copy the file to the output directory
                shutil.copy(output_file_path, new_output_file_path)
            else:
                logging.warning(f"Output directory not provided, not copying {output_file_path} to output directory")

            # create a DataObject object
            data_object = DataObject(
                id=output_spec["id"], name=output_file_path.name, type="nmdc:DataObject", url=file_url,
                data_object_type=output_spec["data_object_type"], md5_checksum=md5_sum,
                description=output_spec["description"], was_generated_by=self.workflow_execution_id, )

            data_objects.append(data_object)
        return data_objects

    def make_workflow_execution(self, data_objects: List[DataObject]) -> WorkflowExecution:
        """
        Create a workflow execution instance for the job. This record includes the basic workflow execution attributes
        and the data objects generated by the job. Additional workflow-specific attributes can be defined in the
        workflow execution template and read from a job's output files.
        The data objects are added to the record as a list of IDs in the "has_output" key.
        """
        wf_dict = self.as_workflow_execution_dict
        wf_dict["has_output"] = [dobj.id for dobj in data_objects]
        wf_dict["ended_at_time"] = self.job.metadata.get("end")

        # workflow-specific keys
        logical_names = set()
        field_names = set()
        pattern = r'\{outputs\.(\w+)\.(\w+)\}'
        for attr_key, attr_val in self.workflow.execution_template.items():
            if attr_val.startswith("{outputs."):
                match = re.match(pattern, attr_val)
                if not match:
                    logging.warning(f"Invalid output reference {attr_val}")
                    continue
                logical_names.add(match.group(1))
                field_names.add(match.group(2))

        for logical_name in logical_names:
            output_key = f"{self.workflow.input_prefix}.{logical_name}"
            data_path = self.job.outputs.get(output_key)
            if data_path:
                # read in as json
                with open(data_path) as f:
                    data = json.load(f)
                for field_name in field_names:
                    # add to wf_dict if it has a value
                    if field_name in data:
                        wf_dict[field_name] = data[field_name]
                    else:
                        logging.warning(f"Field {field_name} not found in {data_path}")

        wfe = workflow_process_factory(wf_dict)
        return wfe



def _json_tmp(data):
    fp, fname = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fp, "w") as fd:
        fd.write(json.dumps(data))
    return fname


def _md5(file):
    return hashlib.md5(open(file, "rb").read()).hexdigest()
