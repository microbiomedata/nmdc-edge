import logging
import asyncio
from yaml import load
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader
from datetime import datetime
import uuid
import os
import requests
import json
from time import sleep
from time import time

from functools import lru_cache
from pymongo import MongoClient
from pymongo.database import Database as MongoDatabase


_POLL_INTERVAL = 60


@lru_cache
def get_mongo_db() -> MongoDatabase:
    for k in ["HOST", "USERNAME", "PASSWORD", "DBNAME"]:
        if f"MONGO_{k}" not in os.environ:
            raise KeyError(f"Missing MONGO_{k}")
    _client = MongoClient(
        host=os.getenv("MONGO_HOST"),
        username=os.getenv("MONGO_USERNAME"),
        password=os.getenv("MONGO_PASSWORD"),
    )
    return _client[os.getenv("MONGO_DBNAME")]


"""
This is still a prototype implementation.  The plan
is to migrate this fucntion into Dagster.
"""


class Scheduler():
    _sets = ['metagenome_annotation_activity_set',
             'metagenome_assembly_set',
             'read_qc_analysis_activity_set',
             'mags_activity_set',
             'read_based_analysis_activity_set']

    def __init__(self, db, wfn="workflows.yaml"):
        logging.info("Initializing Scheduler")
        # Init
        self.workflows = load(open(wfn), Loader=Loader)
        self.db = db
        self.token = None
        self.expires = 0
        self.api_url = os.environ.get("NMDC_API_URL")
        self.client_id = os.environ.get("NMDC_CLIENT_ID")
        self.client_secret = os.environ.get("NMDC_CLIENT_SECRET")

        # Build a workflow map for later use
        self.workflow_by_name = dict()
        for w in self.workflows['Workflows']:
            self.workflow_by_name[w['Name']] = w

    def refresh_token(self):
        # If it expires in 60 seconds, refresh
        if not self.token or self.expires + 60 > time():
            self.get_token()

    def get_token(self):
        """
        Get a token using a client id/secret.
        """
        h = {
                'accept': 'application/json',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
        data = {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret
                }
        url = self.api_url + '/token'
        resp = requests.post(url, headers=h, data=data).json()
        expt = resp['expires']
        self.expires = time() + expt['minutes'] * 60

        self.token = resp['access_token']
        self.api_headers = {
                       'accept': 'application/json',
                       'Content-Type': 'application/json',
                       'Authorization': 'Bearer %s' % (self.token)
                       }
        return resp

    async def run(self):
        logging.info("Starting Scheduler")
        while True:
            self.cycle()
            await asyncio.sleep(_POLL_INTERVAL)

    def coll_prov_acts(self, act, rset, acts, root_dos=[]):
        """
        This is a recursive function that will walk up the
        object provenance (has_input, has_output) to find
        all the preceeding activities and data objects.

        It returns the set of activities and "root" objects.
        Root objects are data objects with no matching
        has_output.  So they must be the original raw data.
        """
        activity_id = act['id']
        rec_id = f'{rset}:{activity_id}'
        if rec_id in acts:
            return acts
        act.pop("_id")
        acts[rec_id] = act
        inp = act["has_input"]
        root_dos = []
        for d in inp:
            hit = False
            for set in self._sets:
                nact = self.db[set].find_one({"has_output": d})
                if nact is None:
                    continue
                hit = True
                acts, root_dos = self.coll_prov_acts(nact, set,
                                                     acts, root_dos)
            if not hit:
                root_dos.append(d)
        return acts, root_dos

    def add_job_rec(self, job):
        """
        This takes a job and using the workflow definition,
        resolves all the information needed to create a
        job record.
        """
        wf = job['wf']
        trig_actid = job['trigger_activity_id']
        trigger_set = job['trigger_set']
        pred = wf['Predecessor']
        if not pred:
            # This can't happen
            logging.error("Missing predecessor")
            return
        pred_wf = self.workflow_by_name[pred]

        # Find the activity that generated the data object id
        act = self.db[trigger_set].find_one({"id": trig_actid})
        informed_by = act.get("was_informed_by", "undefined")

        # Ignore if the trigger activity isn't the latest version
        if act is None or pred_wf['Version'] != act.get('version'):
            return

        # Get the provenance
        acts, root_dos = self.coll_prov_acts(act, trigger_set, {})
        dos = root_dos
        for aid, act in acts.items():
            for did in act['has_output']:
                dos.append(did)

        # Now collect all the data objects and their types
        do_by_type = dict()
        for did in dos:
            dobj = self.db["data_object_set"].find_one({"id": did})
            if dobj and 'data_object_type' in dobj:
                dobj.pop("_id")
                do_by_type[dobj['data_object_type']] = dobj
        base_id, iteration = self.get_activity_id(wf, informed_by)
        activity_id = f"{base_id}.{iteration}"
        inp_objects = []
        inp = dict()
        for k, v in wf['Inputs'].items():
            if v.startswith('do:'):
                do_type = v[3:]
                dobj = do_by_type.get(do_type)
                if not dobj:
                    raise ValueError(f"Unable to resolve {do_type}")
                inp_objects.append(dobj)
                v = dobj["url"]
            # TODO: Make this smarter
            if v == "{was_informed_by}":
                v = informed_by
            elif v == "{activity_id}":
                v = activity_id

            inp[k] = v

        # Build the respoonse
        job_config = {
                "git_repo": wf["Git_repo"],
                "release": wf["Version"],
                "wdl": wf["WDL"],
                "activity_id": activity_id,
                "was_informed_by": informed_by,
                "trigger_activity": trig_actid,
                "iteration": iteration,
                "input_prefix": wf["Input_prefix"],
                "inputs": inp,
                "input_data_objects": inp_objects
                }
        if "Activity" in wf:
            job_config["activity"] = wf["Activity"]
        if "Outputs" in wf:
            outputs = []
            for output in wf["Outputs"]:
                # Mint an ID
                output["id"] = self.call_minter("type:DataObject", informed_by)
                outputs.append(output)
            job_config["outputs"] = outputs

        jr = {
            "workflow": {
                "id": "{Name}: {Version}".format(**wf)
            },
            "id": self.get_id(),
            "created_at": datetime.today().replace(microsecond=0),
            "config": job_config,
            "claims": []
        }
        rec = self.db.jobs.insert_one(jr, bypass_document_validation=True)
        logging.info(f'JOB RECORD: {jr["id"]}')
        # This would make the job record
        # print(json.dumps(ji, indent=2))
        return jr

    def get_id(self):
        """
        Generate an ID for the job

        Note: This is currently Napa compliant.  Since these are somewhat
        ephemeral I'm not sure if it matters though.
        """
        u = str(uuid.uuid1())
        return f"nmdc:{u}"

    def call_minter(self, id_type, informed_by):
        self.refresh_token()
        url = f"{self.api_url}/pids/mint"
        data = {
                "schema_class": {"id": id_type},
                "how_many": 1
               }
        resp = requests.post(url,
                             data=json.dumps(data),
                             headers=self.api_headers)
        if not resp.ok:
            raise ValueError("Failed to mint ID")
        id = resp.json()[0]
        url = f"{self.api_url}/pids/bind"
        data = {
                "id_name": id,
                "metadata_record": {"informed_by": informed_by}
               }
        resp = requests.post(url,
                             data=json.dumps(data),
                             headers=self.api_headers)
        if not resp.ok:
            raise ValueError("Failed to bind metadata to pid")
        return id

    def get_activity_id(self, wf, informed_by):
        """
        See if anything exist for this and if not
        mint a new id.
        """

        # This is a temporary workaround and should be removed
        # once the schema names are all fixed.
        act_set = wf['Collection'] #.replace("_qc_", "_QC_")
        q = {"was_informed_by": informed_by}
        ct = 0
        root_id = None

        for doc in self.db[act_set].find(q):
            ct += 1
            last_id = doc['id']

        if ct == 0:
            # Get an ID
            id_type = wf['Type']
            root_id = self.call_minter(id_type, informed_by)
            return root_id, 1
        else:
            root_id = '.'.join(last_id.split('.')[0:-1])
            return root_id, ct+1

    def new_jobs(self, wf):
        """
        This function is given a workflow and identifies new
        jobs to create by looking at the workflow's trigger data
        types and what has been previously processed.
        """

        # Skip disabled workflows
        if not wf['Enabled']:
            return []
        act_set = wf['Collection']
        git_repo = wf['Git_repo']
        vers = wf['Version']
        pred = wf['Predecessor']
        if not pred:
            # Nothing to do
            return []
        pred_wf = self.workflow_by_name[pred]
        trigger_set = pred_wf['Collection']
        comp_acts = {}
        # Filter by git_repo and version
        q = {'config.git_repo': git_repo,
             'config.release': vers}
        for j in self.db.jobs.find(q):
            act = j['config']['trigger_activity']
            comp_acts[act] = j
        # Find all jobs of for this workflow
        q = {'version': vers, 'git_repo': git_repo}
        for act in self.db[act_set].find(q):
            comp_acts[act['id']] = act

        # Check triggers
        # TODO: filter based on active version
        todo = []
        for act in self.db[trigger_set].find():
            actid = act['id']
            if actid in comp_acts:
                continue
            todo.append({'wf': wf,
                         'trigger_set': trigger_set,
                         'trigger_activity_id': actid})
        return todo

    def cycle(self):
        """
        This function does a single cycle of looking for new jobs
        """
        job_recs = []
        for w in self.workflows['Workflows']:
            if not w["Enabled"]:
                continue
            logging.debug("Checking: " + w['Name'])
            jobs = self.new_jobs(w)
            for job in jobs:
                try:
                    jr = self.add_job_rec(job)
                    if jr:
                        job_recs.append(jr)
                except Exception as ex:
                    logging.error(str(ex))
                    raise ex
        return job_recs


def main():
    sched = Scheduler(get_mongo_db())
    while True:
        sched.cycle()
        sleep(_POLL_INTERVAL)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
