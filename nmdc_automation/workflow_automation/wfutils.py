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
import yaml
from linkml_runtime.dumpers import json_dumper

class WorkflowJob():
    
    debug = False
    dryrun = False
    # Future
    options = None
    activity_templ = None
    outputs = None
    input_data_objects = []
    start = None
    end = None

    def __init__(self, config,typ=None, nmdc_jobid=None, 
                 opid=None, activity_id="TODO", state=None, nocheck=False):
        self.config = config
        self.cromurl = self.config['cromwell']['cromwell_url']
        self.data_dir = self.config['directories']['data_dir']
        self.resource = self.config['site']['resource']
        self.url_root = self.config['nmdc']['url_root']
        with open(self.config['worfklows']['workflows_config'], 'r') as file:
            self.worfklow_config = yaml.safe_load(file)
        if state:
            self.activity_id = state['activity_id']
            self.nmdc_jobid = state['nmdc_jobid']
            self.opid = state.get('opid', None)
            self.type = state['type']
            self.workflow_config = state['conf']
            self.jobid = state['cromwell_jobid']
            self.last_status = state['last_status']
            self.failed_count = state.get('failed_count', 0)
            self.done = state.get('done', None)
            self.start = state.get('start')
            self.end = state.get('end')
        else:
            self.activity_id = activity_id
            self.type = typ
            self.nmdc_jobid = nmdc_jobid
            self.opid = opid
            self.done = None
            self.jobid = None
            self.failed_count = 0
            self.last_status = "Unsubmitted"

        if 'outputs' in self.workflow_config:
            self.outputs = self.workflow_config['outputs']
        if 'activity' in self.workflow_config:
            self.activity_templ = self.workflow_config['activity']
        if 'input_data_objects' in self.workflow_config:
            self.input_data_objects = self.workflow_config['input_data_objects']

        if self.jobid and not nocheck:
            self.check_status()

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
                "opid": self.opid
                }
        return data

    def json_log(self, data, title="json_log"):
        logging.debug(title)
        logging.debug(json.dumps(data, indent=2))

    def check_status(self):
        """
        Check the status in Cromwell
        """
        if not self.jobid:
            return "Unsubmitted"
        url = f"{self.cromurl}/{self.jobid}/status"
        resp = requests.get(url)
        state = "Unknown"
        if resp.status_code == 200:
            data = resp.json()
            state = data['status']
        self.last_status = state
        if state == "Succeeded" and not self.end:
            self.end = datetime.datetime.now(pytz.utc).isoformat()
        return state

    def get_metadata(self):
        """
        Check the status in Cromwell
        """
        if not self.jobid:
            return "Unsubmitted"
        url = f"{self.cromurl}/{self.jobid}/metadata"
        resp = requests.get(url)
        md = {}
        if resp.status_code == 200:
            md = resp.json()
        return md
    
    def _generate_inputs(self):
        inputs = {}
        prefix = self.workflow_config['input_prefix']
        for k, v in self.workflow_config['inputs'].items():
            nk = f'{prefix}.{k}'
            # TODO: clean this up
            if v == "{resource}":
                v = self.config['site']['resource']
            inputs[nk] = v
        return inputs

    def _generate_labels(self):
        labels = dict()
        for p in ['release', 'wdl', 'git_repo']:
            labels[p] = self.workflow_config[p]
        labels["pipeline_version"] = labels['release']
        labels["pipeline"] = labels['wdl']
        labels["activity_id"] = self.activity_id
        labels["opid"] = self.opid
        labels["submitter"] = "nmdcda"
        return labels

    def fetch_release_file(self, fn, suffix=None):
        release = self.workflow_config['release']
        url = self.workflow_config['git_repo'].rstrip('/')
        url += f"/releases/download/{release}/{fn}"

        resp = requests.get(url, stream=True)
        if resp.status_code != 200:
            raise ValueError("Bad response")
        fp, fname = tempfile.mkstemp(suffix=suffix)
        with os.fdopen(fp, 'wb') as fd:
            for chunk in resp.iter_content(chunk_size=1000000):
                fd.write(chunk)
        return fname

    def cromwell_submit(self, force=False):
        """
        Check if a task needs to be submitted.
        """

        # Refresh the log
        status = self.check_status()
        states = ['Failed', 'Aborted', 'Aborting', "Unsubmitted"]
        if not force and status not in states:
            logging.info("Skipping: %s %s" % (self.activity_id, status))
            return
    
        cleanup = []
        files = {}
        job_id = "unknown"
        conf = self.workflow_config
        try:
            inputs = self._generate_inputs()
            labels = self._generate_labels()
            wdl_file = self.fetch_release_file(conf['wdl'], suffix='.wdl')
            cleanup.append(wdl_file)
            bundle_file = self.fetch_release_file("bundle.zip", suffix='.zip')
            cleanup.append(bundle_file)
            self.json_log(inputs, title="Inputs")
            self.json_log(labels, title="Labels")
            infname = _json_tmp(inputs)
            cleanup.append(infname)
            lblname = _json_tmp(labels)
            cleanup.append(lblname)

            files['workflowSource'] = open(wdl_file)
            files['workflowDependencies'] = open(bundle_file, 'rb')
            files['workflowInputs'] = open(infname)
            files['labels'] = open(lblname)

            # TODO: Add something to handle priority
            if self.options:
                files['workflowOptions'] = open(self.options)

            if not self.dryrun:
                resp = requests.post(self.cromurl, data={}, files=files)
                if resp.ok:
                    data = resp.json()
                    self.json_log(data, title="Response")
                    job_id = data['id']
            else:
                job_id = "dryrun"

            logging.info(f"Submitted: {job_id}")
            self.start = datetime.datetime.now(pytz.utc).isoformat()
            self.jobid = job_id
            self.done = False

        finally:
            for fld in files:
                files[fld].close()

            for f in cleanup:
                os.unlink(f)


