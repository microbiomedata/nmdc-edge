import logging
import asyncio
from datetime import datetime
import uuid
import os
from time import sleep
from .nmdcapi import nmdcapi
from .workflows import load_workflows

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
        self.workflows = load_workflows(wfn)
        self.db = db
        self.api = nmdcapi()

        # Build a workflow map for later use
        self.workflow_by_name = dict()
        for wf in self.workflows:
            self.workflow_by_name[wf.name] = wf

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
        pred = wf.predecessor
        if not pred:
            # This can't happen
            logging.error("Missing predecessor")
            return
        pred_wf = self.workflow_by_name[pred]

        # Find the activity that generated the data object id
        act = self.db[trigger_set].find_one({"id": trig_actid})
        informed_by = act.get("was_informed_by", "undefined")

        # Ignore if the trigger activity isn't the latest version
        if act is None or pred_wf.version != act.get('version'):
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
        for k, v in wf.inputs.items():
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
                "git_repo": wf.git_repo,
                "release": wf.version,
                "wdl": wf.wdl,
                "activity_id": activity_id,
                "activity_set": wf.collection,
                "was_informed_by": informed_by,
                "trigger_activity": trig_actid,
                "iteration": iteration,
                "input_prefix": wf.input_prefix,
                "inputs": inp,
                "input_data_objects": inp_objects
                }
        if wf.activity:
            job_config["activity"] = wf.activity
        if wf.outputs:
            outputs = []
            for output in wf.outputs:
                # Mint an ID
                output["id"] = self.api.minter("nmdc:DataObject", informed_by)
                outputs.append(output)
            job_config["outputs"] = outputs

        jr = {
            "workflow": {
                "id": "{wf.ame}: {wf.version}"
            },
            "id": self.generate_job_id(),
            "created_at": datetime.today().replace(microsecond=0),
            "config": job_config,
            "claims": []
        }
        self.db.jobs.insert_one(jr, bypass_document_validation=True)
        logging.info(f'JOB RECORD: {jr["id"]}')
        # This would make the job record
        # print(json.dumps(ji, indent=2))
        return jr

    def generate_job_id(self):
        """
        Generate an ID for the job

        Note: This is not currently Napa compliant.  Since these are somewhat
        ephemeral I'm not sure if it matters though.
        """
        u = str(uuid.uuid1())
        return f"nmdc:{u}"

    def mock_mint(self, id_type):
        """
        Return a fixed pattern
        """
        mapping = {
            "nmdc:ReadQcAnalysisActivity": "mgrqc",
            "nmdc:MetagenomeAssembly": "mgasm",
            "nmdc:MetagenomeAnnotationActivity": "mgann",
            "nmdc:MAGsAnalysisActivity": "mgmag",
            "nmdc:ReadBasedTaxonomyAnalysisActivity": "mgrbt"
        }
        return f"nmdc:wf{mapping[id_type]}-11-xxxxxx"

    def get_activity_id(self, wf, informed_by):
        """
        See if anything exist for this and if not
        mint a new id.
        """

        # This is a temporary workaround and should be removed
        # once the schema names are all fixed.
        act_set_name = wf.collection
        q = {"was_informed_by": informed_by}
        ct = 0
        root_id = None

        # We need to see if any version exist and
        # if so get its ID
        for doc in self.db[act_set_name].find(q):
            ct += 1
            last_id = doc['id']

        if ct == 0:
            # Get an ID
            id_type = wf.type
            if os.environ.get("MOCK_MINT"):
                root_id = self.mock_mint(id_type)
            else:
                root_id = self.api.minter(id_type, informed_by)
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
        if not wf.enabled:
            return []
        act_set_name = wf.collection
        git_repo = wf.git_repo
        vers = wf.version
        pred = wf.predecessor
        if not pred:
            # Nothing to do
            return []
        pred_wf = self.workflow_by_name[pred]
        trigger_set = pred_wf.collection
        completed_acts = {}
        # Filter by git_repo and version
        # Find all existing jobs for this workflow
        q = {'config.git_repo': git_repo,
             'config.release': vers}
        for j in self.db.jobs.find(q):
            act = j['config']['trigger_activity']
            completed_acts[act] = j
        # Find all completed activities for this workflow
        q = {'version': vers, 'git_repo': git_repo}
        for act in self.db[act_set_name].find(q):
            completed_acts[act['id']] = act

        # Check triggers
        # TODO: filter based on active version
        todo = []
        for act in self.db[trigger_set].find():
            actid = act['id']
            if actid in completed_acts:
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
        for wf in self.workflows:
            if not wf.enabled:
                continue
            logging.debug("Checking: " + wf.name)
            jobs = self.new_jobs(wf)
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
