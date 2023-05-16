#!/usr/bin/env python

import sys
import os
import json
import shutil
import requests
from jsonschema import validate
from nmdcapi import nmdcapi


class wfXtraction:
    """
    Class to handle cromwell execution data in the form of metadata.json.
    """

    runtime = nmdcapi()

    def __init__(self):
        # self.metafile = open('metadata_out.json')
        self.respfile = open('response.json')
        self.claimedJobres = json.load(self.respfile)
        # self.cromwellMetadata = json.load(self.metafile)
        self.nmdc_schema_url = "https://raw.githubusercontent.com/microbiomedata/nmdc-schema/main/nmdc_schema/nmdc.schema.json"
        self.job_id = "c2ec9372-cb68-416d-953b-64db76e9d35e" 
        self.http_directory = "/global/cfs/cdirs/m3408/aim2/dev/ReadsQC"
        self.directory_url = "https://data.microbiomedata.org/data/"
        self.cromwell_root = "http://cori21-ib0:8088/api/workflows/v1"

    def extract(self):
        """
        Extract from execution, validate, and register
        """

        actid_directory = self.handler(self.claimedJobres['actid'],self.claimedJobres['workflow']['id'])

        if(actid_directory is not None):
            for productKey,productValue in self.cromwellMetadata['outputs'].items():
                try: 
                    print(f"Worfklow Product {productValue} for {self.claimedJobres['workflow']['id']} being moved to {actid_directory}")
                    shutil.copy(productValue,actid_directory)

                except shutil.SameFileError:
                    print("Source and destination represents the same file.")
            
                except PermissionError:
                    print("Permission denied.")
        else:
            sys.exit("Process Has Been Mistakenly Repeated, Detected by Logic Capture. Goodbye")

        
        if schema_validation(actid_directory):
            try:
                object_file = "object.json"
                http_dir = f"{self.claimedJobres['actid']}/{object_file}"
                reg_resp = self.runtime.create_object(object_file,"Metaata",http_dir)
                metadata_in = runtime.set_type(obj, "metadata-in")
            except requests.exceptions.RequestException as err:
                 raise SystemExit(err)


    def handler(self):
        mode = 0o777
  
        # Path
        _path = os.path.join(self.http_directory, self.claimedJobres['actid'])
        workflow_directory = os.path.join(_path, self.claimedJobres['workflow']['id'])
        
        try:
            os.mkdir(_path, mode)
            os.mkdir(workflow_directory,mode)
            print(f"Directory '{workflow_directory} created")
            return workflow_directory
        except FileExistsError:
            print(f'Directory Exists for {actid}')
            skip_process = 'Process_Complete'
            for product in os.listdir(_path):
                print(f"{product} exists for Activity {actid}, and {self.claimedJobres['config']['release']} is has not changed since last process")

            return None

    def cromwell_metadata(self, expand=True):
        expand_s = "false"
        if expand:
            expand_s = "true"

        url = "%s/%s/metadata?expandSubWorkflows=%s" %(self.cromwell_root, self.job_id, expand_s)
        
        resp = requests.post(url, timeout=60).json()

        return resp

    def schema_validation(self,object_dir):
        nmdc_schema_json = json.loads(requests.get(self.nmdc_schema_url).text)

        object_file = os.path.join(object_dir,'object.json')

        with open(object_file,'r') as analysis_set:
            object_dict = json.load(analysis_set)

        try:
            validate(instance=object_dict, schema=nmdc_schema_json)
        except jsonschema.exceptions.ValidationError as err:
            print(err.message)
            return False

        return True

        
if __name__=='__main__':
    xtract = wfXtraction()