class NmdcSchema():
    
    def __init__(self):
        self.nmdc_db = nmdc.Database()
        self._data_object_string = "nmdc:DataObject"
        
    def make_data_object(self,name: str,full_file_name: str,file_url: str, data_object_type: str, dobj_id: str, md5_sum: str,description: str, omics_id: str) -> None:
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
                description=description.replace("{id}", omics_id)
            ))
                    
    def create_activity_record(self, activity_name, workflow, activity_id, resource, has_inputs_list, has_output_list, omic_id, start_time, end_time):
        
        
        
        database_activity_set = self.activity_store[activity_name[0]]
                
        database_activity_range = self.activity_store[activity_name[1]]
        
        database_activity_set.append(
                    database_activity_range(
                        id=activity_id, #call minter for activity type
                        name=activity_name,
                        git_url=workflow['Git_repo'],
                        version=workflow['Version'],
                        part_of=[omic_id],
                        execution_resource=resource,
                        started_at_time=start_time,
                        has_input=has_inputs_list,
                        has_output=has_output_list, 
                        type=workflow['Type'],
                        ended_at_time=end_time, 
                        was_informed_by=omic_id, 
                    ))
        
    def activity_imap(self):
        '''Inform Object Mapping Process what activies need to be imported and distrubuted across the process'''
        
        activity_store_dict = {
            'nmdc:MetagenomeSequencing': (self.nmdc_db.metagenome_sequencing_activity_set, nmdc.MetagenomeSequencingActivity),
            'nmdc:ReadQcAnalysisActivity': (self.nmdc_db.read_qc_analysis_activity_set,nmdc.ReadQcAnalysisActivity),
            'nmdc:ReadBasedTaxonomyAnalysisActivity': (self.nmdc_db.read_based_taxonomy_analysis_activity_set, nmdc.ReadBasedTaxonomyAnalysisActivity),
            'nmdc:MetagenomeAssembly': (self.nmdc_db.metagenome_assembly_set, nmdc.MetagenomeAssembly),
            'nmdc:MetagenomeAnnotationActivity': (self.nmdc_db.metagenome_annotation_activity_set, nmdc.MetagenomeAnnotationActivity),
            'nmdc:MAGsAnalysisActivity': (self.nmdc_db.mags_activity_set, nmdc.MagsAnalysisActivity)
        }
                
        return activity_store_dict
    
    def get_database_object_dump(self):
        """
        Get the NMDC database object.

        Returns:
            nmdc.Database: NMDC database object.
        """
        nmdc_database_object = json_dumper.dumps(self.nmdc_db,inject_type=False)
        return nmdc_database_object

def _json_tmp(data):
    fp, fname = tempfile.mkstemp(suffix='.json')
    with os.fdopen(fp, 'w') as fd:
        fd.write(json.dumps(data))
    return fname

def jprint(obj):
    print(json.dumps(obj, indent=2))
    
def _md5(file):
    return hashlib.md5(open(file, 'rb').read()).hexdigest()