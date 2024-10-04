#!/usr/bin/env python

from abc import ABC, abstractmethod
import os
import json
import tempfile
import requests
import nmdc_schema.nmdc as nmdc
import logging
import datetime
import pytz
import re
import hashlib
from linkml_runtime.dumpers import json_dumper
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import shutil

from nmdc_automation.config import SiteConfig
from nmdc_automation.workflow_automation.models import DataObject, workflow_process_factory

def get_workflow_execution_record_for_job(job: "WorkflowJobDeprecated", has_output_ids: List[str]) -> Dict[str, Any]:
    """
    Create the appropriate subtype of WorkflowExecution object for a completed job.
    """
    record = job.as_workflow_execution_dict()

    # get workflow-specific keys
    prefix = job.workflow_config["input_prefix"]
    for k, v in job.execution_template.items():
        if v.startswith('{outputs.'):
            out_key = f"{prefix}.{v[9:-1]}"
            if out_key not in job.outputs:
                ele = out_key.split(".")
                map_name = ".".join(ele[0:-1])
                key_name = ele[-1]
                record[k] = job.outputs[map_name][key_name]
            else:
                record[k] = job.outputs[out_key]

    record["has_output"] = has_output_ids
    return record


class WorkflowJobDeprecated:
    DEFAULT_STATUS = "Unsubmitted"
    SUCCESS_STATUS = "Succeeded"
    METADATA_URL_SUFFIX = "/metadata"
    LABEL_SUBMITTER_VALUE = "nmdcda"
    LABEL_PARAMETERS = ["release", "wdl", "git_repo"]
    CHUNK_SIZE = 1000000  # 1 MB
    GIT_RELEASES_PATH = "/releases/download"

    debug = False
    dryrun = False
    options = None
    execution_template = None
    outputs = None
    input_data_objects = []
    start = None
    end = None

    def __init__(
        self,
        site_config,
        type=None,
        workflow_config=None,
        nmdc_jobid=None,
        opid=None,
        activity_id=None,
        state=None,
        nocheck=False,
    ):
        self.config = site_config
        self.workflow_config = workflow_config
        self.set_config_attributes()
        if workflow_config:
            self.load_workflow_config()
        self.set_initial_state(state, activity_id, type, nmdc_jobid, opid)
        if self.jobid and not nocheck:
            self.check_status()

    def set_config_attributes(self):
        # TODO: Why are we not using the config object directly? This is a code smell.
        #   Consider wrapping with @property decorators to make this more explicit.
        self.cromwell_url = self.config.cromwell_url
        self.data_dir = self.config.data_dir
        self.resource = self.config.resource
        self.url_root = self.config.url_root

    # TODO: These could be @property decorators
    def load_workflow_config(self):
        self.outputs = self.workflow_config.get("outputs")
        # for backward compatibility
        workflow_execution = self.workflow_config.get("workflow_execution", None)
        if not workflow_execution:
            workflow_execution = self.workflow_config.get("activity", None)

        self.execution_template = workflow_execution
        self.input_data_objects = self.workflow_config.get("input_data_objects")

    def set_initial_state(self, state, activity_id, typ, nmdc_jobid, opid):
        if state:
            self.load_state_from_dict(state)
        else:
            self.set_default_state(activity_id, typ, nmdc_jobid, opid)

    def load_state_from_dict(self, state):
        self.activity_id = state["activity_id"]
        self.nmdc_jobid = state["nmdc_jobid"]
        self.opid = state.get("opid", None)
        self.type = state["type"]
        self.workflow_config = state["conf"]
        self.jobid = state["cromwell_jobid"]
        self.last_status = state["last_status"]
        self.failed_count = state.get("failed_count", 0)
        self.done = state.get("done", None)
        self.start = state.get("start")
        self.end = state.get("end")
        self.load_workflow_config()

    def set_default_state(self, activity_id, typ, nmdc_jobid, opid):
        self.activity_id = activity_id
        # TODO why?
        self.type = typ
        self.nmdc_jobid = nmdc_jobid
        self.opid = opid
        self.done = None
        self.jobid = None
        self.failed_count = 0
        self.last_status = self.DEFAULT_STATUS

    def get_state(self):
        data = {
            "type": self.type,
            "cromwell_jobid": self.jobid,
            "nmdc_jobid": self.nmdc_jobid,
            "conf": self.workflow_config,
            "activity_id": self.activity_id,
            "last_status": self.last_status,
            "done": self.done,
            "failed_count": self.failed_count,
            "start": self.start,
            "end": self.end,
            "opid": self.opid,
        }
        return data

    def as_workflow_execution_dict(self):
        return {
            "id": self.activity_id,
            "type": self.type,
            "name": self.execution_template["name"].replace("{id}", self.activity_id),
            "git_url": self.workflow_config["git_repo"],
            "execution_resource": self.config.resource,
            "was_informed_by": self.workflow_config["was_informed_by"],
            "has_input": [dobj["id"] for dobj in self.input_data_objects],
            "started_at_time": self.start,
            "ended_at_time": self.end,
            "version": self.workflow_config["release"],
        }

    def check_status(self):
        """
        Check the status in Cromwell
        """
        if not self.jobid:
            self.last_status = "Unsubmitted"
            return self.last_status

        url = f"{self.cromwell_url}/{self.jobid}/status"

        try:
            resp = requests.get(url)
            resp.raise_for_status()
        except requests.exceptions.RequestException as ex:
            # logging.error(f"Error checking status: {ex}")
            self.last_status = "Error"
            return self.last_status

        data = resp.json()
        # TODO: Why not name this variable 'status'?
        state = data.get("status", "Unknown")
        self.last_status = state

        if state == "Succeeded" and not self.end:
            self.end = datetime.datetime.now(pytz.utc).isoformat()

        return state

    def get_cromwell_metadata(self):
        """
        Check the status in Cromwell
        """
        if not self.jobid:
            return self.DEFAULT_STATUS
        url = f"{self.cromwell_url}/{self.jobid}{self.METADATA_URL_SUFFIX}"
        resp = requests.get(url)
        resp.raise_for_status()
        return resp.json()

    def json_log(self, data, title="json_log"):
        logging.debug(title)
        logging.debug(json.dumps(data, indent=2))

    def _generate_inputs(self):
        inputs = {}
        prefix = self.workflow_config["input_prefix"]
        for input, input_object in self.workflow_config["inputs"].items():
            input_prefix = f"{prefix}.{input}"
            if input_object == "{resource}":
                input_object = self.config.resource
            inputs[input_prefix] = input_object
        return inputs

    def _generate_labels(self):
        labels = self.get_label_parameters()
        labels["pipeline_version"] = labels["release"]
        labels["pipeline"] = labels["wdl"]
        labels["activity_id"] = self.activity_id
        labels["opid"] = self.opid
        labels["submitter"] = self.LABEL_SUBMITTER_VALUE
        return labels

    def get_label_parameters(self):
        return {param: self.workflow_config[param] for param in self.LABEL_PARAMETERS}

    def fetch_release_file(self, fn, suffix=None):
        release = self.workflow_config["release"]
        base_url = self.workflow_config["git_repo"].rstrip("/")
        url = base_url + f"{self.GIT_RELEASES_PATH}/{release}/{fn}"

        logging.debug(f"BASE URL: {base_url}")
        logging.debug(f"URL: {url}")

        resp = requests.get(url, stream=True)
        resp.raise_for_status()

        fp, fname = tempfile.mkstemp(suffix=suffix)
        try:
            with os.fdopen(fp, "wb") as fd:
                for chunk in resp.iter_content(chunk_size=self.CHUNK_SIZE):
                    fd.write(chunk)
        except Exception as ex:
            os.unlink(fname)
            raise ex

        return fname

    def generate_files(self, conf):
        wdl_file = self.fetch_release_file(conf["wdl"], suffix=".wdl")
        bundle_file = self.fetch_release_file("bundle.zip", suffix=".zip")
        files = {
            "workflowSource": open(wdl_file),
            "workflowDependencies": open(bundle_file, "rb"),
            "workflowInputs": open(_json_tmp(self._generate_inputs())),
            "labels": open(_json_tmp(self._generate_labels())),
        }
        if self.options:
            files["workflowOptions"] = open(self.options)
        return files

    def cromwell_submit(self, force=False):
        # Refresh the log
        status = self.check_status()
        states = ["Failed", "Aborted", "Aborting", "Unsubmitted"]
        if not force and status not in states:
            logging.info("Skipping: %s %s" % (self.activity_id, status))
            return

        cleanup = []
        conf = self.workflow_config
        try:
            self.json_log(self._generate_inputs(), title="Inputs")
            self.json_log(self._generate_labels(), title="Labels")
            files = self.generate_files(conf)
            cleanup.extend(files.values())

            job_id = "unknown"
            if not self.dryrun:
                logging.debug(self.cromwell_url)
                resp = requests.post(self.cromwell_url, data={}, files=files)
                resp.raise_for_status()
                data = resp.json()
                self.json_log(data, title="Response")
                job_id = data["id"]
            else:
                job_id = "dryrun"

            logging.info(f"Submitted: {job_id}")
            self.start = datetime.datetime.now(pytz.utc).isoformat()
            self.jobid = job_id
            self.done = False
        finally:
            for file in cleanup:
                file.close()
                os.unlink(file.name)


