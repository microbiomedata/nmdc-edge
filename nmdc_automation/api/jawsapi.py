#!/usr/bin/env python

import requests
import uuid
from nmdc_automation.config import SiteConfig

_base_url = "http://jaws.lbl.gov:5003/api/v2"
_base_in = "/pscratch/sd/n/nmjaws/nmdc-prod/inputs"

wdl = "https://github.com/microbiomedata/ReadsQC/releases/download/b1.0.8/rqcfilter.wdl"



class JawsApi:
    
    def __init__(self, site_configuration):
        self.config = SiteConfig(site_configuration)
        self._base_url = self.config.api_url
        self.client_id = self.config.client_id
        self.client_secret = self.config.client_secret
        if self._base_url[-1] != "/":
            self._base_url += "/"
        self.token = None
        self.expires = 0
        self.headers = ""
    
    def get_jaws_token(self):
        pass
        
    def submit_job(self, wdl_file, input_json):
        
        sub_id = str(uuid.uuid4())
        
        data = {
                "compute_site_id": "nmdc",
                "input_site_id": "nmdc",
                "team_id": "nmdc",
                "max_ram_gb": "500",
                "submission_id": sub_id,
                "manifest": "{}",
                "json_file": input_json,
                "wdl_file": wdl_file
                }
        
        resp = requests.post(f"{_base_url}/run", headers=self.headers, data=data)
        
        return resp.json()
        
    def cancel_job_by_id(self, job_id):
        
        resp = requests.put(f"{_base_url}/run/{job_id}/cancel", headers=self.headers)
        
        return resp.json()
    
    def get_job_info(self, job_id):
        
        resp = requests.get(f"{_base_url}/run/{job_id}", headers=self.headers)
        
        return resp.json()
    
    def resubmit_job(self, job_id):
        
        resp = requests.put(f"{_base_url}/run/{job_id}/resubmit", headers=self.headers)
        
        return resp.json()
        
    def get_run_logs(self, job_id):
        
        resp = requests.get(f"{_base_url}/run/{job_id}/run_log", headers=self.headers)
        
        return resp.json()        
    
    def get_task_metadata(self, job_id):
        
        resp = requests.get(f"{_base_url}/run/{job_id}/tasks", headers=self.headers)
        
        return resp.json() 

    def get_runtime_metrics(self, job_id):
        
        resp = requests.get(f"{_base_url}/run_metrics/{job_id}", headers=self.headers)
        
        return resp.json()
        
    def cancell_all_jobs(self):
        
        resp = requests.get(f"{_base_url}/run/cancel_all", headers=self.headers)
        
        return resp.json()
        