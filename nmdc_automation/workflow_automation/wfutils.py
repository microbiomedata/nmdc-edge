#!/usr/bin/env python

import os
import json
import tempfile
import requests
import nmdc_schema.nmdc as nmdc
import logging
import datetime
import pytz
import hashlib
from linkml_runtime.dumpers import json_dumper


class WorkflowJob:
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
    activity_templ = None
    outputs = None
    input_data_objects = []
    start = None
    end = None

    def __init__(
        self,
        site_config,
        typ=None,
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
        self.set_initial_state(state, activity_id, typ, nmdc_jobid, opid)
        if self.jobid and not nocheck:
            self.check_status()

    def set_config_attributes(self):
        self.cromurl = self.config.cromwell_url
        self.data_dir = self.config.data_dir
        self.resource = self.config.resource
        self.url_root = self.config.url_root

    def load_workflow_config(self):
        self.outputs = self.workflow_config.get("outputs")
        self.activity_templ = self.workflow_config.get("activity")
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

    def check_status(self):
        """
        Check the status in Cromwell
        """
        if not self.jobid:
            self.last_status = "Unsubmitted"
            return self.last_status

        url = f"{self.cromurl}/{self.jobid}/status"

        try:
            resp = requests.get(url)
            resp.raise_for_status()
        except requests.exceptions.RequestException as ex:
            # logging.error(f"Error checking status: {ex}")
            self.last_status = "Error"
            return self.last_status

        data = resp.json()
        state = data.get("status", "Unknown")
        self.last_status = state

        if state == "Succeeded" and not self.end:
            self.end = datetime.datetime.now(pytz.utc).isoformat()

        return state

    def get_metadata(self):
        """
        Check the status in Cromwell
        """
        if not self.jobid:
            return self.DEFAULT_STATUS
        url = f"{self.cromurl}/{self.jobid}{self.METADATA_URL_SUFFIX}"
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
                logging.debug(self.cromurl)
                resp = requests.post(self.cromurl, data={}, files=files)
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

# TODO: Rename this class to something more descriptive
# and to avoid confusion with the the schema class of the same name
class NmdcSchema:
    def __init__(self):
        self.nmdc_db = nmdc.Database()
        self._data_object_string = "nmdc:DataObject"
        self.activity_store = self.activity_map()

    def make_data_object(
        self,
        name: str,
        full_file_name: str,
        file_url: str,
        data_object_type: str,
        dobj_id: str,
        md5_sum: str,
        description: str,
        omics_id: str,
    ) -> None:
        """Create nmdc database data object

        Args:
            name (str): name of data object
            full_file_name (str): full file name
            file_url (str): url for data object file
            data_object_type (str): nmdc data object type
            dobj_id (str): minted data object id
            md5_sum (str): md5 check sum of data product
            description (str): description for data object
            omics_id (str): minted omics id
        """

        self.nmdc_db.data_object_set.append(
            nmdc.DataObject(
                file_size_bytes=os.stat(full_file_name).st_size,
                name=name,
                url=file_url,
                data_object_type=data_object_type,
                type=self._data_object_string,
                id=dobj_id,
                md5_checksum=md5_sum,
                description=description.replace("{id}", omics_id),
            )
        )

    def create_activity_record(
        self,
        activity_record,
        activity_name,
        workflow,
        activity_id,
        resource,
        has_inputs_list,
        has_output_list,
        omic_id,
        start_time,
        end_time,
    ):
        database_activity_set = self.activity_store[activity_record][0]

        database_activity_range = self.activity_store[activity_record][1]

        database_activity_set.append(
            database_activity_range(
                id=activity_id,  # call minter for activity type
                name=activity_name,
                git_url=workflow["git_repo"],
                version=workflow["release"],
                part_of=[omic_id],
                execution_resource=resource,
                started_at_time=start_time,
                has_input=has_inputs_list,
                has_output=has_output_list,
                type=activity_record,
                ended_at_time=end_time,
                was_informed_by=omic_id,
            )
        )

    def activity_map(self):
        """
        Inform Object Mapping Process what activies need to be imported and
        distrubuted across the process
        """

        activity_store_dict = {
            "nmdc:MetagenomeSequencing": (
                self.nmdc_db.metagenome_sequencing_activity_set,
                nmdc.MetagenomeSequencingActivity,
            ),
            "nmdc:ReadQcAnalysisActivity": (
                self.nmdc_db.read_qc_analysis_activity_set,
                nmdc.ReadQcAnalysisActivity,
            ),
            "nmdc:ReadBasedTaxonomyAnalysisActivity": (
                self.nmdc_db.read_based_taxonomy_analysis_activity_set,
                nmdc.ReadBasedTaxonomyAnalysisActivity,
            ),
            "nmdc:MetagenomeAssembly": (
                self.nmdc_db.metagenome_assembly_set,
                nmdc.MetagenomeAssembly,
            ),
            "nmdc:MetagenomeAnnotationActivity": (
                self.nmdc_db.metagenome_annotation_activity_set,
                nmdc.MetagenomeAnnotationActivity,
            ),
            "nmdc:MagsAnalysisActivity": (
                self.nmdc_db.mags_activity_set,
                nmdc.MagsAnalysisActivity,
            ),
        }

        return activity_store_dict

    def get_database_object_dump(self):
        """
        Get the NMDC database object.

        Returns:
            nmdc.Database: NMDC database object.
        """
        nmdc_database_object = json_dumper.dumps(self.nmdc_db, inject_type=False)
        return nmdc_database_object


def _json_tmp(data):
    fp, fname = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fp, "w") as fd:
        fd.write(json.dumps(data))
    return fname


def jprint(obj):
    print(json.dumps(obj, indent=2))


def _md5(file):
    return hashlib.md5(open(file, "rb").read()).hexdigest()