class JobRunnerABC(ABC):
    @abstractmethod
    def submit_job(self) -> str:
        pass

    @abstractmethod
    def check_job_status(self) -> str:
        pass


class CromwellRunner(JobRunnerABC):

        def __init__(self, site_config: SiteConfig, workflow: "WorkflowStateManager", job_metadata: Dict[str, Any] = None):
            self.config = site_config
            self.workflow = workflow
            self.service_url = self.config.cromwell_url
            if job_metadata is None:
                job_metadata = {}
            self.metadata = job_metadata


        def submit_job(self) -> str:
            pass

        def check_job_status(self) -> str:
            return "Pending"

        @property
        def job_id(self) -> Optional[str]:
            return self.metadata.get("id", None)

        @property
        def outputs(self) -> Dict[str, str]:
            return self.metadata.get("outputs", {})


class WorkflowStateManager:
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
    def nmdc_job_id(self)-> Optional[str]:
        # different keys in state file vs database record
        return self.cached_state.get("nmdc_jobid", self.cached_state.get("id", None))

    @property
    def job_runner_id(self) -> Optional[str]:
        # for now we only have cromwell as a job runner
        job_runner_ids = ["cromwell_jobid", ]
        for job_runner_id in job_runner_ids:
            if job_runner_id in self.cached_state:
                return self.cached_state[job_runner_id]



