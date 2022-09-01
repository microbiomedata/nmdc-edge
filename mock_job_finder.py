import json
import os
from pymongo import MongoClient
import sys
from yaml import load
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader


trigger_set = 'metagenome_annotation_activity_set'
trigger_id = 'nmdc:55a79b5dd58771e28686665e3c3faa0c'
trigger_doid = 'nmdc:1d87115c442a1f83190ae47c7fe4011f'


def init_nmdc_mongo():
    url = os.environ['MONGO_URL']
    client = MongoClient(url)
    nmdc = client.nmdc
    return nmdc

_sets = ['metagenome_annotation_activity_set',
         'metagenome_assembly_set',
         'read_QC_analysis_activity_set']

def load_workflows():
    return load(open('workflows.yaml'), Loader=Loader)

def collect_provenance_activities(act, rset, acts, root_dos=[]):
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
        for s in _sets:
            nact = nmdc[s].find_one({"has_output": d})
            if nact == None:
                continue
            hit = True
            acts, root_dos = collect_provenance_activities(nact, s, acts, root_dos)
        if not hit:
            # print("No match %s" % (d))
            root_dos.append(d)
    return acts, root_dos

def create_job(job):
    wf = job['wf']
    doid = job['data_object_id']
    pred = wf['Predecessor']
    if pred:
        pred_wf = workflows['Workflows_by_name'][pred]
        trigger_set = pred_wf['Activity']
        act = nmdc[trigger_set].find_one({"has_output": doid})
        # See if the trigger object is the latest version
        if act is None or pred_wf['Version'] != act.get('version'):
            #print("DEBUG: Skipping old version")
            return
        acts, root_dos = collect_provenance_activities(act, trigger_set, {})
        dos = root_dos
        for aid, act in acts.items():
            for did in act['has_output']:
                dos.append(did)
    else:
        dos = [doid]

    do_by_type = dict()
    for did in dos:
        do = nmdc["data_object_set"].find_one({"id": did})
        if do and 'data_object_type' in do:
            do_by_type[do['data_object_type']] = do['url']
            # print(do['data_object_type'], do['url'])
    inp = dict()
    for k, v in wf['Inputs'].items():
        if v.startswith('do:'):
            p = v[3:]
            v = do_by_type.get(p, "FIX ME")
        inp[k] = v
    ji = {
            "git_repo": wf["Git_repo"],
            "release": wf["Version"],
            "wdl": wf["WDL"],
            "inputs": inp
            }
    # This would make the job record
    print(json.dumps(ji, indent=2))

def find_jobs(wf):
    # Find jobs for this workflow
    if not wf['Enabled']:
        return []
    act_set = wf['Activity']
    git_repo = wf['Git_repo']
    vers = wf['Version']
    trig = wf['Trigger_on']
    comp_dos = {}
    # Would filter by git_repo and version
    q = {'version': vers}
    # Note this could be jobs
    for act in nmdc[act_set].find(q):
        # Would check git_repo and version
        for do in act['has_input']:
            comp_dos[do] = act
    # Check triggers
    todo = []
    q = {'data_object_type': trig}
    for do in nmdc.data_object_set.find(q):
        doid = do['id']
        if doid in comp_dos:
            continue
        todo.append({'wf': wf, 'data_object_id': doid})
    # mock
    #todo =  [{'wf': wf, 'data_object_id': trigger_doid}]
    return todo

def cycle():
    
    for w in workflows['Workflows']:
        jobs = find_jobs(w)
        for job in jobs:
            create_job(job)

if __name__ == "__main__":
    # Init
    workflows = load_workflows()
    nmdc = init_nmdc_mongo()
    workflows['Workflows_by_name'] = dict()
    for w in workflows['Workflows']:
        workflows['Workflows_by_name'][w['Name']] = w
    cycle()
