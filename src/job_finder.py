import os
from pymongo import MongoClient
from yaml import load
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader
from datetime import datetime


class JobMaker():
    _sets = ['metagenome_annotation_activity_set',
             'metagenome_assembly_set',
             'read_QC_analysis_activity_set']

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
        doid = job['data_object_id']
        pred = wf['Predecessor']
        if pred:
            pred_wf = self.workflow_by_name[pred]
            trigger_set = pred_wf['Activity']

            # Find the activity that generated the data object id
            act = self.db[trigger_set].find_one({"has_output": doid})

            # Ignore if the trigger object isn't the latest version
            if act is None or pred_wf['Version'] != act.get('version'):
                return

            # Get the provenance
            acts, root_dos = self.coll_prov_acts(act, trigger_set, {})
            dos = root_dos
            for aid, act in acts.items():
                for did in act['has_output']:
                    dos.append(did)
        else:
            dos = [doid]

        # Now collect all the data objects and their types
        do_by_type = dict()
        for did in dos:
            do = self.db["data_object_set"].find_one({"id": did})
            if do and 'data_object_type' in do:
                do_by_type[do['data_object_type']] = do['url']
        inp = dict()
        for k, v in wf['Inputs'].items():
            if v.startswith('do:'):
                p = v[3:]
                v = do_by_type.get(p, "FIX ME")
            inp[k] = v

        # Build the respoonse
        ji = {
                "git_repo": wf["Git_repo"],
                "release": wf["Version"],
                "wdl": wf["WDL"],
                "trigger_object": job['data_object_id'],
                "input_prefix": wf["Input_prefix"],
                "inputs": inp
                }

        jr = {
            "workflow": {
                "id": "{Name}: {Version}".format(**wf)
            },
            "id": "nmdc:TODO",
            "created_at": datetime.today().replace(microsecond=0),
            "config": ji,
            "claims": []
        }
        rec = self.db.jobs.insert_one(jr, bypass_document_validation=True)
        # This would make the job record
        # print(json.dumps(ji, indent=2))
        return rec

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
        trig = wf['Trigger_on']
        comp_dos = {}
        # Filter by git_repo and version
        q = {'config.git_repo': git_repo,
             'config.release': vers}
        for j in self.db.jobs.find(q):
            do = j['config']['trigger_object']
            comp_dos[do] = j
        # Find all jobs of for this workflow
        q = {'version': vers, 'git_repo': git_repo}
        for act in self.db[act_set].find(q):
            for do in act['has_input']:
                comp_dos[do] = act

        # Check triggers
        todo = []
        q = {'data_object_type': trig}
        for do in self.db.data_object_set.find(q):
            doid = do['id']
            if doid in comp_dos:
                continue
            todo.append({'wf': wf, 'data_object_id': doid})
        return todo

    def cycle(self):
        """
        This function does a single cycle of looking for new jobs
        """
        job_recs = []
        for w in self.workflows['Workflows']:
            jobs = self.find_jobs(w)
            for job in jobs:
                jr = self.add_job_rec(job)
                if jr:
                    job_recs.append(jr)
        return job_recs


if __name__ == "__main__":
    jm = JobMaker()
    jm.cycle()