class WorkflowJob:
    def __init__(self, site_config: SiteConfig, workflow_state: Dict[str, Any] = None,
                 job_metadata: Dict['str', Any] = None, opid: str = None, job_runner: JobRunnerABC = None
                 )-> None:
        self.site_config = site_config
        self.workflow = WorkflowStateManager(workflow_state, opid)
        # default to CromwellRunner if no job_runner is provided
        if job_runner is None:
            job_runner = CromwellRunner(site_config, self.workflow, job_metadata)
        self.job = job_runner

    # Properties to access the site config, job state, and job runner attributes
    # getter and setter props for job state opid
    @property
    def opid(self) -> str:
        return self.workflow.state.get("opid", None)

    def set_opid(self, opid: str, force: bool = False):
        if self.opid and not force:
            raise ValueError("opid already set in job state")
        self.workflow.update_state({"opid": opid})

    @property
    def done(self) -> Optional[bool]:
        return self.workflow.state.get("done", None)

    @property
    def job_status(self) -> str:
        status = None
        job_id_keys = ["cromwell_jobid"]
        # if none of the job id keys are in the workflow state, it is unsubmitted
        if not any(key in self.workflow.state for key in job_id_keys):
            status = "Unsubmitted"
            self.workflow.update_state({"last_status": status})
            return status
        elif self.workflow.state.get("last_status") == "Succeeded":
            status = "Succeeded"
            return status
        else:
            status = self.job.check_job_status()
            self.workflow.update_state({"last_status": status})
            return status




    @property
    def workflow_execution_id(self) -> Optional[str]:
        return self.workflow.workflow_execution_id

    @property
    def cromwell_url(self) -> str:
        return self.site_config.cromwell_url

    @property
    def data_dir(self) -> str:
        return self.site_config.data_dir

    @property
    def execution_resource(self) -> str:
        return self.site_config.resource

    @property
    def url_root(self) -> str:
        return self.site_config.url_root

    @property
    def was_informed_by(self) -> str:
        return self.workflow.was_informed_by

    @property
    def as_workflow_execution_dict(self) -> Dict[str, Any]:
        # for forward compatibility we need to strip Activity from the type
        normalized_type = self.workflow.workflow_execution_type.replace("Activity", "")
        base_dict = {
            "id": self.workflow_execution_id,
            "type": normalized_type,
            "name": self.workflow.workflow_execution_name,
            "git_url": self.workflow.config["git_repo"],
            "execution_resource": self.execution_resource,
            "was_informed_by": self.was_informed_by,
            "has_input": [dobj["id"] for dobj in self.workflow.config["input_data_objects"]],
            "started_at_time": self.workflow.state.get("start"),
            "ended_at_time": self.workflow.state.get("end"),
            "version": self.workflow.config["release"],
        }
        return base_dict

    def make_data_objects(self, output_dir: Union[str, Path] = None)-> List[DataObject]:
        """
        Create DataObject objects for each output of the job.
        """

        data_objects = []

        for output_spec in self.workflow.data_outputs: # specs are defined in the workflow.yaml file under Outputs
            output_key = f"{self.workflow.input_prefix}.{output_spec['output']}"
            if output_key not in self.job.outputs:
                if output_spec.get("optional"):
                    logging.debug(f"Optional output {output_key} not found in job outputs")
                    continue
                else:
                    logging.warning(f"Required output {output_key} not found in job outputs")
                    continue
            # get the full path to the output file from the job_runner
            output_file_path = Path(self.job.outputs[output_key])


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
                id = output_spec["id"],
                name=output_file_path.name,
                type="nmdc:DataObject",
                url=file_url,
                data_object_type=output_spec["data_object_type"],
                md5_checksum=md5_sum,
                description=output_spec["description"],
                was_generated_by=self.workflow_execution_id,
            )

            data_objects.append(data_object)
        return data_objects

    def make_workflow_execution_record(self, data_objects: List[DataObject]) -> Dict[str, Any]:
        """
        Create a workflow execution record for the job
        """
        wf_dict = self.as_workflow_execution_dict
        wf_dict["has_output"] = [dobj.id for dobj in data_objects]

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

        return wf_dict





def _json_tmp(data):
    fp, fname = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fp, "w") as fd:
        fd.write(json.dumps(data))
    return fname


def jprint(obj):
    print(json.dumps(obj, indent=2))


def _md5(file):
    return hashlib.md5(open(file, "rb").read()).hexdigest()
