import os
import sys
from time import sleep
from pymongo import MongoClient
from yaml import load
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader
from datetime import datetime
import uuid


_POLL_INTERVAL = 10


class JobMaker():
    _sets = ['metagenome_annotation_activity_set',
             'metagenome_assembly_set',
             'read_QC_analysis_activity_set',
             'mags_activity_set',
             'read_based_analysis_activity_set']

    def __init__(self, db="nmdc", wfn="workflows.yaml"):
        # Init
        self.workflows = load(open(wfn), Loader=Loader)
        url = os.environ['MONGO_URL']
        client = MongoClient(url)
        self.db = client[db]

        # Build a workflow map for later use
        self.workflow_by_name = dict()
        for w in self.workflows['Workflows']:
            self.workflow_by_name[w['Name']] = w

    def coll_prov_acts(self, act, rset, acts, root_dos=[]):
        """
        This is a recursive function that will walk up the
        object provenance (has_input, has_output) to find
        all the preceeding activities and data objects.

        It returns the set of activities and "root" objects.
        Root objects are data objects with no matching
        has_output.  So they must be the original raw data.
        """
        aid = '%s:%s' % (rset, act['id'])
        # print(aid, rset, act['has_input'])
        if aid in acts:
            return acts
        act.pop("_id")
        acts[aid] = act
        inp = act["has_input"]
        root_dos = []
        for d in inp:
            hit = False
            for s in self._sets:
                nact = self.db[s].find_one({"has_output": d})
                if nact is None:
                    continue
                hit = True
                acts, root_dos = self.coll_prov_acts(nact, s, acts, root_dos)
            if not hit:
                # print("No match %s" % (d))
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
            do = self.db["data_object_set"].find_one({"id": did})
            if do and 'data_object_type' in do:
                do_by_type[do['data_object_type']] = do['url']
        base_id, iteration = self.get_activity_id(wf, informed_by)
        activity_id = f"{base_id}.{iteration}"
        inp = dict()
        for k, v in wf['Inputs'].items():
            if v.startswith('do:'):
                p = v[3:]
                v = do_by_type.get(p)
                print(v)
                if not v:
                    raise ValueError(f"Unable to resolve {v}")
            # TODO: Make this smarter
            if v == "{was_informed_by}":
                v = informed_by
            elif v == "{activity_id}":
                v = activity_id

            inp[k] = v

        # Build the respoonse
        ji = {
                "git_repo": wf["Git_repo"],
                "release": wf["Version"],
                "wdl": wf["WDL"],
                "activity_id": activity_id,
                "was_informed_by": informed_by,
                "trigger_activity": trig_actid,
                "iteration": iteration,
                "input_prefix": wf["Input_prefix"],
                "inputs": inp
                }

        jr = {
            "workflow": {
                "id": "{Name}: {Version}".format(**wf)
            },
            "id": self.get_id(),
            "created_at": datetime.today().replace(microsecond=0),
            "config": ji,
            "claims": []
        }
        # rec = jr
        rec = self.db.jobs.insert_one(jr, bypass_document_validation=True)
        print('JOB RECORD:',rec)
        # This would make the job record
        # print(json.dumps(ji, indent=2))
        return rec

    def get_id(self):
        u = str(uuid.uuid1())
        return f"nmdc:test_{u}"

    def get_activity_id(self, wf, informed_by):
        """
        See if anything exist for this and if not
        mint a new id.
        """
        act_set = wf['Activity'].replace("_qc_", "_QC_")
        q = {"was_informed_by": informed_by}
        ct = 0
        root_id = None
        
        for doc in self.db[act_set].find(q):
            ct += 1
            last_id = doc['id']

        if ct == 0:
            # Get an ID
            id_type = wf['ID_type']
            root_id = f"nmdc:{id_type}0xxxx"
            return root_id, 1
        else:
            print(last_id)
            root_id = '.'.join(last_id.split('.')[0:-1])
            return root_id, ct+1

    def find_jobs(self, wf):
        """
        This function is given a workflow and identifies new
        jobs to create by looking at the workflow's trigger data
        types and what has been previously processed.
        """

        # Skip disabled workflows
        if not wf['Enabled']:
            return []
        act_set = wf['Activity']
        git_repo = wf['Git_repo']
        vers = wf['Version']
        pred = wf['Predecessor']
        if not pred:
            # Nothing to do
            print("NOTHING!")
            return []
        pred_wf = self.workflow_by_name[pred]
        trigger_set = pred_wf['Activity']
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
            name = w["Name"]
            # print(f"Checking {name}")
            if not w["Enabled"]:
                continue
            jobs = self.find_jobs(w)
            for job in jobs:
                jr = self.add_job_rec(job)
                if jr:
                    job_recs.append(jr)
        return job_recs


if __name__ == "__main__":
    jm = JobMaker()
    if len(sys.argv) > 1 and sys.argv[1]=="daemon":
        while True:
            jm.cycle()
            sleep(_POLL_INTERVAL)
    else:
        jm.cycle()
