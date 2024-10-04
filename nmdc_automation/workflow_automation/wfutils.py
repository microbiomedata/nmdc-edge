#!/usr/bin/env python

from abc import ABC, abstractmethod
import os
import json
import tempfile
import logging
import re
import hashlib
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import shutil

from nmdc_automation.config import SiteConfig
from nmdc_automation.workflow_automation.models import DataObject, workflow_process_factory


class JobRunnerABC(ABC):

    @abstractmethod
    def submit_job(self) -> str:
        pass

    @abstractmethod
    def check_job_status(self) -> str:
        pass

    @property
    @abstractmethod
    def job_id(self) -> Optional[str]:
        pass

    @property
    @abstractmethod
    def outputs(self) -> Dict[str, str]:
        pass

    @property
    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        pass



class CromwellRunner(JobRunnerABC):

    def __init__(self, site_config: SiteConfig, workflow: "WorkflowStateManager", job_metadata: Dict[str, Any] = None):
        self.config = site_config
        self.workflow = workflow
        self.service_url = self.config.cromwell_url
        self._metadata = {}
        if job_metadata:
            self._metadata = job_metadata


    def submit_job(self) -> str:
            # TODO: implement
            pass

    def check_job_status(self) -> str:
            # TODO: implement
            return "Pending"

    @property
    def job_id(self) -> Optional[str]:
            return self.metadata.get("id", None)

    @property
    def outputs(self) -> Dict[str, str]:
            return self.metadata.get("outputs", {})

    @property
    def metadata(self) -> Dict[str, Any]:
            return self._metadata

    @metadata.setter
    def metadata(self, metadata: Dict[str, Any]):
            self._metadata = metadata


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

    @done.setter
    def done(self, done: bool):
        self.workflow.update_state({"done": done})

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
